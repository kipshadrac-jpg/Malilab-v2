"""Payments for the app. Every call except Safaricom's callback needs the learner's sign-in token."""
import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.api import _body, _error, _json
from content.models import Module
from notepad.api import learner
from . import service
from .models import Entitlement, ModuleUnlock, Payment


def _payment(p):
    return {
        'id': p.pk, 'status': p.status, 'product': p.product, 'module': p.module.slug if p.module_id else None,
        'module_title': p.module.current_published_revision.title if p.module_id and p.module.current_published_revision_id else '',
        'amount': p.amount, 'receipt': p.receipt, 'message': p.customer_message, 'detail': p.result_desc,
        'sandbox': p.sandbox, 'created_at': p.created_at.isoformat(), 'paid_at': p.paid_at.isoformat() if p.paid_at else None,
    }


@require_GET
@learner
def status(request):
    return _json(service.status(request.learner))


@require_POST
@learner
def pay(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    product = data.get('product')
    module = None
    if product == 'module':
        module = Module.objects.filter(slug=str(data.get('module', '')), status='published').first()
        if module is None:
            return _error('not_found', 'That module was not found.', 404)
    try:
        payment = service.start_payment(request.learner, product, module, data.get('phone'))
    except service.BillingError as exc:
        return _error(exc.code, str(exc), exc.status)
    return _json(_payment(payment), status=201)


@require_GET
@learner
def payment_detail(request, payment_id):
    payment = Payment.objects.filter(pk=payment_id, user=request.learner).select_related('module', 'module__current_published_revision').first()
    if payment is None:
        return _error('not_found', 'That payment was not found.', 404)
    payment = service.refresh(payment)
    return _json({'payment': _payment(payment), 'status': service.status(request.learner)})


@require_GET
@learner
def payment_list(request):
    rows = Payment.objects.filter(user=request.learner).select_related('module', 'module__current_published_revision')[:50]
    granted = ModuleUnlock.objects.filter(user=request.learner, source='grant').select_related('module', 'module__current_published_revision')
    entitlement = Entitlement.objects.filter(user=request.learner, all_modules_at__isnull=False).first()
    return _json({
        'payments': [_payment(p) for p in rows],
        'granted': [{'slug': g.module.slug, 'title': g.module.current_published_revision.title if g.module.current_published_revision_id else g.module.slug,
                     'at': g.created_at.isoformat()} for g in granted],
        'all_modules_at': entitlement.all_modules_at.isoformat() if entitlement else None,
    })


@csrf_exempt
@never_cache
@require_POST
def mpesa_callback(request, secret):
    """Safaricom reports how the prompt ended. Always answers 200 so Safaricom stops retrying."""
    ack = {'ResultCode': 0, 'ResultDesc': 'Accepted'}
    if not service.secret_ok(secret, getattr(settings, 'MPESA_CALLBACK_SECRET', '')):
        return HttpResponse(status=404)
    try:
        raw = json.loads(request.body.decode() or '{}')
    except (ValueError, UnicodeDecodeError):
        return _json(ack)
    info = service.parse_callback(raw)
    if info is None:
        return _json(ack)
    payment = Payment.objects.filter(checkout_request_id=info['checkout']).first()
    if payment is not None:
        service.settle(payment.pk, info['code'], info['desc'], info['receipt'], info['amount'], raw)
    return _json(ack)
