"""Practice for the app: start or resume, autosave one answer at a time, submit, and see your history.

This is a thin JSON layer over practice.services, so every rule the website enforces (verified account,
exact pinned revision, strict answer checks, immutable submitted history) is enforced here too.
A submitted attempt is also recorded as evidence for the module requirement it satisfies.
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import Http404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.api import _body, _error, _json
from content.models import ModuleLearningRequirement
from notepad.api import learner
from practice import services
from practice.models import PracticeAttempt
from practice.schema import validate_schema
from billing.service import practice_gate, prices_note
from .models import RequirementEvidence
from .services import record_requirement_evidence

log = logging.getLogger(__name__)
HISTORY_LIMIT = 100


def _stamp(value):
    return value.isoformat() if value else None


def _tool_refs(revision):
    refs = revision.tool_refs if isinstance(revision.tool_refs, list) else []
    out = []
    for ref in refs[:5]:
        if isinstance(ref, dict):
            out.append({str(k)[:40]: str(v)[:120] for k, v in ref.items() if isinstance(v, (str, int, float))})
    return out


def _activity_part(revision):
    schema = validate_schema(revision.response_schema)
    return {
        'slug': revision.activity.slug, 'title': revision.title, 'instructions': revision.instructions,
        'prompt': revision.prompt, 'safety_text': revision.safety_text,
        'questions': schema['questions'], 'tool_refs': _tool_refs(revision),
    }


def _attempt(attempt):
    data = _activity_part(attempt.practice_revision)
    data.update({
        'id': attempt.pk, 'state': attempt.state, 'started_at': _stamp(attempt.started_at),
        'submitted_at': _stamp(attempt.submitted_at),
        'answers': {r.prompt_key: r.value for r in attempt.responses.all()},
    })
    return data


def _invalid(exc):
    if hasattr(exc, 'error_dict'):
        fields = {k: ' '.join(m.message for m in v) for k, v in exc.error_dict.items()}
        return _json({'error': 'invalid', 'message': next(iter(fields.values()), 'Please check your answers.'),
                      'fields': fields}, status=400)
    return _json({'error': 'invalid', 'message': ' '.join(exc.messages) or 'Please check your answers.', 'fields': {}}, status=400)


def _guarded(view):
    """Map the service layer's errors onto API errors."""
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except PermissionDenied:
            return _error('unauthorized', 'Please sign in with a verified account.', 401)
        except (PracticeAttempt.DoesNotExist, Http404):
            return _error('not_found', 'That practice was not found.', 404)
        except ValidationError as exc:
            return _invalid(exc)
    wrapper.__name__ = view.__name__
    return wrapper


def _locked(request, identity):
    """A 402 when this activity belongs to modules the learner has not unlocked, else None."""
    gate = practice_gate(request.learner, identity)
    if not gate:
        return None
    return _json({'error': 'payment_required', 'message': 'Unlock this module to use its practice.', 'modules': gate,
                  'prices': prices_note()}, status=402)


def _owned(request, attempt_id):
    return services.get_owned_attempt(user=request.learner, attempt_id=attempt_id)


@require_GET
@learner
@_guarded
def detail(request, slug):
    identity, revision = services.resolve_public_activity(slug)
    locked = _locked(request, identity)
    if locked is not None:
        return locked
    data = _activity_part(revision)
    mine = PracticeAttempt.objects.filter(owner=request.learner, practice_revision__activity=identity)
    open_attempt = mine.filter(state='started', practice_revision=revision).order_by('-started_at').first()
    last = mine.filter(state='submitted').order_by('-submitted_at').first()
    data['open_attempt_id'] = open_attempt.pk if open_attempt else None
    data['last_submitted'] = {'id': last.pk, 'submitted_at': _stamp(last.submitted_at)} if last else None
    data['submitted_count'] = mine.filter(state='submitted').count()
    return _json(data)


@require_POST
@learner
@_guarded
def start(request, slug):
    """Resume this learner's open attempt on the current revision, or begin a new one (retakes are allowed)."""
    identity, revision = services.resolve_public_activity(slug)
    locked = _locked(request, identity)
    if locked is not None:
        return locked
    open_attempt = PracticeAttempt.objects.filter(owner=request.learner, state='started', practice_revision=revision).order_by('-started_at').first()
    if open_attempt is not None:
        return _json(_attempt(open_attempt))
    return _json(_attempt(services.create_attempt(user=request.learner, slug=slug)), status=201)


@require_GET
@learner
@_guarded
def attempt_detail(request, attempt_id):
    return _json(_attempt(_owned(request, attempt_id)))


@require_http_methods(['PUT', 'DELETE'])
@learner
@_guarded
def answer(request, attempt_id, question_id):
    if request.method == 'DELETE':
        row = _owned(request, attempt_id).responses.filter(prompt_key=question_id).first()
        if row is not None:
            services.delete_response(user=request.learner, response_id=row.pk)
        return _json({'cleared': question_id})
    data = _body(request)
    if data is None or 'value' not in data:
        return _error('bad_request', 'Send {"value": ...}.')
    saved = services.save_response(user=request.learner, attempt_id=attempt_id, prompt_key=question_id, value=data['value'])
    return _json({'saved': question_id, 'value': saved.value})


def record_evidence(user, attempt):
    """Credit this submitted attempt to one module requirement, preferring one the learner has not met yet."""
    reqs = list(ModuleLearningRequirement.objects.filter(
        target_kind='practice', active=True, practice_revision_id=attempt.practice_revision_id,
        module_revision__status='published',
        module_revision__module__current_published_revision_id=F('module_revision_id'),
    ).select_related('module_revision').order_by('module_revision__module__slug', 'position'))
    met = set(RequirementEvidence.objects.filter(owner=user, state='accepted', requirement__in=reqs).values_list('requirement_id', flat=True))
    reqs.sort(key=lambda r: r.pk in met)       # unmet first (stable)
    for req in reqs:
        try:
            with transaction.atomic():
                return record_requirement_evidence(user=user, module_revision=req.module_revision, requirement=req, attempt=attempt)
        except (ValidationError, IntegrityError):
            continue
    return None


@require_POST
@learner
@_guarded
def submit(request, attempt_id):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    responses = data.get('responses')
    if responses is not None and not isinstance(responses, dict):
        return _error('bad_request', 'responses must be an object.')
    attempt = services.submit_attempt(user=request.learner, attempt_id=attempt_id, responses=responses)
    try:
        record_evidence(request.learner, attempt)
    except Exception:       # the submission itself is final and already saved
        log.exception('practice evidence not recorded for attempt %s', attempt.pk)
    attempt = _owned(request, attempt_id)
    from .api import progress_for
    return _json({'attempt': _attempt(attempt), 'progress': progress_for(request.learner)})


@require_GET
@learner
@_guarded
def history(request):
    rows = PracticeAttempt.objects.filter(owner=request.learner).select_related('practice_revision', 'practice_revision__activity').order_by('-started_at')[:HISTORY_LIMIT]
    return _json({'attempts': [{
        'id': a.pk, 'slug': a.practice_revision.activity.slug, 'title': a.practice_revision.title, 'state': a.state,
        'started_at': _stamp(a.started_at), 'submitted_at': _stamp(a.submitted_at),
        'answered': a.responses.count(),
    } for a in rows]})
