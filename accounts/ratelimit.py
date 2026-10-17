"""Hourly brake for the account-email forms (register, forgot password).

Every submission counts, whether or not the address exists, so the limit reveals nothing.
Per address: 3 per hour. Per visitor address: 10 per hour. Uses Django's cache (no new dependency).
"""
import hashlib

from django.core.cache import cache

WINDOW_SECONDS = 60 * 60
EMAIL_LIMIT = 3
IP_LIMIT = 10


def client_ip(request):
    remote = request.META.get('REMOTE_ADDR', '')
    if remote in ('127.0.0.1', '::1'):  # request came through nginx on this machine
        return request.META.get('HTTP_X_REAL_IP', '').strip()[:45] or remote
    return remote


def _count(key):
    if cache.add(key, 1, WINDOW_SECONDS):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, WINDOW_SECONDS)
        return 1


def too_many(request, scope, email):
    """Count this request; return True when it is over the limit."""
    ident = hashlib.sha256((email or '').strip().casefold().encode()).hexdigest()[:32]
    over_email = _count(f'acct-rl:{scope}:email:{ident}') > EMAIL_LIMIT
    over_ip = _count(f'acct-rl:{scope}:ip:{client_ip(request)}') > IP_LIMIT
    return over_email or over_ip
