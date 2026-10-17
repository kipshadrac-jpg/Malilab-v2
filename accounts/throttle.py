"""Sign-in brake against password guessing (no new dependency; uses Django's cache).

5 failed sign-ins per email, or 30 per client address, within 15 minutes blocks further attempts
for the rest of the window. Counted whether or not the account exists, so it reveals nothing.
Limitation: the default per-process cache counts per worker; a shared cache can be configured later.
"""
import hashlib

from django.core.cache import cache

EMAIL_LIMIT = 5
IP_LIMIT = 30
WINDOW_SECONDS = 15 * 60


def _client_ip(request):
    """Real visitor address; X-Real-IP is trusted only when the request comes from nginx on this machine."""
    remote = request.META.get('REMOTE_ADDR', '')
    if remote in ('127.0.0.1', '::1'):
        return request.META.get('HTTP_X_REAL_IP', '').strip()[:45] or remote
    return remote


def _keys(request, email):
    ident = hashlib.sha256((email or '').strip().casefold().encode()).hexdigest()[:32]
    return f'signin-fail-email:{ident}', f'signin-fail-ip:{_client_ip(request)}'


def is_blocked(request, email):
    email_key, ip_key = _keys(request, email)
    return cache.get(email_key, 0) >= EMAIL_LIMIT or cache.get(ip_key, 0) >= IP_LIMIT


def record_failure(request, email):
    for key in _keys(request, email):
        if not cache.add(key, 1, WINDOW_SECONDS):
            try:
                cache.incr(key)
            except ValueError:
                cache.add(key, 1, WINDOW_SECONDS)


def clear_failures(request, email):
    cache.delete(_keys(request, email)[0])
