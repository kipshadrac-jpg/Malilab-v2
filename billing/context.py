"""Puts the trial / free-with-ads line on every public page for signed-in learners."""
from . import catalog, service


def strip(request):
    user = getattr(request, 'user', None)
    if not catalog.paywall_on() or user is None or not user.is_authenticated:
        return {}
    if not getattr(user, 'can_use_personal_features', True):
        return {}
    if service.owns_all(user):
        return {}
    t = service.trial(user)
    if t['active']:
        days = (t['seconds_left'] + 86399) // 86400
        return {'billing_strip': {'kind': 'trial', 'days': days, 'module_price': catalog.MODULE_PRICE, 'all_price': catalog.ALL_PRICE}}
    return {'billing_strip': {'kind': 'free', 'module_price': catalog.MODULE_PRICE, 'all_price': catalog.ALL_PRICE}}
