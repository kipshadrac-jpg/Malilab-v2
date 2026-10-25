from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from .models import PracticeAttempt
from .schema import validate_schema
from .services import create_attempt, get_owned_attempt, resolve_public_activity, save_response, submit_attempt


def _context_page(request, template, context, status=200):
    context.update({'user': request.user, 'csrf_token': get_token(request), 'request': request})
    from django.http import HttpResponse
    return HttpResponse(render_to_string(template, context), status=status)


@require_GET
def activity(request, slug):
    try:
        identity, revision = resolve_public_activity(slug)
    except ValidationError:
        return _context_page(request, 'practice/unavailable.html', {}, 503)
    from billing.catalog import paywall_on
    if paywall_on():
        from billing import service as billing_service
        blocked = billing_service.web_gate(request.user, billing_service.practice_modules(identity))
        if blocked:
            from billing.views import locked_page
            return locked_page(request, blocked, revision.title, revision.instructions, 'practice')
    open_attempts = []
    if request.user.is_authenticated and request.user.can_use_personal_features:
        open_attempts = PracticeAttempt.objects.filter(owner=request.user, state='started', practice_revision__activity=identity).select_related('practice_revision').order_by('-started_at')
    return _context_page(request, 'practice/activity.html', {'identity': identity, 'revision': revision, 'open_attempts': open_attempts})


@login_required(login_url='sign-in')
@require_POST
def start(request, slug):
    from billing.catalog import paywall_on
    if paywall_on():
        from billing import service as billing_service
        try:
            activity_identity, _ = resolve_public_activity(slug)
        except ValidationError:
            activity_identity = None
        if activity_identity is not None and billing_service.web_gate(request.user, billing_service.practice_modules(activity_identity)):
            return redirect(reverse('unlock') + '?next=' + reverse('practice-activity', args=[slug]))
    try:
        attempt = create_attempt(user=request.user, slug=slug)
    except PermissionDenied:
        return redirect(f"{reverse('sign-in')}?next={reverse('practice-activity', args=[slug])}")
    except ValidationError:
        return redirect('practice-unavailable')
    return redirect('practice-attempt', attempt_id=attempt.pk)


def _owned(request, attempt_id):
    try:
        return get_owned_attempt(user=request.user, attempt_id=attempt_id)
    except PracticeAttempt.DoesNotExist:
        raise Http404


@login_required(login_url='sign-in')
@require_GET
def attempt(request, attempt_id):
    try:
        current = _owned(request, attempt_id)
    except PermissionDenied:
        return redirect('sign-in')
    if current.state == 'submitted':
        return _context_page(request, 'practice/submitted.html', {'attempt': current})
    try:
        schema = validate_schema(current.practice_revision.response_schema)
    except ValidationError:
        return _context_page(request, 'practice/unavailable.html', {}, 503)
    saved = {r.prompt_key: r.value for r in current.responses.all()}
    return _context_page(request, 'practice/attempt.html', {'attempt': current, 'schema': schema, 'saved': saved, 'errors': {}})


@login_required(login_url='sign-in')
@require_POST
def save(request, attempt_id):
    try:
        current = _owned(request, attempt_id)
        schema = validate_schema(current.practice_revision.response_schema)
        questions = {q['id']: q for q in schema['questions']}
        key = request.POST.get('question_id', '')
        if key not in questions:
            raise ValidationError('Unknown Practice question.')
        q = questions[key]
        if q['type'] == 'multiple_choice':
            value = request.POST.getlist(key)
        elif q['type'] == 'integer':
            raw = request.POST.get(key, '')
            if not raw or not raw.lstrip('-').isdigit():
                raise ValidationError({key: 'Enter a whole number.'})
            value = int(raw)
        else:
            value = request.POST.get(key, '')
        save_response(user=request.user, attempt_id=attempt_id, prompt_key=key, value=value)
        return redirect('practice-attempt', attempt_id=attempt_id)
    except PermissionDenied:
        return redirect('sign-in')
    except ValidationError as exc:
        current = _owned(request, attempt_id)
        schema = validate_schema(current.practice_revision.response_schema)
        saved = {r.prompt_key: r.value for r in current.responses.all()}
        return _context_page(request, 'practice/attempt.html', {'attempt': current, 'schema': schema, 'saved': saved, 'errors': getattr(exc, 'message_dict', {'form': exc.messages})}, 400)


@login_required(login_url='sign-in')
@require_POST
def submit(request, attempt_id):
    try:
        current = _owned(request, attempt_id)
        if current.state == 'submitted':
            return _context_page(request, 'practice/submitted.html', {'attempt': current}, 409)
        schema = validate_schema(current.practice_revision.response_schema)
        final = {}
        for q in schema['questions']:
            key, kind = q['id'], q['type']
            if kind == 'multiple_choice':
                if key in request.POST:
                    final[key] = request.POST.getlist(key)
            elif kind == 'integer':
                raw = request.POST.get(key)
                if raw is not None:
                    if not raw or not raw.lstrip('-').isdigit():
                        raise ValidationError({key: 'Enter a whole number.'})
                    final[key] = int(raw)
            elif key in request.POST:
                final[key] = request.POST.get(key)
        submit_attempt(user=request.user, attempt_id=attempt_id, responses=final)
        return redirect('practice-submitted', attempt_id=attempt_id)
    except PermissionDenied:
        return redirect('sign-in')
    except ValidationError as exc:
        current = _owned(request, attempt_id)
        schema = validate_schema(current.practice_revision.response_schema)
        saved = {r.prompt_key: r.value for r in current.responses.all()}
        return _context_page(request, 'practice/attempt.html', {'attempt': current, 'schema': schema, 'saved': saved, 'errors': getattr(exc, 'message_dict', {'form': exc.messages})}, 400)


@login_required(login_url='sign-in')
@require_GET
def submitted(request, attempt_id):
    current = _owned(request, attempt_id)
    if current.state != 'submitted':
        return redirect('practice-attempt', attempt_id=attempt_id)
    return _context_page(request, 'practice/submitted.html', {'attempt': current})


@require_GET
def unavailable(request):
    return _context_page(request, 'practice/unavailable.html', {}, 503)
