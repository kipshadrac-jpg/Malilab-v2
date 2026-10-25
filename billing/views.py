"""Website pages for buying: the locked-page notice, the unlock form, and the waiting page."""
from urllib.parse import quote, urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.cache import add_never_cache_headers
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

from content.models import Module
from . import service
from .models import Payment


def _render(request, template, context, status=200):
    context.update({'user': request.user, 'csrf_token': get_token(request), 'request': request})
    response = HttpResponse(render_to_string(template, context), status=status)
    add_never_cache_headers(response)
    return response


def safe_next(request, value, fallback='/modules/'):
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return fallback


def locked_page(request, modules, title, summary, kind):
    """Shown instead of a lesson or practice the visitor has not unlocked."""
    here = request.get_full_path()
    signed_in = request.user.is_authenticated and request.user.can_use_personal_features
    rows = [{'title': m['title'], 'url': '%s?%s' % (reverse('unlock'), urlencode({'module': m['slug'], 'next': here}))} for m in modules]
    return _render(request, 'billing/locked.html', {
        'title': title, 'summary': summary, 'kind': kind, 'modules': rows, 'signed_in': signed_in,
        'sign_in_url': '%s?next=%s' % (reverse('sign-in'), quote(here)),
        'all_url': '%s?%s' % (reverse('unlock'), urlencode({'next': here})),
        'price_module': service.MODULE_PRICE, 'price_all': service.ALL_PRICE,
    })


@login_required(login_url='sign-in')
def unlock(request):
    user = request.user
    if not user.can_use_personal_features:
        return redirect('sign-in')
    source = request.POST if request.method == 'POST' else request.GET
    module = Module.objects.filter(slug=source.get('module', ''), status='published').first() if source.get('module') else None
    nxt = safe_next(request, source.get('next'), fallback=reverse('module-detail', args=[module.slug]) if module else '/modules/')
    if module is not None and service.owns_module(user, module):
        return redirect(nxt)
    if module is None and service.owns_all(user):
        return redirect(nxt)
    error = None
    if request.method == 'POST':
        product = request.POST.get('product', 'module' if module else 'all')
        try:
            payment = service.start_payment(user, product, module if product == 'module' else None, request.POST.get('phone', ''))
        except service.BillingError as exc:
            error = str(exc)
        else:
            return redirect('%s?%s' % (reverse('unlock-waiting', args=[payment.pk]), urlencode({'next': nxt})))
    info = service.status(user)
    title = module.current_published_revision.title if module is not None and module.current_published_revision_id else ''
    return _render(request, 'billing/unlock.html', {
        'module': module, 'module_title': title, 'next': nxt, 'error': error, 'sandbox': info['sandbox'],
        'price_module': service.MODULE_PRICE, 'price_all': service.ALL_PRICE,
        'phone': request.POST.get('phone', ''), 'choice': request.POST.get('product', 'module' if module else 'all'),
    }, status=400 if error else 200)


def _own_payment(request, payment_id):
    payment = Payment.objects.filter(pk=payment_id, user=request.user).select_related('module').first()
    if payment is None:
        raise Http404
    return payment


@login_required(login_url='sign-in')
@require_GET
def waiting(request, payment_id):
    payment = service.refresh(_own_payment(request, payment_id))
    nxt = safe_next(request, request.GET.get('next'))
    if payment.status == 'paid':
        return redirect(nxt)
    return _render(request, 'billing/waiting.html', {
        'payment': payment, 'next': nxt, 'status_url': reverse('unlock-status', args=[payment.pk]),
        'sandbox': service.status(request.user)['sandbox'],
    })


@login_required(login_url='sign-in')
@require_GET
def payment_status(request, payment_id):
    payment = service.refresh(_own_payment(request, payment_id))
    response = JsonResponse({'status': payment.status, 'detail': payment.result_desc})
    add_never_cache_headers(response)
    return response
