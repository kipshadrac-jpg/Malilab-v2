"""Emailed 6-digit codes for account setup and password reset. No database table is needed.

A request stores a random nonce in the visitor's own session; the code is an HMAC of (purpose, email,
nonce) under the site secret. So a code only works in the browser that asked for it, expires after
10 minutes, dies after 5 wrong tries, and is replaced whenever a new one is requested.
"""
import hashlib
import hmac
import secrets
import time

from django.conf import settings

SESSION_KEY = 'account_challenge'
CODE_MAX_AGE = 10 * 60
MAX_WRONG = 5
PURPOSES = ('setup', 'reset')


def expected_code(purpose, email, nonce):
    digest = hmac.new(settings.SECRET_KEY.encode(), f'malilab-code|{purpose}|{email}|{nonce}'.encode(), hashlib.sha256).digest()
    return f'{int.from_bytes(digest[:8], "big") % 1_000_000:06d}'


def start_challenge(request, email, purpose):
    """Remember the request in this browser's session and return the code to email."""
    nonce = secrets.token_hex(16)
    request.session[SESSION_KEY] = {'email': email, 'purpose': purpose, 'nonce': nonce, 'issued': int(time.time()), 'wrong': 0}
    return expected_code(purpose, email, nonce)


def clear_challenge(request):
    request.session.pop(SESSION_KEY, None)


def get_challenge(request):
    """The live request for this browser, or None when absent, expired, locked or damaged."""
    data = request.session.get(SESSION_KEY)
    try:
        if not isinstance(data, dict) or data['purpose'] not in PURPOSES:
            raise KeyError
        if not isinstance(data['email'], str) or not isinstance(data['nonce'], str):
            raise KeyError
        if int(data['wrong']) >= MAX_WRONG or time.time() - int(data['issued']) > CODE_MAX_AGE:
            raise KeyError
    except (KeyError, TypeError, ValueError):
        if data is not None:
            clear_challenge(request)
        return None
    return data


def clean_code(raw):
    return ''.join(ch for ch in (raw or '') if ch in '0123456789')


def code_is_right(challenge, raw):
    supplied = clean_code(raw)
    return len(supplied) == 6 and hmac.compare_digest(
        supplied, expected_code(challenge['purpose'], challenge['email'], challenge['nonce']))


def record_wrong_code(request):
    data = request.session.get(SESSION_KEY)
    if not isinstance(data, dict):
        return
    data['wrong'] = int(data.get('wrong', 0)) + 1
    if data['wrong'] >= MAX_WRONG:
        clear_challenge(request)
    else:
        request.session[SESSION_KEY] = data


def account_can_receive_mail(user):
    return user.is_active and user.account_status == 'active'
