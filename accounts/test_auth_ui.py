from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class AuthenticationBoundaryTests(TestCase):
    def make_user(self, email='reader@example.com', verified=True, status='active'):
        user = User.objects.create_user(email, 'Valid-password-493!')
        user.account_status = status
        user.email_verified = verified
        user.email_verified_at = timezone.now() if verified else None
        user.save()
        return user

    def test_anonymous_can_read_public_routes(self):
        for route in ('home', 'playbook-list', 'module-list'):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        # Missing slugs stay ordinary public not-found responses.
        self.assertEqual(self.client.get(reverse('playbook-detail', args=['missing'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('module-detail', args=['missing'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('lesson-detail', args=['missing'])).status_code, 404)

    def test_valid_login_establishes_session_and_shell_shows_email(self):
        user = self.make_user()
        response = self.client.post(reverse('sign-in'), {
            'email': ' READER@example.com ', 'password': 'Valid-password-493!',
        })
        self.assertRedirects(response, '/')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        home = self.client.get('/')
        self.assertContains(home, 'reader@example.com')
        self.assertContains(home, 'Sign out')

    def test_unknown_wrong_password_and_unverified_accounts_have_safe_error(self):
        self.make_user(verified=False)
        for data in (
            {'email': 'missing@example.com', 'password': 'Valid-password-493!'},
            {'email': 'reader@example.com', 'password': 'wrong-password'},
            {'email': 'reader@example.com', 'password': 'Valid-password-493!'},
        ):
            with self.subTest(email=data['email'], password=data['password']):
                response = self.client.post(reverse('sign-in'), data)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'We could not sign you in with those details.')
                self.assertNotIn('Valid-password-493!', response.content.decode())
                self.assertNotIn('missing@example.com', response.content.decode())
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_disabled_account_cannot_sign_in(self):
        self.make_user(status='disabled')
        response = self.client.post(reverse('sign-in'), {
            'email': 'reader@example.com', 'password': 'Valid-password-493!',
        })
        self.assertContains(response, 'We could not sign you in with those details.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_required_credentials_are_reported_without_authenticating(self):
        response = self.client.post(reverse('sign-in'), {})
        self.assertContains(response, 'This field is required.', status_code=200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_redirect_is_limited_to_same_site(self):
        user = self.make_user()
        for next_value, expected in (('https://attacker.example/path', '/'), ('/playbooks/', '/playbooks/')):
            response = self.client.post(f"{reverse('sign-in')}?next={next_value}", {
                'email': user.email, 'password': 'Valid-password-493!', 'next': next_value,
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response['Location'], expected)
            self.client.logout()

    def test_logout_requires_post_and_ends_session(self):
        self.make_user()
        self.client.login(email='reader@example.com', password='Valid-password-493!')
        self.assertEqual(self.client.get(reverse('sign-out')).status_code, 405)
        response = self.client.post(reverse('sign-out'), {'next': 'https://attacker.example/'})
        self.assertRedirects(response, '/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_csrf_is_required_for_credential_submission_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        self.make_user()
        self.assertEqual(client.post(reverse('sign-in'), {
            'email': 'reader@example.com', 'password': 'Valid-password-493!',
        }).status_code, 403)
        client.get(reverse('sign-in'))
        token = client.cookies['csrftoken'].value
        response = client.post(reverse('sign-in'), {
            'email': 'reader@example.com', 'password': 'Valid-password-493!', 'csrfmiddlewaretoken': token,
        }, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.post(reverse('sign-out')).status_code, 403)
        rotated_token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(reverse('sign-out'), HTTP_X_CSRFTOKEN=rotated_token).status_code, 302)


class SignInPromptTests(TestCase):
    def test_shared_shell_offers_sign_in_for_anonymous_users(self):
        response = self.client.get('/')
        self.assertContains(response, reverse('sign-in'))

    def test_sign_in_form_never_prefills_password(self):
        response = self.client.get(reverse('sign-in'))
        self.assertContains(response, 'autocomplete="email"')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertNotContains(response, 'name="password" value=')
