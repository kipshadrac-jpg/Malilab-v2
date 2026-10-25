"""Who owns what, and how a payment becomes ownership."""
import hmac
import re
from datetime import timedelta

from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from content.models import Module
from content.public import public_lesson_modules, public_modules
from . import daraja
from .catalog import ALL_PRICE, MODULE_PRICE, TRIAL_DAYS, all_covers_future, paywall_on, price_of, providers
from .models import Entitlement, ModuleUnlock, Payment

PENDING_LIFETIME = timedelta(minutes=10)
POLL_GAP = timedelta(seconds=8)
PAY_LIMIT = 6              # prompts per learner per 10 minutes


class BillingError(Exception):
    """A problem the learner can read."""

    def __init__(self, message, code='billing', status=400):
        super().__init__(message)
        self.code, self.status = code, status


# ------------------------------------------------------------------------------------------------ what a learner owns
def entitlement(user):
    """The learner's row; the 3-day trial starts the first time this is asked for."""
    row, _ = Entitlement.objects.get_or_create(user=user, defaults={'trial_started_at': timezone.now()})
    return row


def trial(user):
    row = entitlement(user)
    ends = row.trial_started_at + timedelta(days=TRIAL_DAYS)
    left = (ends - timezone.now()).total_seconds()
    return {'active': left > 0, 'ends_at': ends.isoformat(), 'seconds_left': max(0, int(left))}


def owns_all(user, module=None):
    row = Entitlement.objects.filter(user=user, all_modules_at__isnull=False).first()
    if row is None:
        return False
    if module is None or all_covers_future():
        return True
    return module.created_at <= row.all_modules_at


def owns_module(user, module):
    return owns_all(user, module) or ModuleUnlock.objects.filter(user=user, module=module).exists()


def unlocked_slugs(user):
    slugs = set(ModuleUnlock.objects.filter(user=user).values_list('module__slug', flat=True))
    row = Entitlement.objects.filter(user=user, all_modules_at__isnull=False).first()
    if row is not None:
        for m in public_modules():
            if all_covers_future() or m.created_at <= row.all_modules_at:
                slugs.add(m.slug)
    return sorted(slugs)


def lesson_gate(user, lesson_revision):
    """None when this lesson is open to the learner, otherwise the modules that would open it."""
    if not paywall_on():
        return None
    mods = list(public_lesson_modules(lesson_revision))
    if not mods or any(owns_module(user, m) for m in mods):
        return None
    return [{'slug': m.slug, 'title': m.current_published_revision.title} for m in mods]


def practice_modules(activity):
    """The published modules that hold this practice activity."""
    return list(Module.objects.filter(
        status='published', current_published_revision__learning_requirements__target_kind='practice',
        current_published_revision__learning_requirements__active=True,
        current_published_revision__learning_requirements__practice_revision__activity=activity,
    ).select_related('current_published_revision').distinct())


def web_gate(user, modules):
    """For website pages. None when the visitor may read; otherwise the modules that would open the page.

    Visitors who are not signed in are blocked too, because ownership belongs to an account."""
    if not modules:
        return None
    if getattr(user, 'is_authenticated', False) and user.can_use_personal_features and any(owns_module(user, m) for m in modules):
        return None
    return [{'slug': m.slug, 'title': m.current_published_revision.title} for m in modules]


def practice_gate(user, activity):
    """Same idea for a practice activity that belongs to modules."""
    if not paywall_on():
        return None
    mods = practice_modules(activity)
    if not mods or any(owns_module(user, m) for m in mods):
        return None
    return [{'slug': m.slug, 'title': m.current_published_revision.title} for m in mods]


def status(user):
    t = trial(user)
    on = paywall_on()
    return {
        'paywall': on, 'trial': t, 'ads': bool(on and not t['active']),
        'all_modules': owns_all(user), 'modules': unlocked_slugs(user),
        'prices': {'module': MODULE_PRICE, 'all': ALL_PRICE, 'currency': 'KES'},
        'providers': providers(), 'sandbox': daraja.sandbox(),
    }


# ------------------------------------------------------------------------------------------------ paying
def normalize_phone(raw):
    """07xx / 01xx / +2547xx / 2547xx -> 2547xxxxxxxx, or None."""
    digits = re.sub(r'[\s\-().+]', '', raw or '')
    if re.fullmatch(r'0[17]\d{8}', digits):
        digits = '254' + digits[1:]
    return digits if re.fullmatch(r'254[17]\d{8}', digits) else None


