from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from practice.models import PracticeAttempt
from .models import (Note, LearningJourney, JourneyTargetRef, JourneyStep,
    JourneyPlaybookTarget, JourneyModuleTarget, JourneyLessonTarget,
    JourneyPracticeTarget, JourneyAttemptTarget, JourneyCalculationTarget,
    JourneyPlanTarget, RequirementEvidence, ModuleCompletion, LessonCompletion)

def require_verified_account(user):
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_active', False) or not getattr(user, 'email_verified', False) or getattr(user, 'account_status', None) != 'active':
        raise PermissionDenied('A verified active account is required.')

def owned_notes(user):
    require_verified_account(user)
    return Note.objects.filter(owner=user, deleted_at__isnull=True)

@transaction.atomic
def create_note(*, user, kind, body='', lesson_revision=None, block_key='', anchor_data=None, journey=None):
    require_verified_account(user)
    if journey is not None and journey.owner_id != user.pk:
        raise PermissionDenied('Journey belongs to another account.')
    if kind == 'highlight':
        validate_note_anchor(lesson_revision, block_key, anchor_data)
    return Note.objects.create(owner=user, kind=kind, body=body, lesson_revision=lesson_revision, block_key=block_key, anchor_schema_version=1 if anchor_data else None, anchor_data=anchor_data, journey=journey)

def validate_note_anchor(lesson_revision, block_key, anchor_data):
    if lesson_revision is None or not block_key or not isinstance(anchor_data, dict) or not anchor_data.get('selected_quote'):
        raise ValidationError('Highlights require an exact lesson revision, block key, and selected quote.')
    blocks = lesson_revision.blocks if isinstance(lesson_revision.blocks, list) else []
    matches = [b for b in blocks if isinstance(b, dict) and b.get('key') == block_key]
    if len(matches) != 1:
        raise ValidationError({'block_key': 'Block key must resolve exactly once in the pinned lesson revision.'})
    quote = anchor_data['selected_quote']
    block = matches[0]
    def collect(value):
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [part for item in value for part in collect(item)]
        if isinstance(value, dict):
            return [part for key, child in value.items() if key in ('text','content') for part in collect(child)]
        return []
    payload = block.get('payload', {})
    text = ' '.join(collect(payload.get('text', '')))
    from content.richtext import plain_text
    text = text + '\n' + plain_text(block)
    if not isinstance(quote, str) or not quote or quote not in text:
        raise ValidationError({'anchor_data': 'Selected quote must exist in the pinned content block text.'})
    offsets = anchor_data.get('start_offset'), anchor_data.get('end_offset')
    if any(value is not None for value in offsets):
        start, end = offsets
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
            raise ValidationError({'anchor_data': 'Offsets must be nonnegative hints.'})

TARGET_SPECS = {
    'playbook': (JourneyPlaybookTarget, 'playbook', False),
    'module': (JourneyModuleTarget, 'module', False),
    'lesson': (JourneyLessonTarget, 'lesson', False),
    'practice': (JourneyPracticeTarget, 'practice', False),
    'attempt': (JourneyAttemptTarget, 'attempt', True),
    'calculation': (JourneyCalculationTarget, 'calculation', True),
    'plan': (JourneyPlanTarget, 'plan', True),
}

def validate_journey_target(journey, target_ref):
    spec = TARGET_SPECS.get(target_ref.target_kind)
    if spec is None:
        raise ValidationError({'target_ref': 'Unknown journey target kind.'})
    association, accessor, user_owned = spec
    records = [m for model in (JourneyPlaybookTarget, JourneyModuleTarget, JourneyLessonTarget,
        JourneyPracticeTarget, JourneyAttemptTarget, JourneyCalculationTarget, JourneyPlanTarget)
        for m in model.objects.filter(target_ref=target_ref)]
    if len(records) != 1 or not isinstance(records[0], association):
        raise ValidationError({'target_ref': 'Target kind must have exactly one matching target subtype.'})
    target = getattr(records[0], 'target')
    owner_id = getattr(target, 'owner_id', None)
    if user_owned and (owner_id is None or target_ref.owner_id != owner_id or journey.owner_id != owner_id):
        raise ValidationError({'target_ref': 'Private target and target registry must match journey owner.'})
    if not user_owned and target_ref.owner_id is not None:
        raise ValidationError({'target_ref': 'Editorial targets cannot carry a private owner.'})
    return target

