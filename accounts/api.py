"""Account API for the MaliLab app: sign up with an emailed code, sign in, sign out. Token based, no cookies.

Codes work like the website's (same 6-digit HMAC code, 10 minutes, 5 wrong tries), but because the app has no
browser session, the request is carried in a signed `ticket` that the app sends back with the code.
Nothing here reveals whether an email address already has an account.
"""
import hashlib
import json
import re
import secrets
import time

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from . import emails, ratelimit, registration, registration_views, throttle
from .models import AccountManager, ApiToken

User = get_user_model()

TICKET_SALT = 'malilab-api-ticket'
TOKEN_IDLE_DAYS = 365
MAX_TOKENS_PER_USER = 10


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def _error(code, message, status=400):
    return _json({'error': code, 'message': message}, status=status)


def _body(request):
    try:
        data = json.loads(request.body.decode() or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _text(data, key, limit=200):
    value = data.get(key)
    return value.strip()[:limit] if isinstance(value, str) else ''


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(user, device=''):
    token = secrets.token_urlsafe(32)
    ApiToken.objects.create(user=user, key_hash=_hash(token), device=device[:80])
    keep = list(ApiToken.objects.filter(user=user).order_by('-created').values_list('id', flat=True)[:MAX_TOKENS_PER_USER])
    ApiToken.objects.filter(user=user).exclude(id__in=keep).delete()
    return token


def _bearer(request):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    match = re.match(r'^Bearer\s+([A-Za-z0-9_\-]{20,100})$', header)
    return match.group(1) if match else None


def token_user(request):
    """The signed-in learner for this request, or None. Also refreshes the token's last-used time."""
    token = _bearer(request)
    if not token:
        return None
    row = ApiToken.objects.select_related('user').filter(key_hash=_hash(token)).first()
    if row is None:
        return None
    now = timezone.now()
    if row.last_used and (now - row.last_used).days > TOKEN_IDLE_DAYS:
        row.delete()
        return None
    if not row.user.can_use_personal_features:
        return None
    if row.last_used is None or (now - row.last_used).total_seconds() > 3600:
        ApiToken.objects.filter(pk=row.pk).update(last_used=now)
    return row.user


def _me(user):
    return {'email': user.email, 'verified': user.email_verified, 'joined': user.date_joined.date().isoformat()}


def _session(user, device):
    return {'token': issue_token(user, device), 'user': _me(user)}


# ---------------------------------------------------------------- code request
def _latest_key(purpose, email):
    return 'api-latest:' + hashlib.sha256(f'{purpose}|{email}'.encode()).hexdigest()[:40]


@csrf_exempt
@require_POST
@never_cache
def ask_code(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    kind = _text(data, 'purpose', 12) or 'register'
    if kind not in ('register', 'reset'):
        return _error('bad_request', 'Unknown purpose.')
    raw = _text(data, 'email', 254)
    try:
        validate_email(raw)
    except ValidationError:
        return _error('bad_email', 'Enter a valid email address.')
    if ratelimit.too_many(request, f'api-{kind}', raw):
        return _error('too_many', 'Too many requests. Please wait an hour and try again.', 429)
    email = AccountManager.normalize_identity(raw)
    decide = registration_views._decide_register if kind == 'register' else registration_views._decide_forgot
    purpose, action = decide(User.objects.filter(email=email).first())
    nonce = secrets.token_hex(16)
    code = registration.expected_code(purpose, email, nonce)
    if action == 'code':
        emails.send_code(email, code, purpose)
    elif action == 'already':
        emails.send_already_registered(request, email)
    cache.set(_latest_key(purpose, email), nonce, registration.CODE_MAX_AGE)
    ticket = signing.dumps({'e': email, 'p': purpose, 'n': nonce}, salt=TICKET_SALT)
    return _json({'ticket': ticket, 'expires_in': registration.CODE_MAX_AGE})


# ---------------------------------------------------------------- code + password
BAD_CODE = ('bad_code', 'That code is not right or has expired.')


@csrf_exempt
@require_POST
@never_cache
def verify_code(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    try:
        info = signing.loads(_text(data, 'ticket', 600), salt=TICKET_SALT, max_age=registration.CODE_MAX_AGE)
        email, purpose, nonce = info['e'], info['p'], info['n']
        if purpose not in registration.PURPOSES:
            raise KeyError
    except (signing.BadSignature, KeyError, TypeError):
        return _error('expired', 'This request has expired. Please ask for a new code.')
    if cache.get(_latest_key(purpose, email)) != nonce:
        return _error('expired', 'This request has expired. Please ask for a new code.')
    wrong_key = f'api-wrong:{nonce}'
    if cache.get(wrong_key, 0) >= registration.MAX_WRONG:
        return _error('locked', 'Too many wrong codes. Please ask for a new one.', 429)
    challenge = {'email': email, 'purpose': purpose, 'nonce': nonce}
    if not registration.code_is_right(challenge, data.get('code')):
        if not cache.add(wrong_key, 1, registration.CODE_MAX_AGE):
            try:
                cache.incr(wrong_key)
            except ValueError:
                cache.set(wrong_key, 1, registration.CODE_MAX_AGE)
        return _error(*BAD_CODE)

    password = data.get('password') if isinstance(data.get('password'), str) else ''
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email=email).first()
            usable = user is not None and registration.account_can_receive_mail(user)
            if purpose == 'setup':
                if user is not None and (user.email_verified or not usable):
                    return _error(*BAD_CODE)
                account = user or User(email=email)
            else:
                if not (usable and user.email_verified):
                    return _error(*BAD_CODE)
                account = user
            try:
                validate_password(password, account)
            except ValidationError as exc:
                return _error('weak_password', ' '.join(exc.messages))
            account.set_password(password)
            if purpose == 'setup':
                account.email_verified = True
                account.email_verified_at = timezone.now()
            account.save()
    except IntegrityError:
        return _error(*BAD_CODE)
    cache.delete(_latest_key(purpose, email))
    throttle.clear_failures(request, email)
    return _json(_session(account, _text(data, 'device', 80)), status=201 if purpose == 'setup' else 200)


# ---------------------------------------------------------------- sign in and out
@csrf_exempt
@require_POST
@never_cache
def sign_in(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    email = _text(data, 'email', 254)
    password = data.get('password') if isinstance(data.get('password'), str) else ''
    if throttle.is_blocked(request, email):
        return _error('too_many', 'Too many sign-in attempts. Please wait 15 minutes and try again.', 429)
    user = authenticate(request, email=email, password=password) if email and password else None
    if user is None or not user.can_use_personal_features:
        throttle.record_failure(request, email)
        return _error('bad_credentials', 'We could not sign you in with those details. Check them and try again.', 401)
    throttle.clear_failures(request, email)
    return _json(_session(user, _text(data, 'device', 80)))


@csrf_exempt
@require_POST
@never_cache
def sign_out(request):
    token = _bearer(request)
    if token:
        ApiToken.objects.filter(key_hash=_hash(token)).delete()
    return _json({'ok': True})


@csrf_exempt
@require_GET
@never_cache
def me(request):
    user = token_user(request)
    if user is None:
        return _error('unauthorized', 'Please sign in.', 401)
    return _json({'user': _me(user)})
