import json

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from content.models import ModuleLearningRequirement, PracticeActivity
from practice.models import PracticeAttempt
from learning.models import RequirementEvidence

BUDGET = '/api/v1/practice/sample-monthly-budget/'
FULL = {'income': '60000.00', 'rent': '20000', 'dependants': 3, 'biggest': 'food', 'plan': 'Track every shilling'}


def verified(email):
    return UserAccount.objects.create_user(email, 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


@override_settings(SECURE_SSL_REDIRECT=False)
class PracticeApiTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command('seed_practice_samples', verbosity=0)
        self.client = Client()
        self.user = verified('p1@example.com')
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.user)}
        self.other = verified('p2@example.com')
        self.other_auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.other)}

    def call(self, method, path, data=None, auth=None):
        kwargs = dict(self.auth if auth is None else auth)
        if data is not None:
            kwargs.update(data=json.dumps(data), content_type='application/json')
        return getattr(self.client, method)(path, **kwargs)

    def begin(self, path=BUDGET, auth=None):
        response = self.call('post', path + 'attempts/', auth=auth)
        self.assertIn(response.status_code, (200, 201), response.content)
        return response.json()

    def fill(self, attempt_id, answers=FULL):
        for key, value in answers.items():
            r = self.call('put', '/api/v1/practice/attempts/%d/answers/%s/' % (attempt_id, key), {'value': value})
            self.assertEqual(r.status_code, 200, r.content)

    def test_requires_sign_in(self):
        self.assertEqual(self.client.get(BUDGET).status_code, 401)
        self.assertEqual(self.client.post(BUDGET + 'attempts/').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/practice/').status_code, 401)

    def test_detail_shows_activity_and_no_attempt_yet(self):
        data = self.call('get', BUDGET).json()
        self.assertEqual(data['slug'], 'sample-monthly-budget')
        self.assertEqual(len(data['questions']), 6)
        self.assertIsNone(data['open_attempt_id'])
        self.assertEqual(data['tool_refs'][0]['model'], 'compound')

    def test_unpublished_or_unknown_is_not_found(self):
        self.assertEqual(self.call('get', '/api/v1/practice/nope/').status_code, 404)
        PracticeActivity.objects.create(slug='draft-one')
        self.assertEqual(self.call('get', '/api/v1/practice/draft-one/').status_code, 404)

    def test_start_resumes_the_open_attempt(self):
        first = self.begin()
        second = self.begin()
        self.assertEqual(first['id'], second['id'])
        self.assertEqual(PracticeAttempt.objects.filter(owner=self.user).count(), 1)

    def test_autosave_then_reload_keeps_answers(self):
        attempt = self.begin()
        self.fill(attempt['id'], {'income': '60000.5', 'habits': ['track', 'save']})
        got = self.call('get', '/api/v1/practice/attempts/%d/' % attempt['id']).json()
        self.assertEqual(got['answers']['income'], '60000.5')
        self.assertEqual(got['answers']['habits'], ['track', 'save'])

    def test_bad_answers_are_rejected_with_the_question(self):
        attempt = self.begin()
        base = '/api/v1/practice/attempts/%d/answers/' % attempt['id']
        self.assertEqual(self.call('put', base + 'income/', {'value': '12.345'}).status_code, 400)
        self.assertEqual(self.call('put', base + 'dependants/', {'value': 99}).status_code, 400)
        self.assertEqual(self.call('put', base + 'biggest/', {'value': 'nonsense'}).status_code, 400)
        self.assertEqual(self.call('put', base + 'plan/', {'value': 'x' * 141}).status_code, 400)
        self.assertEqual(self.call('put', base + 'ghost/', {'value': 'x'}).status_code, 400)
        self.assertEqual(self.call('put', base + 'plan/', {}).status_code, 400)

    def test_clear_an_answer(self):
        attempt = self.begin()
        self.fill(attempt['id'], {'plan': 'Save'})
        r = self.call('delete', '/api/v1/practice/attempts/%d/answers/plan/' % attempt['id'])
        self.assertEqual(r.status_code, 200)
        got = self.call('get', '/api/v1/practice/attempts/%d/' % attempt['id']).json()
        self.assertNotIn('plan', got['answers'])

    def test_submit_needs_every_required_answer(self):
        attempt = self.begin()
        self.fill(attempt['id'], {'income': '1000'})
        r = self.call('post', '/api/v1/practice/attempts/%d/submit/' % attempt['id'], {})
        self.assertEqual(r.status_code, 400)
        self.assertIn('fields', r.json())
        self.assertEqual(PracticeAttempt.objects.get(pk=attempt['id']).state, 'started')

    def test_submit_with_full_answer_set_and_progress(self):
        attempt = self.begin()
        r = self.call('post', '/api/v1/practice/attempts/%d/submit/' % attempt['id'], {'responses': FULL})
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body['attempt']['state'], 'submitted')
        self.assertIn('sample-monthly-budget', body['progress']['practice'])
        module = [m for m in body['progress']['modules'] if m['slug'] == 'sample-practice-module'][0]
        self.assertEqual((module['practice_done'], module['practice_total']), (1, 2))
        self.assertTrue(module['complete'])          # the optional one does not block
        self.assertEqual(RequirementEvidence.objects.filter(owner=self.user, state='accepted').count(), 1)

    def test_submitted_attempt_is_locked(self):
        attempt = self.begin()
        self.call('post', '/api/v1/practice/attempts/%d/submit/' % attempt['id'], {'responses': FULL})
        r = self.call('put', '/api/v1/practice/attempts/%d/answers/plan/' % attempt['id'], {'value': 'changed'})
        self.assertEqual(r.status_code, 400)
        again = self.call('post', '/api/v1/practice/attempts/%d/submit/' % attempt['id'], {'responses': FULL})
        self.assertEqual(again.status_code, 400)

    def test_retake_starts_a_new_attempt(self):
        first = self.begin()
        self.call('post', '/api/v1/practice/attempts/%d/submit/' % first['id'], {'responses': FULL})
        second = self.begin()
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(second['answers'], {})
        self.assertEqual(self.call('post', '/api/v1/practice/attempts/%d/submit/' % second['id'], {'responses': FULL}).status_code, 200)
        detail = self.call('get', BUDGET).json()
        self.assertEqual(detail['submitted_count'], 2)

    def test_attempts_are_private(self):
        attempt = self.begin()
        base = '/api/v1/practice/attempts/%d/' % attempt['id']
        self.assertEqual(self.call('get', base, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('put', base + 'answers/plan/', {'value': 'x'}, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('post', base + 'submit/', {}, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('get', '/api/v1/practice/', auth=self.other_auth).json()['attempts'], [])

    def test_unverified_account_cannot_start(self):
        user = UserAccount.objects.create_user('nv@example.com', 'strong-password-123')
        auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(user)}
        self.assertEqual(self.call('post', BUDGET + 'attempts/', auth=auth).status_code, 401)

    def test_history_lists_attempts_newest_first(self):
        a = self.begin()
        self.call('post', '/api/v1/practice/attempts/%d/submit/' % a['id'], {'responses': FULL})
        b = self.begin('/api/v1/practice/sample-emergency-fund/')
        rows = self.call('get', '/api/v1/practice/').json()['attempts']
        self.assertEqual([r['id'] for r in rows], [b['id'], a['id']])
        self.assertEqual(rows[1]['state'], 'submitted')

    def test_old_revision_attempt_stays_pinned(self):
        from content.models import PracticeActivityRevision
        from learning.management.commands.seed_practice_samples import BUDGET as SCHEMA, publish
        attempt = self.begin()
        activity = PracticeActivity.objects.get(slug='sample-monthly-budget')
        newer = PracticeActivityRevision.objects.create(activity=activity, revision_number=2, title='[Sample] v2', response_schema=SCHEMA)
        publish(newer, activity)
        got = self.call('get', '/api/v1/practice/attempts/%d/' % attempt['id']).json()
        self.assertEqual(got['title'], '[Sample] Your monthly budget')
        fresh = self.begin()
        self.assertNotEqual(fresh['id'], attempt['id'])
        self.assertEqual(fresh['title'], '[Sample] v2')


@override_settings(SECURE_SSL_REDIRECT=False)
class ModuleApiPracticeTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command('seed_practice_samples', verbosity=0)

    def test_seed_is_idempotent(self):
        call_command('seed_practice_samples', verbosity=0)
        self.assertEqual(PracticeActivity.objects.count(), 2)

    def test_module_detail_lists_practice(self):
        data = Client().get('/api/v1/modules/sample-practice-module/').json()
        self.assertEqual([p['slug'] for p in data['practice']], ['sample-monthly-budget', 'sample-emergency-fund'])
        self.assertEqual([p['classification'] for p in data['practice']], ['required', 'optional'])

    def test_progress_for_a_fresh_learner(self):
        user = verified('fresh@example.com')
        data = Client().get('/api/v1/progress/', HTTP_AUTHORIZATION='Bearer ' + issue_token(user)).json()
        self.assertEqual(data['practice'], [])
        module = [m for m in data['modules'] if m['slug'] == 'sample-practice-module'][0]
        self.assertEqual((module['practice_done'], module['practice_total'], module['complete']), (0, 2, False))
