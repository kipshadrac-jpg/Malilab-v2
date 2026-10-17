"""Plain-text account emails. A failed send never breaks the page, so the response cannot reveal anything."""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

from . import registration

log = logging.getLogger(__name__)

_PURPOSE_TEXT = {'setup': 'confirm your email address and choose your password', 'reset': 'reset your password'}


def _base(request):
    return settings.SITE_URL or request.build_absolute_uri('/').rstrip('/')


def _send(to, subject, body):
    try:
        EmailMessage(subject, body, to=[to]).send(fail_silently=False)
        return True
    except Exception:
        log.exception('Account email could not be sent')
        return False


def send_code(email, code, purpose):
    minutes = registration.CODE_MAX_AGE // 60
    return _send(email, 'Your MaliLab verification code', (
        f'Use this code to {_PURPOSE_TEXT[purpose]}:\n\n'
        f'{code}\n\n'
        f'Type it into the MaliLab page you have open. It works for {minutes} minutes and only in that browser. '
        'MaliLab will never ask you to read this code out to anyone. '
        'If you did not ask for it, ignore this email: nothing has changed.\n'
    ))


def send_already_registered(request, email):
    base = _base(request)
    return _send(email, 'You already have a MaliLab account', (
        'Someone (hopefully you) tried to create a MaliLab account with this email address, '
        'but an account already exists.\n\n'
        f'Sign in: {base}{reverse("sign-in")}\n'
        f'Forgot your password: {base}{reverse("forgot-password")}\n\n'
        'If this was not you, you can ignore this email.\n'
    ))
