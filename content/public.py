"""Read-only public content boundary for current, published revisions."""

from django.shortcuts import get_object_or_404
from django.db.models import F

from .models import (
    Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision,
    Playbook, PlaybookModuleRecommendation, PlaybookRevision,
)


REVISION_MODELS = {
    Playbook: ('current_published_revision', PlaybookRevision, 'playbook'),
    Module: ('current_published_revision', ModuleRevision, 'module'),
    Lesson: ('current_published_revision', LessonRevision, 'lesson'),
}


def resolve_public_revision(identity_model, slug):
    """Resolve only an identity's own current revision in public state."""
    pointer_field, revision_model, owner_field = REVISION_MODELS[identity_model]
    identity = get_object_or_404(
        identity_model.objects.select_related(pointer_field), slug=slug,
        status='published',
    )
    revision = getattr(identity, pointer_field)
    if (revision is None or getattr(revision, f'{owner_field}_id') != identity.pk
            or revision.status != 'published'):
        from django.http import Http404
        raise Http404
    return identity, revision


def public_playbooks():
    """Published identities whose pointer targets their own published revision."""
    return Playbook.objects.filter(
        status='published', current_published_revision__status='published',
        current_published_revision__playbook_id=F('pk'),
    ).select_related('current_published_revision').order_by('current_published_revision__title', 'slug')


def public_modules():
    return Module.objects.filter(
        status='published', current_published_revision__status='published',
        current_published_revision__module_id=F('pk'),
    ).select_related('current_published_revision').order_by('current_published_revision__title', 'slug')


def public_recommended_modules(playbook_revision):
    rows = PlaybookModuleRecommendation.objects.filter(
        playbook_revision=playbook_revision, active=True,
        module_revision__status='published',
        module_revision__module__status='published',
        module_revision__module__current_published_revision_id=F('module_revision_id'),
        module_revision__module__current_published_revision__module_id=F('module_revision__module_id'),
    ).select_related('module_revision', 'module_revision__module').order_by('position')
    return list(rows)


def public_module_lessons(module_revision):
    rows = ModuleLearningRequirement.objects.filter(
        module_revision=module_revision, target_kind='lesson', active=True,
        lesson_revision__status='published', lesson_revision__lesson__status='published',
        lesson_revision__lesson__current_published_revision_id=F('lesson_revision_id'),
        lesson_revision__lesson__current_published_revision__lesson_id=F('lesson_revision__lesson_id'),
    ).select_related('lesson_revision', 'lesson_revision__lesson').order_by('position')
    return [row.lesson_revision for row in rows]


def public_lesson_modules(lesson_revision):
    """Return only exact current public Module contexts containing this LessonRevision."""
    return public_modules().filter(
        current_published_revision__learning_requirements__target_kind='lesson',
        current_published_revision__learning_requirements__active=True,
        current_published_revision__learning_requirements__lesson_revision=lesson_revision,
    ).distinct()
