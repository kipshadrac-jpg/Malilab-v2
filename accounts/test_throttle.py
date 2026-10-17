from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

User = get_user_model()


class SignInThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user('t1@example.com', 'right-Password-123', email_verified=True, email_verified_at=timezone.now())
        User.objects.create_user('t2@example.com', 'right-Password-123', email_verified=True, email_verified_at=timezone.now())

    def attempt(self, email='t1@example.com', password='wrong', client=None):
        return (client or self.client).post('/sign-in/', {'email': email, 'password': password, 'next': '/'})

    def test_five_failures_block_even_the_correct_password(self):
        for _ in range(5):
            self.assertEqual(self.attempt().status_code, 200)
        blocked = self.attempt(password='right-Password-123')
        self.assertEqual(blocked.status_code, 429)
        self.assertContains(blocked, 'Too many sign-in attempts', status_code=429)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_other_accounts_are_unaffected(self):
        for _ in range(5):
            self.attempt()
        ok = self.attempt(email='t2@example.com', password='right-Password-123', client=Client())
        self.assertEqual(ok.status_code, 302)

    def test_success_resets_the_counter(self):
        for _ in range(4):
            self.attempt()
        self.assertEqual(self.attempt(password='right-Password-123').status_code, 302)
        self.client.post('/sign-out/')
        for _ in range(4):
            self.assertEqual(self.attempt().status_code, 200)

    def test_unknown_email_is_counted_the_same_way(self):
        for _ in range(5):
            self.attempt(email='nobody@example.com')
        self.assertEqual(self.attempt(email='nobody@example.com').status_code, 429)
