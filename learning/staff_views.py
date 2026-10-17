from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import render_to_string

from practice.models import PracticeAttempt
from .evaluation import candidate_requirements, evaluate_attempt, pending_attempts, require_evaluator


def _page(request, template, context, status=200):
    context.update({'user': request.user, 'csrf_token': get_token(request)})
    return HttpResponse(render_to_string(template, context), status=status)


def _gate(request):
    try:
        require_evaluator(request.user)
    except PermissionDenied:
        raise Http404   # do not reveal that the staff route exists


def queue(request):
    _gate(request)
    return _page(request, 'learning/evaluation_queue.html', {'attempts': pending_attempts()[:100]})


def detail(request, attempt_id):
    _gate(request)
    try:
        attempt = PracticeAttempt.objects.select_related('owner', 'practice_revision__activity').get(pk=attempt_id, state='submitted')
    except PracticeAttempt.DoesNotExist:
        raise Http404
    error = ''
    if request.method == 'POST':
        try:
            evaluate_attempt(evaluator=request.user, attempt_id=attempt.pk,
                             requirement_id=int(request.POST.get('requirement', '0') or 0),
                             decision=request.POST.get('decision', ''), note=request.POST.get('note', ''))
            return redirect('staff-evaluations')
        except (ValidationError, ValueError, PermissionDenied):
            error = 'This evaluation could not be recorded. It may already be evaluated, or the choice is invalid.'
        except Exception as exc:
            if exc.__class__.__name__ != 'DoesNotExist':
                raise
            error = 'Unknown requirement.'
    schema = attempt.practice_revision.response_schema if isinstance(attempt.practice_revision.response_schema, dict) else {}
    labels = {q.get('id'): q.get('label') for q in schema.get('questions', []) if isinstance(q, dict)}
    answers = [{'label': labels.get(r.prompt_key, r.prompt_key), 'value': r.value}
               for r in attempt.responses.order_by('prompt_key')]
    return _page(request, 'learning/evaluation_detail.html', {
        'attempt': attempt, 'answers': answers, 'requirements': candidate_requirements(attempt),
        'evaluations': attempt.requirement_evidence.select_related('requirement'), 'error': error},
        400 if error else 200)
