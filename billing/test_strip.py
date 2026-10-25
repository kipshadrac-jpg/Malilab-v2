from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from billing.models import Entitlement

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class StripTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('strip@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.client.force_login(self.user)

    def test_no_strip_when_paywall_is_off(self):
        with override_settings(MALILAB_PAYWALL=False):
            self.assertNotContains(self.client.get('/modules/'), 'billing-strip')

    def test_trial_strip(self):
        with self.settings(MALILAB_PAYWALL=True):
            page = self.client.get('/modules/')
        self.assertContains(page, 'Free trial')

    def test_free_plan_strip_after_trial(self):
        Entitlement.objects.create(user=self.user, trial_started_at=timezone.now() - timedelta(days=9))
        with self.settings(MALILAB_PAYWALL=True):
            page = self.client.get('/modules/')
        self.assertContains(page, 'free plan')

    def test_all_modules_owner_sees_no_strip(self):
        Entitlement.objects.create(user=self.user, trial_started_at=timezone.now() - timedelta(days=9), all_modules_at=timezone.now())
        with self.settings(MALILAB_PAYWALL=True):
            self.assertNotContains(self.client.get('/modules/'), 'billing-strip')

    def test_signed_out_visitors_see_no_strip(self):
        self.client.logout()
        with self.settings(MALILAB_PAYWALL=True):
            self.assertNotContains(self.client.get('/modules/'), 'billing-strip')
