"""Patch 14: staff sign in with a password only (OTP optional), one sign-in works for site, Studio and admin, long sessions."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.utils import timezone

from content.services import ROLE_GROUPS

User = get_user_model()
PASSWORD = 'strong-password-123'


def make_staff(email='boss@example.com'):
    user = User.objects.create_user(email, PASSWORD, is_staff=True, email_verified=True, email_verified_at=timezone.now())
    user.groups.add(Group.objects.get_or_create(name=ROLE_GROUPS['author_editor'])[0])
    return user


@override_settings(STAFF_OTP_REQUIRED=False)
class PasswordOnlyStaffTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_staff()

    def test_site_sign_in_also_opens_the_studio_and_the_admin(self):
        client = Client()
        self.assertEqual(client.get('/studio/').status_code, 302)
        response = client.post('/sign-in/', {'email': self.user.email, 'password': PASSWORD})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get('/studio/').status_code, 200)
        self.assertEqual(client.get('/admin/').status_code, 200)

    def test_admin_login_has_no_code_field_and_works_with_a_password(self):
        client = Client()
        page = client.get('/admin/login/')
        self.assertNotContains(page, 'otp_token')
        response = client.post('/admin/login/', {'username': self.user.email, 'password': PASSWORD, 'next': '/studio/'})
        self.assertEqual(response.status_code, 302, response.content[:600])
        self.assertEqual(client.get('/studio/').status_code, 200)

    def test_a_wrong_password_still_fails(self):
        client = Client()
        client.post('/admin/login/', {'username': self.user.email, 'password': 'wrong-password-1', 'next': '/studio/'})
        self.assertEqual(client.get('/studio/').status_code, 302)

    def test_learners_are_still_kept_out(self):
        learner = User.objects.create_user('learner@example.com', PASSWORD, email_verified=True, email_verified_at=timezone.now())
        client = Client()
        client.force_login(learner)
        self.assertEqual(client.get('/studio/').status_code, 404)
        self.assertNotEqual(client.get('/admin/').status_code, 200)

    def test_the_sign_in_lasts_about_a_year(self):
        self.assertGreaterEqual(settings.SESSION_COOKIE_AGE, 60 * 60 * 24 * 360)
        self.assertFalse(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        client = Client()
        response = client.post('/sign-in/', {'email': self.user.email, 'password': PASSWORD})
        self.assertGreaterEqual(int(response.cookies['sessionid']['max-age']), 60 * 60 * 24 * 360)


@override_settings(STAFF_OTP_REQUIRED=True)
class OTPStillAvailableTests(TestCase):
    def test_switching_it_back_on_requires_the_code_again(self):
        user = make_staff('otp@example.com')
        client = Client()
        client.force_login(user)
        self.assertEqual(client.get('/studio/').status_code, 302)
        self.assertContains(Client().get('/admin/login/'), 'otp_token')
