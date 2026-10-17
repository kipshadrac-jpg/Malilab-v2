from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from content.models import PracticeActivity
from .models import PracticeAttempt, PracticeResponse
from .schema import validate_answer, validate_response_set, validate_schema


def require_verified_account(user):
    if not getattr(user, 'is_authenticated', False) or not getattr(user, 'is_active', False) or not getattr(user, 'email_verified', False) or getattr(user, 'account_status', None) != 'active':
        raise PermissionDenied('A verified active account is required.')


def resolve_public_activity(slug):
    activity = get_object_or_404(PracticeActivity.objects.select_related('current_published_revision'), slug=slug, status='published')
    revision = activity.current_published_revision
    if revision is None or revision.activity_id != activity.pk or revision.status != 'published':
        from django.http import Http404
        raise Http404
    try:
        validate_schema(revision.response_schema)
    except ValidationError:
        raise ValidationError('This Practice activity is temporarily unavailable.')
    return activity, revision


@transaction.atomic
def create_attempt(*, user, practice_revision=None, slug=None):
    require_verified_account(user)
    if slug is not None:
        _, practice_revision = resolve_public_activity(slug)
    if practice_revision is None:
        raise ValidationError('A published Practice revision is required.')
    # Internal callers may pin a known revision; learner routes always resolve by public slug.
    if practice_revision.activity_id is None:
        raise ValidationError('A Practice revision is required.')
    validate_schema(practice_revision.response_schema)
    return PracticeAttempt.objects.create(owner=user, practice_revision=practice_revision)


def get_owned_attempt(*, user, attempt_id):
    require_verified_account(user)
    return PracticeAttempt.objects.select_related('practice_revision').get(owner=user, pk=attempt_id)


@transaction.atomic
def save_response(*, user, attempt_id, prompt_key, value, unit=None):
    require_verified_account(user)
    attempt = PracticeAttempt.objects.select_for_update().select_related('practice_revision').get(pk=attempt_id, owner=user)
    require_verified_account(user)
    if attempt.state != 'started':
        raise ValidationError('Submitted attempts are immutable.')
    schema = validate_schema(attempt.practice_revision.response_schema)
    questions = {q['id']: q for q in schema['questions']}
    if prompt_key not in questions:
        raise ValidationError('Unknown Practice question.')
    question = questions[prompt_key]
    validated = validate_answer(question, value)
    if unit not in (None, ''):
        raise ValidationError('Response units are not supported by the current Practice contract.')
    response, _ = PracticeResponse.objects.update_or_create(
        attempt=attempt, prompt_key=prompt_key,
        defaults={'value': validated, 'unit': ''},
    )
    return response


@transaction.atomic
def delete_response(*, user, response_id):
    require_verified_account(user)
    response = PracticeResponse.objects.select_for_update().select_related('attempt').get(pk=response_id, attempt__owner=user)
    if response.attempt.state != 'started':
        raise ValidationError('Submitted responses cannot be deleted.')
    response.delete()


@transaction.atomic
def submit_attempt(*, user, attempt_id, responses=None, response_summary=None):
    require_verified_account(user)
    attempt = PracticeAttempt.objects.select_for_update().select_related('practice_revision').get(pk=attempt_id, owner=user)
    if attempt.state != 'started':
        raise ValidationError('Only a started PracticeAttempt can be submitted.')
    schema = validate_schema(attempt.practice_revision.response_schema)
    rows = {r.prompt_key: r for r in attempt.responses.all()}
    final = ({key: row.value for key, row in rows.items()} if responses is None else responses)
    validated = validate_response_set(schema, final, complete=True)
    # All validation precedes writes. Atomic transaction protects replacement plus transition.
    for key in rows.keys() - validated.keys():
        rows[key].delete()
    for key, value in validated.items():
        question = next(q for q in schema['questions'] if q['id'] == key)
        if key in rows:
            row = rows[key]
            row.value, row.unit = value, ''
            row.save(update_fields=['value', 'unit', 'answered_at'])
        else:
            PracticeResponse.objects.create(attempt=attempt, prompt_key=key, value=value, unit='')
    attempt.state = 'submitted'
    attempt.submitted_at = timezone.now()
    # response_summary is not caller-controlled or canonical; existing JSON field remains unchanged.
    attempt.save(update_fields=['state', 'submitted_at'])
    return attempt
