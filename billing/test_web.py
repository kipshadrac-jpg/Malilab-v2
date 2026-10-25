import json
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.models import UserAccount
from billing import daraja
from billing.models import ModuleUnlock, Payment
from billing.test_billing import CALLBACK, MPESA, callback_body, fake_network
from config.test_6b11 import SiteFixtureMixin
from content.models import Module

BODY = 'A sacco is a savings society.'


@override_settings(SECURE_SSL_REDIRECT=False, MALILAB_PAYWALL=True, **MPESA)
class WebGatingTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()
        self.module = Module.objects.get(slug='mod')
        self.client = Client()

    def sign_in(self):
        self.client.force_login(self.user)

    def test_anonymous_visitor_does_not_get_the_lesson(self):
        page = self.client.get('/lessons/les/?module=mod')
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, BODY)
        self.assertContains(page, 'Sign in')
        self.assertIn('no-store', page['Cache-Control'])

    def test_signed_in_learner_without_the_module_sees_unlock_links(self):
        self.sign_in()
        page = self.client.get('/lessons/les/?module=mod')
        self.assertNotContains(page, BODY)
        self.assertContains(page, 'Unlock Saving module')
        self.assertContains(page, 'KES 100')
        self.assertContains(page, 'KES 900')
        self.assertContains(page, '/unlock/?module=mod')

    def test_owner_reads_the_lesson(self):
        self.sign_in()
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        self.assertContains(self.client.get('/lessons/les/?module=mod'), BODY)

    @override_settings(MALILAB_PAYWALL=False)
    def test_with_the_paywall_off_the_lesson_is_open_to_everyone(self):
        self.assertContains(self.client.get('/lessons/les/'), BODY)

    def test_module_page_offers_unlock_but_still_lists_lessons(self):
        page = self.client.get('/modules/mod/')
        self.assertContains(page, 'Sacco basics')
        self.assertContains(page, 'Unlock · KES 100')
        self.sign_in()
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        self.assertNotContains(self.client.get('/modules/mod/'), 'Unlock · KES')

    def test_practice_page_and_start_are_locked(self):
        self.sign_in()
        page = self.client.get('/practice/prac/')
        self.assertNotContains(page, 'Start Practice')
        self.assertContains(page, 'Unlock Saving module')
        started = self.client.post('/practice/prac/attempts/')
        self.assertEqual(started.status_code, 302)
        self.assertIn('/unlock/', started['Location'])
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        self.assertContains(self.client.get('/practice/prac/'), 'Start Practice')
        self.assertEqual(self.client.post('/practice/prac/attempts/').status_code, 302)

    # ---- the unlock pages
    def test_unlock_needs_sign_in(self):
        response = self.client.get('/unlock/?module=mod')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/sign-in/', response['Location'])

    def test_unlock_page_shows_both_choices(self):
        self.sign_in()
        page = self.client.get('/unlock/?module=mod')
        self.assertContains(page, 'Unlock Saving module')
        self.assertContains(page, 'This module — KES 100')
        self.assertContains(page, 'All modules — KES 900')
        self.assertContains(page, 'Test mode')

    def test_paying_from_the_website_end_to_end(self):
        self.sign_in()
        with mock.patch.object(daraja, '_request', fake_network()):
            response = self.client.post('/unlock/', {'module': 'mod', 'product': 'module', 'phone': '0712 345 678', 'next': '/lessons/les/?module=mod'})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get()
        self.assertEqual((payment.amount, payment.phone), (100, '254712345678'))
        waiting = self.client.get(response['Location'])
        self.assertEqual(waiting.status_code, 200)
        self.assertContains(waiting, 'Check your phone')
        self.assertContains(waiting, '/unlock/status/%d/' % payment.pk)
        self.assertEqual(self.client.get('/unlock/status/%d/' % payment.pk).json()['status'], 'pending')
        self.client.post(CALLBACK, data=json.dumps(callback_body(payment.checkout_request_id)), content_type='application/json')
        self.assertEqual(self.client.get('/unlock/status/%d/' % payment.pk).json()['status'], 'paid')
        again = self.client.get(response['Location'])
        self.assertEqual((again.status_code, again['Location']), (302, '/lessons/les/?module=mod'))
        self.assertContains(self.client.get('/lessons/les/?module=mod'), BODY)

    def test_bad_phone_shows_the_message_on_the_page(self):
        self.sign_in()
        response = self.client.post('/unlock/', {'module': 'mod', 'product': 'module', 'phone': '123'})
        self.assertContains(response, 'Safaricom number', status_code=400)
        self.assertEqual(Payment.objects.count(), 0)

    def test_the_next_address_cannot_leave_the_site(self):
        self.sign_in()
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        response = self.client.get('/unlock/?module=mod&next=https://evil.example/steal')
        self.assertEqual(response['Location'], '/modules/mod/')

    def test_owned_module_goes_straight_back(self):
        self.sign_in()
        ModuleUnlock.objects.create(user=self.user, module=self.module, source='grant')
        response = self.client.get('/unlock/?module=mod&next=/lessons/les/')
        self.assertEqual(response['Location'], '/lessons/les/')

    def test_another_learners_payment_is_not_visible(self):
        self.sign_in()
        with mock.patch.object(daraja, '_request', fake_network()):
            self.client.post('/unlock/', {'module': 'mod', 'product': 'module', 'phone': '0712345678'})
        payment = Payment.objects.get()
        other = UserAccount.objects.create_user('web-other@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        stranger = Client()
        stranger.force_login(other)
        self.assertEqual(stranger.get('/unlock/status/%d/' % payment.pk).status_code, 404)
        self.assertEqual(stranger.get('/unlock/waiting/%d/' % payment.pk).status_code, 404)
