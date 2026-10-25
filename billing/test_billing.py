import json
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from billing import daraja, service
from billing.models import Entitlement, ModuleUnlock, Payment
from config.test_6b11 import SiteFixtureMixin
from content.models import Module, ModuleRevision, Lesson, LessonRevision, ModuleLearningRequirement

MPESA = dict(MPESA_ENV='sandbox', MPESA_CONSUMER_KEY='k', MPESA_CONSUMER_SECRET='s', MPESA_SHORTCODE='174379',
             MPESA_PASSKEY='pass', MPESA_CALLBACK_SECRET='sekret', MPESA_CALLBACK_BASE='https://example.test')
CALLBACK = '/api/v1/billing/mpesa/callback/sekret/'


def fake_network(query=None, push_ok=True):
    """Stands in for Safaricom. [query] is what the status question should answer (None = still in progress)."""
    calls = []

    def request(method, url, headers, body=None):
        calls.append(url)
        if 'oauth' in url:
            return 200, {'access_token': 'tok', 'expires_in': '3599'}
        if 'processrequest' in url:
            if not push_ok:
                return 400, {'errorMessage': 'Bad Request'}
            return 200, {'MerchantRequestID': 'm-1', 'CheckoutRequestID': 'ws_CO_%d' % len(calls), 'ResponseCode': '0',
                         'CustomerMessage': 'Success. Request accepted for processing'}
        if 'query' in url:
            if query is None:
                return 500, {'errorMessage': 'The transaction is being processed'}
            return 200, {'ResultCode': query[0], 'ResultDesc': query[1]}
        raise AssertionError(url)
    request.calls = calls
    return request


def callback_body(checkout, code=0, amount=100, receipt='NLJ7RT61SV'):
    cb = {'MerchantRequestID': 'm-1', 'CheckoutRequestID': checkout, 'ResultCode': code, 'ResultDesc': 'done'}
    if code == 0:
        cb['CallbackMetadata'] = {'Item': [{'Name': 'Amount', 'Value': amount}, {'Name': 'MpesaReceiptNumber', 'Value': receipt},
                                           {'Name': 'PhoneNumber', 'Value': 254708374149}]}
    return {'Body': {'stkCallback': cb}}


