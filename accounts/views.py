from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_protect

from . import throttle
from .forms import SignInForm


def _safe_destination(request, value):
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return '/'


def _render_sign_in(request, form, next_destination='/', status=200):
    from django.middleware.csrf import get_token

    html = render_to_string('accounts/sign_in.html', {
        'form': form,
        'next_destination': next_destination,
        'csrf_token': get_token(request),
        'user': request.user,
    })
    from django.http import HttpResponse
    return HttpResponse(html, status=status)


@csrf_protect
def sign_in(request):
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    destination = _safe_destination(request, request.POST.get('next') if request.method == 'POST' else request.GET.get('next'))
    if request.user.is_authenticated and request.user.can_use_personal_features:
        return redirect(destination)

    form = SignInForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        if throttle.is_blocked(request, email):
            blocked = SignInForm(data={})
            blocked.is_valid()
            blocked.add_error(None, 'Too many sign-in attempts. Please wait 15 minutes and try again.')
            return _render_sign_in(request, blocked, destination, status=429)
        user = authenticate(request, email=email, password=form.cleaned_data['password'])
        if user is not None and user.can_use_personal_features:
            throttle.clear_failures(request, email)
            login(request, user)
            return redirect(destination)
        throttle.record_failure(request, email)
        # Keep one message for unknown, incorrect, disabled, and unverified accounts.
        form = SignInForm(data={})
        form.is_valid()
        form.add_error(None, 'We could not sign you in with those details. Check them and try again.')
    return _render_sign_in(request, form, destination)


@csrf_protect
def sign_out(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    logout(request)
    return redirect('/')