def _guard(user):
    key = 'pay-rl:%s:%s' % (user.pk, int(timezone.now().timestamp() // 600))
    if cache.add(key, 1, 700):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        count = 1
    if count > PAY_LIMIT:
        raise BillingError('Too many payment attempts. Please wait a few minutes and try again.', 'too_many', 429)


def start_payment(user, product, module, phone):
    if 'mpesa' not in providers():
        raise BillingError('Paying with M-Pesa is not available here.', 'unavailable')
    if product == 'module':
        if module is None:
            raise BillingError('Choose a module.')
        if owns_module(user, module):
            raise BillingError('You already have this module.', 'owned')
    elif product == 'all':
        if owns_all(user):
            raise BillingError('You already have every module.', 'owned')
        module = None
    else:
        raise BillingError('Choose what to buy.')
    number = normalize_phone(phone)
    if number is None:
        raise BillingError('Enter a Safaricom number such as 0712 345 678.', 'bad_phone')
    if Payment.objects.filter(user=user, status='pending', created_at__gte=timezone.now() - timedelta(seconds=60)).exists():
        raise BillingError('A payment prompt was just sent to your phone. Approve it, or wait a minute and try again.', 'busy', 409)
    _guard(user)
    payment = Payment.objects.create(user=user, product=product, module=module, amount=price_of(product), phone=number, sandbox=daraja.sandbox())
    try:
        reply = daraja.stk_push(payment)
    except daraja.DarajaError as exc:
        payment.status, payment.result_desc = 'failed', str(exc)[:300]
        payment.save(update_fields=['status', 'result_desc', 'updated_at'])
        raise BillingError('We could not send the payment prompt. Please try again in a moment.', 'gateway', 502)
    payment.merchant_request_id = str(reply.get('MerchantRequestID', ''))[:64]
    payment.checkout_request_id = str(reply.get('CheckoutRequestID', ''))[:64]
    payment.customer_message = str(reply.get('CustomerMessage', ''))[:300]
    payment.save(update_fields=['merchant_request_id', 'checkout_request_id', 'customer_message', 'updated_at'])
    return payment


@transaction.atomic
def fulfil(payment):
    """Turn a paid payment into ownership. Safe to run twice."""
    if payment.product == 'module' and payment.module_id:
        ModuleUnlock.objects.get_or_create(user=payment.user, module=payment.module, defaults={'payment': payment, 'source': 'payment'})
    elif payment.product == 'all':
        row = entitlement(payment.user)
        if row.all_modules_at is None:
            row.all_modules_at = payment.paid_at or timezone.now()
            row.save(update_fields=['all_modules_at', 'updated_at'])


@transaction.atomic
def settle(payment_id, result_code, description='', receipt='', amount=None, raw=None):
    """Record how a prompt ended. Idempotent: a repeated or late message never grants twice."""
    p = Payment.objects.select_for_update().get(pk=payment_id)
    if raw is not None and not p.callback:
        p.callback = raw
    code = str(result_code)
    if p.status == 'paid':
        if receipt and not p.receipt:
            p.receipt = receipt[:40]
        p.save()
        return p
    if code == '0':
        if amount is not None and int(round(float(amount))) < p.amount:
            p.status, p.result_code, p.result_desc = 'review', code, 'Amount received was lower than the price.'
            p.save()
            return p
        p.status, p.result_code, p.result_desc = 'paid', code, (description or 'Paid')[:300]
        p.receipt, p.paid_at = receipt[:40], timezone.now()
        p.save()
        fulfil(p)
        return p
    if p.status == 'pending':
        p.result_code, p.result_desc = code, description[:300]
        p.status = 'cancelled' if code == '1032' else 'expired' if code == '1037' else 'failed'
    p.save()
    return p


def refresh(payment):
    """For the app's polling: ask Safaricom if the callback has not arrived yet, and expire old prompts."""
    if payment.status != 'pending':
        return payment
    now = timezone.now()
    if payment.checkout_request_id and (payment.last_checked is None or now - payment.last_checked >= POLL_GAP) and now - payment.created_at >= timedelta(seconds=10):
        payment.last_checked = now
        payment.save(update_fields=['last_checked', 'updated_at'])
        try:
            result = daraja.stk_query(payment.checkout_request_id)
        except daraja.DarajaError:
            result = {}
        if result:
            return settle(payment.pk, result['ResultCode'], result.get('ResultDesc', ''))
    if now - payment.created_at > PENDING_LIFETIME:
        payment.status, payment.result_desc = 'expired', 'No answer from the phone.'
        payment.save(update_fields=['status', 'result_desc', 'updated_at'])
    return payment


def parse_callback(data):
    """Pull the useful parts out of Safaricom's callback body. Returns a dict, or None when it is not one."""
    try:
        cb = data['Body']['stkCallback']
        out = {'checkout': str(cb['CheckoutRequestID']), 'code': str(cb['ResultCode']), 'desc': str(cb.get('ResultDesc', '')), 'receipt': '', 'amount': None}
        items = (cb.get('CallbackMetadata') or {}).get('Item') or []
        for item in items:
            if item.get('Name') == 'MpesaReceiptNumber':
                out['receipt'] = str(item.get('Value', ''))
            elif item.get('Name') == 'Amount':
                out['amount'] = item.get('Value')
        return out
    except (KeyError, TypeError, AttributeError):
        return None


def secret_ok(given, expected):
    return bool(expected) and hmac.compare_digest(str(given), str(expected))


def prices_note():
    return {'module': MODULE_PRICE, 'all': ALL_PRICE, 'currency': 'KES'}
