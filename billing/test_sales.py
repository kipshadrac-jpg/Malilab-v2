import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from billing.models import Entitlement, ModuleUnlock, Payment
from billing.reports import sales_summary
from content.models import Module, ModuleRevision
from config.test_6b11 import publish

User = get_user_model()


def learner(email):
    return User.objects.create_user(email, 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


def pay(user, amount, product='module', module=None, sandbox=False, status='paid', when=None):
    p = Payment.objects.create(user=user, product=product, module=module, amount=amount, phone='254712345678', status=status, sandbox=sandbox,
                               receipt='R%d' % (Payment.objects.count() + 1))
    if status == 'paid':
        Payment.objects.filter(pk=p.pk).update(paid_at=when or timezone.now())
    return p


class SalesSummaryTests(TestCase):
    def setUp(self):
        self.user = learner('s1@example.com')

    def test_live_and_test_money_are_kept_apart(self):
        pay(self.user, 100)
        pay(self.user, 900, product='all')
        pay(self.user, 100, sandbox=True)
        s = sales_summary()
        self.assertEqual((s['live']['all']['count'], s['live']['all']['amount']), (2, 1000))
        self.assertEqual((s['live']['modules']['amount'], s['live']['all_pass']['amount']), (100, 900))
        self.assertEqual((s['test']['all']['count'], s['test']['all']['amount']), (1, 100))

    def test_unpaid_payments_do_not_count(self):
        pay(self.user, 100, status='cancelled')
        pay(self.user, 100, status='pending')
        self.assertEqual(sales_summary()['live']['all']['count'], 0)

    def test_periods(self):
        pay(self.user, 100)
        pay(self.user, 100, when=timezone.now() - timedelta(days=3))
        pay(self.user, 100, when=timezone.now() - timedelta(days=20))
        pay(self.user, 100, when=timezone.now() - timedelta(days=60))
        live = sales_summary()['live']
        self.assertEqual((live['today']['count'], live['week']['count'], live['month']['count'], live['all']['count']), (1, 2, 3, 4))
        self.assertEqual(len(live['days']), 14)
        self.assertEqual(sum(d['amount'] for d in live['days']), 200)

    def test_flags_for_review_and_stuck_prompts(self):
        pay(self.user, 100, status='review')
        old = pay(self.user, 100, status='pending')
        Payment.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(minutes=30))
        pay(self.user, 100, status='pending')
        s = sales_summary()
        self.assertEqual((s['review'], s['stuck']), (1, 1))


@override_settings(SECURE_SSL_REDIRECT=False)
class SalesAdminTests(TestCase):
    def setUp(self):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        boss = User.objects.create_superuser('boss@example.com', 'strong-password-123')
        device = TOTPDevice.objects.create(user=boss, name='t', confirmed=True)
        self.admin = Client()
        self.admin.force_login(boss)
        session = self.admin.session
        session['otp_device_id'] = device.persistent_id
        session.save()
        self.user = learner('s2@example.com')

    def test_changelist_shows_the_summary(self):
        pay(self.user, 100)
        page = self.admin.get('/admin/billing/payment/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Sales summary')
        self.assertContains(page, 'Live money')

    def test_csv_download(self):
        p = pay(self.user, 100)
        response = self.admin.post('/admin/billing/payment/', {'action': 'export_csv', '_selected_action': [p.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        text = response.content.decode()
        self.assertIn('s2@example.com', text)
        self.assertIn('mpesa_receipt', text)

    def test_payments_cannot_be_added_or_changed_here(self):
        p = pay(self.user, 100)
        self.assertEqual(self.admin.get('/admin/billing/payment/add/').status_code, 403)
        self.assertEqual(self.admin.post('/admin/billing/payment/%d/delete/' % p.pk).status_code, 403)


@override_settings(SECURE_SSL_REDIRECT=False)
class PurchaseListTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = learner('s3@example.com')
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.user)}
        module = Module.objects.create(slug='mod-x')
        rev = ModuleRevision.objects.create(module=module, revision_number=1, title='Money basics')
        publish(rev, module)
        self.module = module

    def test_list_names_modules_and_shows_granted_and_pass(self):
        pay(self.user, 100, module=self.module)
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        Entitlement.objects.create(user=self.user, trial_started_at=timezone.now(), all_modules_at=timezone.now())
        data = json.loads(Client().get('/api/v1/billing/payments/', **self.auth).content)
        self.assertEqual(data['payments'][0]['module_title'], 'Money basics')
        self.assertEqual(data['granted'][0]['title'], 'Money basics')
        self.assertTrue(data['all_modules_at'])

    def test_list_is_empty_for_a_new_learner(self):
        data = json.loads(Client().get('/api/v1/billing/payments/', **self.auth).content)
        self.assertEqual((data['payments'], data['granted'], data['all_modules_at']), ([], [], None))
