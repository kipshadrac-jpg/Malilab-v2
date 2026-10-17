import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone

from accounts import registration
from config.test_6b11 import audit

User = get_user_model()
STRONG = 'Sturdy-Garden-Walk-7421'
NEWER = 'Another-Quiet-River-5530'
OLD = 'Old-Password-4821'


def make_user(email='learner@example.com', password=OLD, verified=True, **extra):
    return User.objects.create_user(
        email, password, email_verified=verified,
        email_verified_at=timezone.now() if verified else None, **extra)


def code_in(message):
    found = re.search(r'^(\d{6})$', message.body, re.MULTILINE)
    assert found, message.body
    return found.group(1)


class Base(TestCase):
    def setUp(self):
        cache.clear()

    def register(self, email='new@example.com', client=None):
        return (client or self.client).post('/register/', {'email': email})

    def forgot(self, email, client=None):
        return (client or self.client).post('/forgot-password/', {'email': email})

    def enter(self, code, password=STRONG, client=None, confirm=None):
        return (client or self.client).post('/enter-code/', {
            'code': code, 'new_password1': password, 'new_password2': confirm or password})

    def sign_in(self, email, password):
        return Client().post('/sign-in/', {'email': email, 'password': password, 'next': '/'})


class SignUpTests(Base):
    def test_registering_emails_a_code_and_creates_nothing_yet(self):
        response = self.register()
        self.assertRedirects(response, '/enter-code/', fetch_redirect_response=False)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['new@example.com'])
        self.assertRegex(mail.outbox[0].body, r'(?m)^\d{6}$')
        self.assertNotIn('http', mail.outbox[0].body)

    def test_full_sign_up_then_sign_in(self):
        self.register()
        page = self.client.get('/enter-code/')
        self.assertContains(page, 'Enter your code')
        self.assertContains(page, 'new@example.com')
        done = self.enter(code_in(mail.outbox[0]))
        self.assertRedirects(done, '/check-email/?for=account-ready', fetch_redirect_response=False)
        user = User.objects.get(email='new@example.com')
        self.assertTrue(user.email_verified)
        self.assertIsNotNone(user.email_verified_at)
        self.assertTrue(user.can_use_personal_features)
        self.assertEqual(self.sign_in('new@example.com', STRONG).status_code, 302)

    def test_code_may_be_typed_with_spaces(self):
        self.register()
        code = code_in(mail.outbox[0])
        self.enter(f'{code[:3]} {code[3:]}')
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_address_is_normalised(self):
        self.register(' New@Example.COM ')
        self.assertEqual(mail.outbox[0].to, ['new@example.com'])
        self.enter(code_in(mail.outbox[0]))
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_existing_verified_address_gets_a_notice_not_a_code_and_the_same_response(self):
        make_user('taken@example.com')
        fresh = self.register('brand-new@example.com')
        other = Client()
        taken = self.register('taken@example.com', client=other)
        self.assertEqual((fresh.status_code, fresh['Location']), (taken.status_code, taken['Location']))
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('already', mail.outbox[1].body)
        self.assertNotRegex(mail.outbox[1].body, r'(?m)^\d{6}$')
        # Nothing the visitor can type will work, and the account is untouched.
        for guess in ('000000', '123456'):
            self.assertEqual(self.enter(guess, NEWER, client=other).status_code, 200)
        self.assertTrue(User.objects.get(email='taken@example.com').check_password(OLD))

    def test_old_unverified_account_is_completed_through_the_code(self):
        make_user('old@example.com', verified=False)
        self.register('old@example.com')
        self.enter(code_in(mail.outbox[0]), NEWER)
        user = User.objects.get(email='old@example.com')
        self.assertTrue(user.email_verified)
        self.assertTrue(user.check_password(NEWER))

    def test_wrong_code_is_refused_and_five_wrong_codes_lock_the_request(self):
        self.register()
        right = code_in(mail.outbox[0])
        wrong = '000000' if right != '000000' else '111111'
        for _ in range(4):
            response = self.enter(wrong)
            self.assertContains(response, 'not right or has expired')
        locked = self.enter(wrong)
        self.assertContains(locked, 'Too many wrong codes', status_code=400)
        self.assertEqual(self.enter(right).status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_does_not_use_up_the_code(self):
        self.register()
        code = code_in(mail.outbox[0])
        for _ in range(6):
            weak = self.enter(code, '12345678')
            self.assertEqual(weak.status_code, 200)
            self.assertContains(weak, 'form-errors')
        mismatch = self.enter(code, STRONG, confirm=NEWER)
        self.assertContains(mismatch, 'form-errors')
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(self.enter(code).status_code, 302)

    def test_code_only_works_in_the_browser_that_asked_for_it(self):
        self.register()
        code = code_in(mail.outbox[0])
        stranger = Client()
        self.assertEqual(self.enter(code, client=stranger).status_code, 400)
        self.assertEqual(stranger.get('/enter-code/').status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_code_expires(self):
        self.register()
        code = code_in(mail.outbox[0])
        with mock.patch.object(registration, 'CODE_MAX_AGE', -1):
            self.assertEqual(self.client.get('/enter-code/').status_code, 400)
            self.assertEqual(self.enter(code).status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_code_cannot_be_used_twice(self):
        self.register()
        code = code_in(mail.outbox[0])
        self.enter(code)
        again = self.enter(code, NEWER)
        self.assertEqual(again.status_code, 400)
        self.assertTrue(User.objects.get(email='new@example.com').check_password(STRONG))

    def test_asking_again_replaces_the_earlier_code(self):
        self.register()
        first = code_in(mail.outbox[0])
        self.register()
        second = code_in(mail.outbox[1])
        self.assertNotEqual(first, second)
        self.assertContains(self.enter(first), 'not right or has expired')
        self.assertEqual(self.enter(second).status_code, 302)

    def test_invalid_email_is_rejected_without_sending(self):
        response = self.register('not-an-email')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-errors')
        self.assertEqual(len(mail.outbox), 0)

    def test_disabled_account_gets_no_email_but_the_same_response(self):
        make_user('off@example.com', verified=False, account_status='disabled')
        response = self.register('off@example.com')
        self.assertRedirects(response, '/enter-code/', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.enter('123456', NEWER).status_code, 200)

    def test_a_failed_send_does_not_break_the_page(self):
        with mock.patch('accounts.emails.EmailMessage.send', side_effect=OSError('smtp down')):
            response = self.register()
        self.assertRedirects(response, '/enter-code/', fetch_redirect_response=False)

    def test_same_address_is_limited_to_three_requests_an_hour(self):
        for _ in range(3):
            self.assertEqual(self.register('spam@example.com').status_code, 302)
        self.assertContains(self.register('spam@example.com'), 'Too many requests', status_code=429)
        self.assertEqual(len(mail.outbox), 3)

    def test_one_visitor_is_limited_to_ten_requests_an_hour(self):
        for i in range(10):
            self.assertEqual(self.register(f'person{i}@example.com').status_code, 302)
        self.assertEqual(self.register('person10@example.com').status_code, 429)

    def test_real_address_comes_from_nginx_only_on_this_machine(self):
        for i in range(10):
            self.client.post('/register/', {'email': f'p{i}@example.com'}, HTTP_X_REAL_IP='203.0.113.5')
        other = self.client.post('/register/', {'email': 'q@example.com'}, HTTP_X_REAL_IP='203.0.113.99')
        self.assertEqual(other.status_code, 302)
        same = self.client.post('/register/', {'email': 'r@example.com'}, HTTP_X_REAL_IP='203.0.113.5')
        self.assertEqual(same.status_code, 429)

    def test_signed_in_learner_is_sent_home_from_register(self):
        client = Client()
        client.force_login(make_user())
        self.assertRedirects(client.get('/register/'), '/', fetch_redirect_response=False)

    def test_all_forms_require_a_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        for path, data in (('/register/', {'email': 'a@example.com'}), ('/forgot-password/', {'email': 'a@example.com'}),
                           ('/enter-code/', {'code': '123456', 'new_password1': STRONG, 'new_password2': STRONG})):
            self.assertEqual(strict.post(path, data).status_code, 403, path)
        self.assertEqual(len(mail.outbox), 0)


class PasswordResetTests(Base):
    def test_unknown_and_known_addresses_get_the_same_response(self):
        make_user('known@example.com')
        known = self.forgot('known@example.com')
        unknown = self.forgot('nobody@example.com', client=Client())
        self.assertEqual((known.status_code, known['Location']), (unknown.status_code, unknown['Location']))
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_with_the_code_changes_the_password_once(self):
        make_user('known@example.com')
        self.forgot('known@example.com')
        code = code_in(mail.outbox[0])
        weak = self.enter(code, '12345678')
        self.assertContains(weak, 'form-errors')
        done = self.enter(code)
        self.assertRedirects(done, '/check-email/?for=password-changed', fetch_redirect_response=False)
        self.assertEqual(self.sign_in('known@example.com', STRONG).status_code, 302)
        self.assertEqual(self.sign_in('known@example.com', OLD).status_code, 200)
        self.assertEqual(self.enter(code, NEWER).status_code, 400)

    def test_an_unknown_address_cannot_be_used_to_create_an_account_through_forgot_password(self):
        self.forgot('nobody@example.com')
        self.assertEqual(self.enter('123456').status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_reset_clears_a_sign_in_lockout(self):
        make_user('known@example.com')
        for _ in range(5):
            Client().post('/sign-in/', {'email': 'known@example.com', 'password': 'wrong'})
        self.assertEqual(self.sign_in('known@example.com', OLD).status_code, 429)
        self.forgot('known@example.com')
        self.enter(code_in(mail.outbox[0]))
        self.assertEqual(self.sign_in('known@example.com', STRONG).status_code, 302)

    def test_unverified_account_is_sent_a_setup_code_that_confirms_it(self):
        make_user('half@example.com', verified=False)
        self.forgot('half@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.enter(code_in(mail.outbox[0]), NEWER)
        user = User.objects.get(email='half@example.com')
        self.assertTrue(user.email_verified)
        self.assertTrue(user.check_password(NEWER))

    def test_disabled_account_gets_nothing(self):
        make_user('off@example.com', account_status='disabled')
        self.forgot('off@example.com')
        self.assertEqual(len(mail.outbox), 0)

    def test_a_reset_code_for_someone_else_is_useless_in_another_browser(self):
        make_user('known@example.com')
        self.forgot('known@example.com')
        code = code_in(mail.outbox[0])
        attacker = Client()
        self.forgot('known@example.com', client=attacker)   # attacker's own request: its code goes to the owner
        self.assertEqual(self.enter(code, NEWER, client=attacker).status_code, 200)
        self.assertTrue(User.objects.get(email='known@example.com').check_password(OLD))

    def test_forgot_password_is_rate_limited_and_allowed_when_signed_in(self):
        for _ in range(3):
            self.assertEqual(self.forgot('known@example.com').status_code, 302)
        self.assertEqual(self.forgot('known@example.com').status_code, 429)
        client = Client()
        client.force_login(make_user('signed@example.com'))
        self.assertEqual(client.get('/forgot-password/').status_code, 200)


class AccountPagesTests(Base):
    def test_pages_meet_basic_accessibility_rules(self):
        c = Client()
        c.post('/register/', {'email': 'a11y@example.com'})
        failures = []
        for path in ('/register/', '/forgot-password/', '/enter-code/', '/check-email/?for=account-ready',
                     '/check-email/?for=password-changed', '/sign-in/'):
            response = c.get(path)
            if response.status_code != 200:
                failures.append(f'{path}: HTTP {response.status_code}')
                continue
            failures += [f'{path}: {problem}' for problem in audit(response)]
        notice = Client().get('/enter-code/')
        failures += [f'no-request page: {problem}' for problem in audit(notice)]
        self.assertEqual(failures, [], '\n'.join(failures))

    def test_sign_in_and_header_offer_the_new_routes(self):
        page = Client().get('/sign-in/')
        self.assertContains(page, 'href="/register/"')
        self.assertContains(page, 'href="/forgot-password/"')
        self.assertContains(Client().get('/'), 'Create account')

    def test_account_pages_are_never_cached(self):
        for path in ('/register/', '/forgot-password/', '/enter-code/', '/check-email/?for=account-ready'):
            self.assertIn('no-store', Client().get(path)['Cache-Control'], path)

    def test_only_get_and_post_are_accepted(self):
        for path in ('/register/', '/forgot-password/', '/enter-code/'):
            self.assertEqual(Client().put(path).status_code, 405, path)
        self.assertEqual(Client().post('/check-email/?for=account-ready').status_code, 405)

    def test_unknown_finished_page_goes_home(self):
        self.assertRedirects(self.client.get('/check-email/?for=anything'), '/', fetch_redirect_response=False)
