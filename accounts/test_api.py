"""Patch 17: the app's account API."""
import json
import re

from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.models import ApiToken, UserAccount

STRONG = 'a-strong-pass-9137'


def post(client, path, data, **extra):
    return client.post(path, json.dumps(data), content_type='application/json', **extra)


@override_settings(SECURE_SSL_REDIRECT=False)
class AccountApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def ask(self, email='new@example.com', purpose='register'):
        response = post(self.client, '/api/v1/account/code/', {'email': email, 'purpose': purpose})
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)['ticket']

    def last_code(self):
        return re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)

    def register(self, email='new@example.com'):
        ticket = self.ask(email)
        return post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': self.last_code(), 'password': STRONG, 'device': 'Pixel'})

    def test_register_creates_a_verified_account_and_a_working_token(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        user = UserAccount.objects.get(email='new@example.com')
        self.assertTrue(user.email_verified)
        me = self.client.get('/api/v1/account/me/', HTTP_AUTHORIZATION='Bearer ' + data['token'])
        self.assertEqual(json.loads(me.content)['user']['email'], 'new@example.com')

    def test_wrong_code_five_times_locks_the_request(self):
        ticket = self.ask()
        for _ in range(5):
            self.assertEqual(post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': '000000', 'password': STRONG}).status_code, 400)
        right = post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': self.last_code(), 'password': STRONG})
        self.assertEqual(right.status_code, 429)
        self.assertFalse(UserAccount.objects.filter(email='new@example.com').exists())

    def test_a_newer_code_replaces_the_older_one(self):
        old = self.ask()
        old_code = self.last_code()
        self.ask()
        response = post(self.client, '/api/v1/account/verify/', {'ticket': old, 'code': old_code, 'password': STRONG})
        self.assertEqual(json.loads(response.content)['error'], 'expired')

    def test_weak_password_is_refused_and_creates_nothing(self):
        ticket = self.ask()
        response = post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': self.last_code(), 'password': '12345678'})
        self.assertEqual(json.loads(response.content)['error'], 'weak_password')
        self.assertFalse(UserAccount.objects.filter(email='new@example.com').exists())

    def test_asking_for_an_existing_email_looks_the_same_and_sends_no_code(self):
        UserAccount.objects.create_user('here@example.com', STRONG, email_verified=True, email_verified_at=timezone.now())
        ticket = self.ask('here@example.com')
        self.assertTrue(ticket)
        self.assertNotRegex(mail.outbox[-1].body, r'\b\d{6}\b')
        response = post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': '123456', 'password': STRONG})
        self.assertEqual(response.status_code, 400)

    def test_sign_in_sign_out_and_bad_password(self):
        UserAccount.objects.create_user('here@example.com', STRONG, email_verified=True, email_verified_at=timezone.now())
        bad = post(self.client, '/api/v1/account/signin/', {'email': 'here@example.com', 'password': 'nope'})
        self.assertEqual(bad.status_code, 401)
        good = post(self.client, '/api/v1/account/signin/', {'email': 'HERE@example.com', 'password': STRONG})
        self.assertEqual(good.status_code, 200)
        token = json.loads(good.content)['token']
        auth = {'HTTP_AUTHORIZATION': 'Bearer ' + token}
        self.assertEqual(self.client.get('/api/v1/account/me/', **auth).status_code, 200)
        self.client.post('/api/v1/account/signout/', **auth)
        self.assertEqual(self.client.get('/api/v1/account/me/', **auth).status_code, 401)
        self.assertEqual(ApiToken.objects.count(), 0)

    def test_unverified_or_disabled_accounts_cannot_sign_in(self):
        UserAccount.objects.create_user('raw@example.com', STRONG)
        UserAccount.objects.create_user('off@example.com', STRONG, email_verified=True, email_verified_at=timezone.now(), account_status='disabled')
        for email in ('raw@example.com', 'off@example.com'):
            self.assertEqual(post(self.client, '/api/v1/account/signin/', {'email': email, 'password': STRONG}).status_code, 401)

    def test_five_bad_sign_ins_block_even_the_right_password(self):
        UserAccount.objects.create_user('here@example.com', STRONG, email_verified=True, email_verified_at=timezone.now())
        for _ in range(5):
            post(self.client, '/api/v1/account/signin/', {'email': 'here@example.com', 'password': 'x'})
        self.assertEqual(post(self.client, '/api/v1/account/signin/', {'email': 'here@example.com', 'password': STRONG}).status_code, 429)

    def test_password_reset_changes_the_password(self):
        UserAccount.objects.create_user('here@example.com', STRONG, email_verified=True, email_verified_at=timezone.now())
        ticket = self.ask('here@example.com', 'reset')
        response = post(self.client, '/api/v1/account/verify/', {'ticket': ticket, 'code': self.last_code(), 'password': 'another-strong-pass-5521'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post(self.client, '/api/v1/account/signin/', {'email': 'here@example.com', 'password': 'another-strong-pass-5521'}).status_code, 200)
        self.assertEqual(post(self.client, '/api/v1/account/signin/', {'email': 'here@example.com', 'password': STRONG}).status_code, 401)

    def test_junk_requests_are_handled(self):
        self.assertEqual(self.client.post('/api/v1/account/code/', 'not json', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get('/api/v1/account/code/').status_code, 405)
        self.assertEqual(self.client.get('/api/v1/account/me/', HTTP_AUTHORIZATION='Bearer short').status_code, 401)
        self.assertEqual(post(self.client, '/api/v1/account/code/', {'email': 'nope'}).status_code, 400)
