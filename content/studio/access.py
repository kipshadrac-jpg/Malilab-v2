from functools import wraps
from urllib.parse import quote

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from content.services import ROLE_GROUPS

ROLE_LABELS = {'author_editor': 'Author', 'reviewer': 'Reviewer',
               'approver_publisher': 'Approver', 'administrator': 'Administrator'}
ROLE_ORDER = ('author_editor', 'reviewer', 'approver_publisher', 'administrator')


def _verified(user):
    check = getattr(user, 'is_verified', None)
    return bool(callable(check) and check())


def staff_roles(user):
    """Editorial roles of a signed-in, MFA-verified, active staff account; empty set otherwise."""
    if not (user.is_authenticated and user.is_active and user.is_staff and _verified(user)):
        return set()
    names = set(user.groups.values_list('name', flat=True))
    return {role for role, group in ROLE_GROUPS.items() if group in names}


def studio_view(*allowed):
    """Studio pages: the OTP sign-in for staff who are not verified yet, 404 for everyone else."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated or (user.is_staff and not _verified(user)):
                if user.is_authenticated and not user.is_staff:
                    raise Http404
                return redirect(f"{reverse('otp_admin:login')}?next={quote(request.get_full_path())}")
            roles = staff_roles(user)
            if not roles or (allowed and not roles.intersection(allowed)):
                raise Http404
            request.studio_roles = roles
            return view(request, *args, **kwargs)
        return never_cache(wrapped)
    return decorator


def page(request, template, context=None, status=200):
    context = dict(context or {})
    context['role_labels'] = ', '.join(ROLE_LABELS[r] for r in ROLE_ORDER if r in request.studio_roles)
    return render(request, template, context, status=status)