@override_settings(SECURE_SSL_REDIRECT=False, MALILAB_PAYWALL=True, **MPESA)
class BillingTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()                      # module "mod" holds lesson "les" and practice "prac"
        self.client = Client()
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.user)}
        self.module = Module.objects.get(slug='mod')
        other = UserAccount.objects.create_user('other-b@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.other_auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(other)}

    def get(self, path, auth=None):
        return self.client.get(path, **(self.auth if auth is None else auth))

    def post(self, path, data=None, auth=None):
        return self.client.post(path, data=json.dumps(data or {}), content_type='application/json', **(self.auth if auth is None else auth))

    def pay(self, product='module', phone='0712345678', network=None, **extra):
        body = {'product': product, 'phone': phone}
        if product == 'module':
            body['module'] = 'mod'
        body.update(extra)
        with mock.patch.object(daraja, '_request', network or fake_network()):
            return self.post('/api/v1/billing/pay/', body)

    # ---- trial and status
    def test_status_needs_sign_in(self):
        self.assertEqual(self.client.get('/api/v1/billing/status/').status_code, 401)

    def test_trial_starts_now_and_lasts_three_days(self):
        data = self.get('/api/v1/billing/status/').json()
        self.assertTrue(data['trial']['active'])
        self.assertAlmostEqual(data['trial']['seconds_left'], 3 * 86400, delta=60)
        self.assertFalse(data['ads'])
        self.assertEqual(data['prices'], {'module': 100, 'all': 900, 'currency': 'KES'})

    def test_ads_start_after_the_trial_and_trial_cannot_restart(self):
        self.get('/api/v1/billing/status/')
        Entitlement.objects.update(trial_started_at=timezone.now() - timedelta(days=4))
        data = self.get('/api/v1/billing/status/').json()
        self.assertFalse(data['trial']['active'])
        self.assertTrue(data['ads'])
        self.assertEqual(Entitlement.objects.count(), 1)

    @override_settings(MALILAB_PAYWALL=False)
    def test_with_the_paywall_off_nothing_is_locked_and_there_are_no_ads(self):
        self.get('/api/v1/billing/status/')
        Entitlement.objects.update(trial_started_at=timezone.now() - timedelta(days=9))
        self.assertFalse(self.get('/api/v1/billing/status/').json()['ads'])
        self.assertEqual(self.client.get('/api/v1/lessons/les/').status_code, 200)

    # ---- gating
    def test_lesson_is_locked_until_the_module_is_owned(self):
        self.assertEqual(self.client.get('/api/v1/lessons/les/').status_code, 401)
        locked = self.get('/api/v1/lessons/les/')
        self.assertEqual(locked.status_code, 402)
        self.assertEqual(locked.json()['error'], 'payment_required')
        self.assertEqual(locked.json()['modules'][0]['slug'], 'mod')
        self.assertEqual(self.post('/api/v1/lessons/les/complete/').status_code, 402)
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        opened = self.get('/api/v1/lessons/les/')
        self.assertEqual(opened.status_code, 200)
        self.assertIn('no-store', opened['Cache-Control'])
        self.assertEqual(self.get('/api/v1/lessons/les/', self.other_auth).status_code, 402)

    def test_the_trial_does_not_open_modules(self):
        self.get('/api/v1/billing/status/')
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 402)

    def test_practice_inside_a_locked_module_is_locked(self):
        self.assertEqual(self.get('/api/v1/practice/prac/').status_code, 402)
        self.assertEqual(self.post('/api/v1/practice/prac/attempts/').status_code, 402)
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        self.assertEqual(self.get('/api/v1/practice/prac/').status_code, 200)

    def test_a_lesson_in_no_module_stays_open(self):
        from config.test_6b11 import publish
        lesson = Lesson.objects.create(slug='loose')
        rev = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='Loose', summary='', blocks=[])
        publish(rev, lesson)
        self.assertEqual(self.get('/api/v1/lessons/loose/').status_code, 200)

    def test_all_modules_pass_covers_later_modules_by_default(self):
        Entitlement.objects.create(user=self.user, trial_started_at=timezone.now(), all_modules_at=timezone.now() - timedelta(days=1))
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 200)
        self.assertIn('mod', self.get('/api/v1/billing/status/').json()['modules'])

    @override_settings(MALILAB_ALL_COVERS_FUTURE=False)
    def test_all_modules_pass_can_be_limited_to_modules_that_existed(self):
        Entitlement.objects.create(user=self.user, trial_started_at=timezone.now(), all_modules_at=timezone.now() - timedelta(days=400))
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 402)

    # ---- phone numbers
    def test_phone_numbers_are_normalised(self):
        for raw in ('0712 345 678', '+254712345678', '254712345678', '0112345678', '0712-345-678'):
            self.assertTrue(service.normalize_phone(raw).startswith('254'), raw)
        self.assertEqual(service.normalize_phone('0712345678'), '254712345678')
        for bad in ('', '12345', '0212345678', '2547123456789', 'abc', None):
            self.assertIsNone(service.normalize_phone(bad), bad)

    # ---- paying
    def test_paying_for_a_module_end_to_end(self):
        response = self.pay()
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual((body['status'], body['amount'], body['module']), ('pending', 100, 'mod'))
        payment = Payment.objects.get()
        self.assertEqual((payment.phone, payment.sandbox, payment.user_id), ('254712345678', True, self.user.pk))
        self.assertTrue(payment.checkout_request_id)
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 402)       # a prompt alone unlocks nothing
        cb = self.post(CALLBACK, callback_body(payment.checkout_request_id), auth={})
        self.assertEqual(cb.json()['ResultCode'], 0)
        payment.refresh_from_db()
        self.assertEqual((payment.status, payment.receipt), ('paid', 'NLJ7RT61SV'))
        self.assertTrue(ModuleUnlock.objects.filter(user=self.user, module=self.module, payment=payment).exists())
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 200)
        self.assertEqual(self.get('/api/v1/billing/status/').json()['modules'], ['mod'])

    def test_a_repeated_callback_grants_once(self):
        self.pay()
        payment = Payment.objects.get()
        for _ in range(3):
            self.post(CALLBACK, callback_body(payment.checkout_request_id), auth={})
        self.assertEqual(ModuleUnlock.objects.count(), 1)
        self.assertEqual(Payment.objects.get().status, 'paid')

    def test_the_callback_needs_the_secret(self):
        self.pay()
        payment = Payment.objects.get()
        wrong = self.post('/api/v1/billing/mpesa/callback/nope/', callback_body(payment.checkout_request_id), auth={})
        self.assertEqual(wrong.status_code, 404)
        self.assertEqual(Payment.objects.get().status, 'pending')
        self.assertEqual(ModuleUnlock.objects.count(), 0)

    @override_settings(MPESA_CALLBACK_SECRET='')
    def test_an_empty_secret_never_matches(self):
        self.assertEqual(self.post('/api/v1/billing/mpesa/callback//', {}, auth={}).status_code, 404)

    def test_junk_and_unknown_callbacks_are_acknowledged_and_ignored(self):
        self.assertEqual(self.post(CALLBACK, {'hello': 1}, auth={}).status_code, 200)
        self.assertEqual(self.post(CALLBACK, callback_body('ws_CO_unknown'), auth={}).status_code, 200)
        self.assertEqual(ModuleUnlock.objects.count(), 0)

    def test_a_cancelled_prompt_unlocks_nothing_and_can_be_retried(self):
        self.pay()
        payment = Payment.objects.get()
        self.post(CALLBACK, callback_body(payment.checkout_request_id, code=1032), auth={})
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'cancelled')
        self.assertEqual(ModuleUnlock.objects.count(), 0)
        Payment.objects.update(created_at=timezone.now() - timedelta(minutes=5))
        self.assertEqual(self.pay().status_code, 201)

    def test_a_short_payment_is_held_for_review(self):
        self.pay()
        payment = Payment.objects.get()
        self.post(CALLBACK, callback_body(payment.checkout_request_id, amount=1), auth={})
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'review')
        self.assertEqual(ModuleUnlock.objects.count(), 0)

    def test_a_late_success_still_counts_after_expiry(self):
        self.pay()
        payment = Payment.objects.get()
        Payment.objects.update(status='expired')
        self.post(CALLBACK, callback_body(payment.checkout_request_id), auth={})
        self.assertEqual(Payment.objects.get().status, 'paid')
        self.assertEqual(ModuleUnlock.objects.count(), 1)

    def test_the_all_modules_pass(self):
        response = self.pay(product='all')
        self.assertEqual((response.status_code, response.json()['amount']), (201, 900))
        payment = Payment.objects.get()
        self.post(CALLBACK, callback_body(payment.checkout_request_id, amount=900), auth={})
        status = self.get('/api/v1/billing/status/').json()
        self.assertTrue(status['all_modules'])
        self.assertEqual(self.get('/api/v1/lessons/les/').status_code, 200)
        self.assertEqual(self.pay(product='all').status_code, 400)             # already owned

    def test_buying_a_module_you_own_is_refused(self):
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        response = self.pay()
        self.assertEqual((response.status_code, response.json()['error']), (400, 'owned'))
        self.assertEqual(Payment.objects.count(), 0)

    def test_bad_input_is_refused(self):
        self.assertEqual(self.pay(phone='12345').json()['error'], 'bad_phone')
        self.assertEqual(self.pay(module='ghost').status_code, 404)
        self.assertEqual(self.pay(product='gift').status_code, 400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_a_second_prompt_within_a_minute_is_refused(self):
        self.assertEqual(self.pay().status_code, 201)
        self.assertEqual(self.pay().status_code, 409)

    def test_gateway_failure_is_recorded_and_reported(self):
        response = self.pay(network=fake_network(push_ok=False))
        self.assertEqual((response.status_code, response.json()['error']), (502, 'gateway'))
        self.assertEqual(Payment.objects.get().status, 'failed')

    @override_settings(MPESA_CONSUMER_KEY='')
    def test_missing_settings_fail_cleanly(self):
        self.assertEqual(self.pay().status_code, 502)
        self.assertEqual(Payment.objects.get().status, 'failed')

    @override_settings(MALILAB_PAY_PROVIDERS=[])
    def test_the_provider_can_be_switched_off(self):
        self.assertEqual(self.pay().json()['error'], 'unavailable')

    # ---- polling
    def test_polling_asks_safaricom_when_the_callback_is_lost(self):
        self.pay()
        payment = Payment.objects.get()
        Payment.objects.update(created_at=timezone.now() - timedelta(seconds=30))
        with mock.patch.object(daraja, '_request', fake_network(query=('0', 'The service request is processed successfully.'))):
            body = self.get('/api/v1/billing/payments/%d/' % payment.pk).json()
        self.assertEqual(body['payment']['status'], 'paid')
        self.assertIn('mod', body['status']['modules'])

    def test_polling_while_still_in_progress_keeps_waiting(self):
        self.pay()
        payment = Payment.objects.get()
        Payment.objects.update(created_at=timezone.now() - timedelta(seconds=30))
        with mock.patch.object(daraja, '_request', fake_network(query=None)):
            body = self.get('/api/v1/billing/payments/%d/' % payment.pk).json()
        self.assertEqual(body['payment']['status'], 'pending')

    def test_old_prompts_expire(self):
        self.pay()
        payment = Payment.objects.get()
        Payment.objects.update(created_at=timezone.now() - timedelta(minutes=11))
        with mock.patch.object(daraja, '_request', fake_network(query=None)):
            body = self.get('/api/v1/billing/payments/%d/' % payment.pk).json()
        self.assertEqual(body['payment']['status'], 'expired')

    def test_payments_are_private(self):
        self.pay()
        payment = Payment.objects.get()
        self.assertEqual(self.get('/api/v1/billing/payments/%d/' % payment.pk, self.other_auth).status_code, 404)
        self.assertEqual(self.get('/api/v1/billing/payments/', self.other_auth).json()['payments'], [])
        self.assertEqual(len(self.get('/api/v1/billing/payments/').json()['payments']), 1)

    def test_pay_needs_sign_in(self):
        self.assertEqual(self.client.post('/api/v1/billing/pay/', data='{}', content_type='application/json').status_code, 401)


class DarajaClientTests(TestCase):
    @override_settings(**MPESA)
    def test_token_is_cached_and_prompt_uses_the_callback_address(self):
        cache.clear()
        net = fake_network()
        user = UserAccount.objects.create_user('d@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        payment = Payment.objects.create(user=user, product='all', amount=900, phone='254712345678')
        with mock.patch.object(daraja, '_request', net):
            daraja.stk_push(payment)
            daraja.stk_push(payment)
        self.assertEqual(len([u for u in net.calls if 'oauth' in u]), 1)
        self.assertEqual(daraja.callback_url(), 'https://example.test/api/v1/billing/mpesa/callback/sekret/')
        self.assertEqual(daraja.base_url(), daraja.SANDBOX)

    @override_settings(**dict(MPESA, MPESA_ENV='production'))
    def test_production_uses_the_live_address(self):
        self.assertEqual(daraja.base_url(), daraja.LIVE)
        self.assertFalse(daraja.sandbox())
