"""Start a new DRAFT revision from an existing one (for corrections and updates).

Never edits the source. Copies content; Module/Playbook links are re-pointed at the
current published revision of each linked item so the new draft starts up to date.
Block keys are kept so a lesson's paragraphs stay recognisable across revisions.
"""
import copy

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import (LessonRevision, ModuleLearningRequirement, ModuleRevision,
                     PlaybookModuleRecommendation, PlaybookRevision, PracticeActivityRevision)
from .services import require_staff_mfa

SPEC = {
    LessonRevision: ('lesson', ('title', 'summary', 'content_schema_version', 'blocks', 'metadata')),
    PracticeActivityRevision: ('activity', ('title', 'instructions', 'prompt', 'response_schema', 'tool_refs', 'safety_text', 'content_schema_version')),
    ModuleRevision: ('module', ('title', 'description', 'metadata')),
    PlaybookRevision: ('playbook', ('title', 'summary', 'scenario', 'audience_context', 'assumptions', 'discovery_metadata', 'cover_asset')),
}


def _current(revision):
    """The current published revision of this revision's identity, else the revision itself."""
    for name in ('lesson', 'activity', 'module'):
        identity = getattr(revision, name, None) if hasattr(revision, name + '_id') else None
        if identity is not None:
            return identity.current_published_revision or revision
    return revision


@transaction.atomic
def start_revision_from(*, revision, actor):
    require_staff_mfa(actor, 'author_editor')
    model = type(revision)
    if model not in SPEC:
        raise ValidationError('This kind of revision cannot be copied.')
    identity_field, fields = SPEC[model]
    identity = getattr(revision, identity_field)
    if model.objects.filter(**{identity_field: identity, 'status__in': ('draft', 'in_review')}).exists():
        raise ValidationError('This item already has an unpublished revision. Finish or publish it first.')
    last = model.objects.filter(**{identity_field: identity}).order_by('-revision_number').first()
    data = {name: copy.deepcopy(getattr(revision, name)) for name in fields if name != 'cover_asset'}
    if 'cover_asset' in fields:
        data['cover_asset'] = revision.cover_asset
    new = model.objects.create(**{identity_field: identity}, revision_number=last.revision_number + 1,
                               author=actor, status='draft', **data)
    if model is ModuleRevision:
        for req in revision.learning_requirements.filter(active=True).order_by('position', 'pk'):
            ModuleLearningRequirement.objects.create(
                module_revision=new, target_kind=req.target_kind, position=req.position,
                lesson_revision=_current(req.lesson_revision) if req.lesson_revision_id else None,
                practice_revision=_current(req.practice_revision) if req.practice_revision_id else None,
                classification=req.classification, completion_condition_key=req.completion_condition_key,
                active=True)
    if model is PlaybookRevision:
        for rec in revision.module_recommendations.filter(active=True).order_by('position', 'pk'):
            PlaybookModuleRecommendation.objects.create(
                playbook_revision=new, module_revision=_current(rec.module_revision),
                position=rec.position, rationale=rec.rationale, active=True)
    return new
