"""Learner registration and password reset by emailed 6-digit code."""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

from . import emails, ratelimit, registration, throttle
from .models import AccountManager
from .registration_forms import CodeSetPasswordForm, EmailForm

User = get_user_model()

TOO_MANY = 'Too many requests from this device or for this address. Please wait an hour and try again.'

NOTICES = {
    'account-ready': ('Your account is ready', [
        'Your email is confirmed and your password is saved. You can sign in now.',
    ], [('sign-in', 'Sign in')]),
    'password-changed': ('Password changed', [
        'Your password has been changed. Sign in with the new one.',
    ], [('sign-in', 'Sign in')]),
    'already': ('You already have an account', [
        'This email address is already set up. Sign in, or reset your password if you have forgotten it.',
    ], [('sign-in', 'Sign in'), ('forgot-password', 'Reset password')]),
    'no-request': ('Start again', [
        'We could not find a current request in this browser. Codes work for 10 minutes and only in the browser where you asked for them.',
    ], [('register', 'Create an account'), ('forgot-password', 'Reset password')]),
    'code-locked': ('Too many wrong codes', [
        'For your safety that code no longer works. Please ask for a new one.',
    ], [('register', 'Create an account'), ('forgot-password', 'Reset password')]),
}
FINISHED_KINDS = ('account-ready', 'password-changed')


def _notice(request, kind, status=200):
    heading, paragraphs, links = NOTICES[kind]
    return render(request, 'accounts/notice.html', {
        'heading': heading, 'paragraphs': paragraphs,
        'links': [(reverse(name), label) for name, label in links],
    }, status=status)


def _form_page(request, form, *, heading, intro, submit_label, links=(), status=200):
    return render(request, 'accounts/form_page.html', {
        'form': form, 'heading': heading, 'intro': intro, 'submit_label': submit_label,
        'action': request.path, 'links': [(reverse(name), label) for name, label in links],
    }, status=status)


def _signed_in_learner(request):
    return request.user.is_authenticated and request.user.can_use_personal_features


def _email_step(request, *, scope, heading, intro, decide, skip_if_signed_in=False):
    """Shared by register and forgot-password: rate limit, remember the request in the session, email the code.

    `decide(user)` returns ('setup'|'reset', 'code'|'already'|None): the purpose to remember and what to email.
    Every valid submission ends the same way, so the page never reveals whether an account exists.
    """
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    if skip_if_signed_in and _signed_in_learner(request):
        return redirect('home')
    form = EmailForm(request.POST if request.method == 'POST' else None)
    links = [('sign-in', 'Back to sign in')]
    if request.method == 'POST':
        if ratelimit.too_many(request, scope, request.POST.get('email', '')):
            form.add_error(None, TOO_MANY)
            return _form_page(request, form, heading=heading, intro=intro, submit_label='Email me a code', links=links, status=429)
        if form.is_valid():
            email = AccountManager.normalize_identity(form.cleaned_data['email'])
            purpose, action = decide(User.objects.filter(email=email).first())
            code = registration.start_challenge(request, email, purpose)
            if action == 'code':
                emails.send_code(email, code, purpose)
            elif action == 'already':
                emails.send_already_registered(request, email)
            return redirect('enter-code')
    return _form_page(request, form, heading=heading, intro=intro, submit_label='Email me a code', links=links)


def _decide_register(user):
    if user is None or (not user.email_verified and registration.account_can_receive_mail(user)):
        return 'setup', 'code'
    if registration.account_can_receive_mail(user):
        return 'setup', 'already'
    return 'setup', None


def _decide_forgot(user):
    if user is None or not registration.account_can_receive_mail(user):
        return 'reset', None
    return ('reset', 'code') if user.email_verified else ('setup', 'code')


@csrf_protect
def register(request):
    return _email_step(request, scope='register', decide=_decide_register, skip_if_signed_in=True,
                       heading='Create your account',
                       intro='Enter your email address. We will email you a 6-digit code to confirm it.')


@csrf_protect
def forgot_password(request):
    return _email_step(request, scope='forgot', decide=_decide_forgot,
                       heading='Reset your password',
                       intro='Enter your email address. We will email you a 6-digit code.')


@csrf_protect
def enter_code(request):
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    challenge = registration.get_challenge(request)
    if challenge is None:
        return _notice(request, 'no-request', status=400)
    email, purpose = challenge['email'], challenge['purpose']
    heading = 'Enter your code'
    intro = (f'If {email} can be used, we have emailed it a 6-digit code. It works for '
             f'{registration.CODE_MAX_AGE // 60} minutes. Enter it here and choose your password.')
    links = [('register', 'Start again with a new code')]

    def page(form, status=200):
        return _form_page(request, form, heading=heading, intro=intro, submit_label='Save password', links=links, status=status)

    if request.method == 'GET':
        user = User.objects.filter(email=email).first()
        return page(CodeSetPasswordForm(user or User(email=email), challenge=challenge))

    try:
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email=email).first()
            form = CodeSetPasswordForm(user or User(email=email), request.POST, challenge=challenge)
            if not form.is_valid():
                if 'code' in form.errors:
                    registration.record_wrong_code(request)
                    if registration.get_challenge(request) is None:
                        return _notice(request, 'code-locked', status=400)
                return page(form)
            usable = user is not None and registration.account_can_receive_mail(user)
            if purpose == 'setup':
                if user is not None and user.email_verified:
                    registration.clear_challenge(request)
                    return _notice(request, 'already')
                if user is not None and not usable:
                    return _notice(request, 'no-request', status=400)
                account = form.save(commit=False)
                account.email_verified = True
                account.email_verified_at = timezone.now()
                account.save()
                finished = 'account-ready'
            else:
                if not (usable and user.email_verified):
                    return _notice(request, 'no-request', status=400)
                form.save()
                finished = 'password-changed'
    except IntegrityError:  # two submissions raced to create the same account
        registration.clear_challenge(request)
        return _notice(request, 'already')
    registration.clear_challenge(request)
    throttle.clear_failures(request, email)
    return redirect(f"{reverse('check-email')}?for={finished}")


def check_email(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    kind = request.GET.get('for')
    if kind not in FINISHED_KINDS:
        return redirect('home')
    return _notice(request, kind)