@transaction.atomic
def append_journey_step(*, user, journey, target_kind, target, step_type, state='planned', occurred_at=None, context_metadata=None):
    require_verified_account(user)
    journey = LearningJourney.objects.select_for_update().get(pk=journey.pk, owner=user)
    spec = TARGET_SPECS.get(target_kind)
    if spec is None:
        raise ValidationError('Unsupported journey target kind.')
    association, _, user_owned = spec
    if target.__class__._meta.label_lower != association._meta.get_field('target').remote_field.model._meta.label_lower:
        raise ValidationError('Target object does not match target kind.')
    if user_owned and getattr(target, 'owner_id', None) != user.pk:
        raise PermissionDenied('Journey target belongs to another account.')
    if not user_owned and target_kind in ('attempt','calculation','plan'):
        raise ValidationError('Target subtype does not match target kind.')
    target_ref = JourneyTargetRef.objects.create(target_kind=target_kind, owner=user if user_owned else None)
    association.objects.create(target_ref=target_ref, target=target)
    validate_journey_target(journey, target_ref)
    sequence = (journey.steps.order_by('-sequence').values_list('sequence', flat=True).first() or 0) + 1
    return JourneyStep.objects.create(journey=journey, target_ref=target_ref, sequence=sequence,
        step_type=step_type, state=state, occurred_at=occurred_at, context_metadata=context_metadata or {})

def validate_requirement_evidence(evidence):
    req, attempt = evidence.requirement, evidence.attempt
    if evidence.module_revision_id != req.module_revision_id:
        raise ValidationError({'module_revision': 'Must be the exact revision owning the requirement.'})
    if req.target_kind != 'practice' or req.practice_revision_id != evidence.practice_revision_id:
        raise ValidationError({'practice_revision': 'Must match the exact practice target of the requirement.'})
    if attempt.practice_revision_id != evidence.practice_revision_id:
        raise ValidationError({'attempt': 'Attempt must reference the exact PracticeRevision.'})
    if attempt.owner_id != evidence.owner_id:
        raise ValidationError({'owner': 'Evidence owner must own the attempt.'})
    if attempt.state != 'submitted' or attempt.submitted_at is None:
        raise ValidationError({'attempt': 'Only a submitted PracticeAttempt is eligible evidence.'})
    if evidence.state == 'accepted' and not req.active:
        raise ValidationError({'requirement': 'Inactive requirements cannot receive accepted evidence.'})
    if evidence.supersedes_id and (evidence.supersedes.owner_id != evidence.owner_id or evidence.supersedes.requirement_id != req.pk or evidence.supersedes.module_revision_id != req.module_revision_id):
        raise ValidationError({'supersedes': 'Superseded evidence must preserve owner and exact requirement context.'})

@transaction.atomic
def record_requirement_evidence(*, user, module_revision, requirement, attempt, state='accepted', supersedes=None, evaluation_context=None):
    require_verified_account(user)
    # Refresh the submitted state from storage; callers may hold a stale started instance.
    attempt = PracticeAttempt.objects.select_related('practice_revision').get(pk=attempt.pk, owner=user)
    evidence = RequirementEvidence(owner=user, module_revision=module_revision, requirement=requirement,
        practice_revision=attempt.practice_revision, attempt=attempt, state=state,
        evaluated_at=timezone.now(), supersedes=supersedes, evaluation_context=evaluation_context or {})
    evidence.full_clean()
    evidence.save()
    return evidence

@transaction.atomic
def evaluate_module_completion(*, user, module_revision, journey=None):
    require_verified_account(user)
    if journey is not None and journey.owner_id != user.pk:
        raise PermissionDenied('Journey belongs to another account.')
    requirements = list(module_revision.learning_requirements.filter(active=True).order_by('position','pk'))
    snapshot = {'module_revision_id': module_revision.pk, 'requirements': [], 'complete': True}
    for req in requirements:
        accepted = None
        if req.target_kind == 'practice':
            accepted = RequirementEvidence.objects.filter(owner=user, module_revision=module_revision,
                requirement=req, practice_revision=req.practice_revision, state='accepted',
                attempt__state='submitted', attempt__submitted_at__isnull=False).select_related('attempt').first()
        if req.target_kind == 'lesson':
            lesson_evidence = LessonCompletion.objects.filter(owner=user, lesson_revision=req.lesson_revision,
                requirement=req).order_by('-completed_at').first()
        else:
            lesson_evidence = None
        has_evidence = accepted is not None if req.target_kind == 'practice' else lesson_evidence is not None
        satisfied = has_evidence
        snapshot['requirements'].append({'requirement_id': req.pk, 'classification': req.classification,
            'target_kind': req.target_kind, 'target_revision_id': req.lesson_revision_id or req.practice_revision_id,
            'satisfied': satisfied, 'evidence_id': accepted.pk if accepted else (lesson_evidence.pk if lesson_evidence else None),
            'attempt_id': accepted.attempt_id if accepted else None})
        if req.classification == 'required' and not satisfied:
            snapshot['complete'] = False
    return ModuleCompletion.objects.create(owner=user, module_revision=module_revision,
        outcome='complete' if snapshot['complete'] else 'incomplete', evidence_snapshot=snapshot, journey=journey)
