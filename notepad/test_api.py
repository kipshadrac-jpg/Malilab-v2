"""Patch 19: the Plan Notepad API (notes, history, export, calculator)."""
import json
import uuid

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from accounts.api import issue_token
from accounts.models import UserAccount
from notepad.models import PlanNote, PlanNoteVersion


def verified(email):
    return UserAccount.objects.create_user(email, 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


@override_settings(SECURE_SSL_REDIRECT=False)
class NotepadApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = verified('a@example.com')
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.user)}
        self.other = verified('b@example.com')
        self.other_auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.other)}

    def call(self, method, path, data=None, auth=None):
        kwargs = dict(auth if auth is not None else self.auth)
        if data is not None:
            kwargs.update(data=json.dumps(data), content_type='application/json')
        return getattr(self.client, method)(path, **kwargs)

    def make(self, title='My plan', **extra):
        body = {'uid': str(uuid.uuid4()), 'title': title, 'blocks': [{'type': 'paragraph', 'text': 'Save **daily**.'}]}
        body.update(extra)
        response = self.call('post', '/api/v1/notes/', body)
        self.assertEqual(response.status_code, 201, response.content)
        return json.loads(response.content)

    def test_everything_needs_a_sign_in(self):
        for method, path in (('get', '/api/v1/notes/'), ('post', '/api/v1/notes/'), ('get', '/api/v1/notes/%s/' % uuid.uuid4()),
                             ('post', '/api/v1/calc/compound/'), ('post', '/api/v1/calc/compare/')):
            self.assertEqual(getattr(self.client, method)(path).status_code, 401, path)

    def test_create_list_read(self):
        note = self.make(collection='Financial goals', tags=['kids', 'Kids', 'school'])
        self.assertEqual(note['version'], 1)
        self.assertEqual(note['tags'], ['kids', 'school'])
        self.assertTrue(note['blocks'][0]['id'])
        rows = json.loads(self.call('get', '/api/v1/notes/').content)['notes']
        self.assertEqual([r['uid'] for r in rows], [note['uid']])
        self.assertIn('Save daily', rows[0]['snippet'])
        full = json.loads(self.call('get', '/api/v1/notes/%s/' % note['uid']).content)
        self.assertEqual(full['blocks'][0]['text'], 'Save **daily**.')

    def test_creating_twice_is_harmless_and_does_not_leak(self):
        note = self.make()
        again = self.call('post', '/api/v1/notes/', {'uid': note['uid'], 'title': 'x', 'blocks': []})
        self.assertEqual(again.status_code, 200)
        self.assertEqual(json.loads(again.content)['title'], 'My plan')
        stolen = self.call('post', '/api/v1/notes/', {'uid': note['uid'], 'title': 'x', 'blocks': []}, auth=self.other_auth)
        self.assertEqual(stolen.status_code, 409)
        self.assertNotIn('My plan', stolen.content.decode())

    def test_notes_are_private(self):
        note = self.make()
        path = '/api/v1/notes/%s/' % note['uid']
        self.assertEqual(self.call('get', path, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('put', path, {'base_version': 1, 'title': 'mine now'}, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('delete', path, auth=self.other_auth).status_code, 404)
        self.assertEqual(self.call('get', path + 'export/', auth=self.other_auth).status_code, 404)
        self.assertEqual(json.loads(self.call('get', '/api/v1/notes/', auth=self.other_auth).content)['notes'], [])

    def test_update_bumps_the_version_and_rejects_stale_edits(self):
        note = self.make()
        path = '/api/v1/notes/%s/' % note['uid']
        first = json.loads(self.call('put', path, {'base_version': 1, 'title': 'Renamed'}).content)
        self.assertEqual(first['version'], 2)
        stale = self.call('put', path, {'base_version': 1, 'title': 'Old phone'})
        self.assertEqual(stale.status_code, 409)
        body = json.loads(stale.content)
        self.assertEqual(body['error'], 'conflict')
        self.assertEqual(body['note']['title'], 'Renamed')
        self.assertEqual(self.call('put', path, {'title': 'no base'}).status_code, 400)

    def test_partial_update_keeps_other_fields(self):
        note = self.make(collection='Budget & cash flow')
        path = '/api/v1/notes/%s/' % note['uid']
        self.call('put', path, {'base_version': 1, 'favourite': True})
        full = json.loads(self.call('get', path).content)
        self.assertTrue(full['favourite'])
        self.assertEqual(full['collection'], 'Budget & cash flow')
        self.assertEqual(len(full['blocks']), 1)

    def test_bad_blocks_are_refused_with_the_field(self):
        response = self.call('post', '/api/v1/notes/', {'uid': str(uuid.uuid4()), 'title': 't', 'blocks': [{'type': 'script', 'text': '<script>'}]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['fields'][0]['field'], 'blocks[0].type')
        self.assertEqual(self.call('post', '/api/v1/notes/', {'uid': 'not-a-uuid', 'blocks': []}).status_code, 400)

    def test_search_filters_and_favourites(self):
        a = self.make('Treasury bills idea', blocks=[{'type': 'paragraph', 'text': 'ninety one day paper'}], collection='Investment research')
        self.make('Budget')
        found = json.loads(self.call('get', '/api/v1/notes/?q=ninety').content)['notes']
        self.assertEqual([r['uid'] for r in found], [a['uid']])
        self.assertEqual(len(json.loads(self.call('get', '/api/v1/notes/?collection=Investment%20research').content)['notes']), 1)
        self.assertEqual(json.loads(self.call('get', '/api/v1/notes/?favourite=1').content)['notes'], [])

    def test_delete_hides_the_note(self):
        note = self.make()
        path = '/api/v1/notes/%s/' % note['uid']
        self.assertEqual(self.call('delete', path).status_code, 200)
        self.assertEqual(self.call('get', path).status_code, 404)
        self.assertEqual(json.loads(self.call('get', '/api/v1/notes/').content)['notes'], [])

    def test_duplicate_leaves_the_original_alone(self):
        note = self.make('Original')
        copy = json.loads(self.call('post', '/api/v1/notes/%s/duplicate/' % note['uid']).content)
        self.assertEqual(copy['title'], 'Copy of Original')
        self.assertNotEqual(copy['uid'], note['uid'])
        self.assertEqual(copy['blocks'], note['blocks'])

    def test_history_and_restore(self):
        note = self.make('Draft one')
        path = '/api/v1/notes/%s/' % note['uid']
        self.call('put', path, {'base_version': 1, 'title': 'Draft two', 'blocks': [{'type': 'paragraph', 'text': 'later words'}]})
        versions = json.loads(self.call('get', path + 'versions/').content)['versions']
        self.assertEqual(len(versions), 1)            # edits within ten minutes share one saved version
        PlanNoteVersion.objects.filter(note__uid=note['uid']).update(created_at=timezone.now() - timezone.timedelta(minutes=30))
        self.call('put', path, {'base_version': 2, 'title': 'Draft three'})
        versions = json.loads(self.call('get', path + 'versions/').content)['versions']
        self.assertEqual(len(versions), 2)
        oldest = versions[-1]['number']
        restored = json.loads(self.call('post', path + 'versions/%d/restore/' % oldest).content)
        self.assertEqual(restored['title'], 'Draft one')
        self.assertEqual(restored['version'], 4)
        labels = [v['label'] for v in json.loads(self.call('get', path + 'versions/').content)['versions']]
        self.assertIn('Before restore', labels)
        self.assertEqual(self.call('post', path + 'versions/999/restore/').status_code, 404)

    def test_markdown_export_keeps_the_evidence(self):
        block = {'type': 'chart', 'title': 'Balance over time', 'x_label': 'Year', 'y_label': 'Balance', 'unit': 'KES', 'x': ['1', '2'],
                 'series': [{'key': 'b', 'name': 'Balance', 'values': ['100.00', '210.00']}], 'mode': 'snapshot',
                 'captured_at': '2026-10-19T10:00:00', 'calc': {'model': 'compound-projection', 'version': '1.0.0'}}
        note = self.make('Can I retire at 45?', blocks=[{'type': 'heading', 'text': 'Question', 'level': 2}, block])
        response = self.call('get', '/api/v1/notes/%s/export/' % note['uid'])
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        text = response.content.decode()
        self.assertIn('# Can I retire at 45?', text)
        self.assertIn('| 2 | 210.00 |', text)
        self.assertIn('Snapshot captured 2026-10-19T10:00:00; model compound-projection 1.0.0', text)

    def test_note_for_a_lesson_is_created_once(self):
        first = self.call('post', '/api/v1/notes/for-context/', {'kind': 'lesson', 'slug': 'les', 'title': 'Sacco basics'})
        self.assertEqual(first.status_code, 201)
        second = self.call('post', '/api/v1/notes/for-context/', {'kind': 'lesson', 'slug': 'les', 'title': 'Sacco basics'})
        self.assertEqual(second.status_code, 200)
        self.assertEqual(json.loads(first.content)['uid'], json.loads(second.content)['uid'])
        self.assertEqual(json.loads(first.content)['title'], 'Notes: Sacco basics')
        self.assertEqual(self.call('post', '/api/v1/notes/for-context/', {'kind': 'nope', 'slug': 'x'}).status_code, 400)
        mine = json.loads(self.call('get', '/api/v1/notes/?context=lesson:les').content)['notes']
        self.assertEqual(len(mine), 1)

    def test_calculator_projection_solve_and_compare(self):
        inputs = {'years': 10, 'annual_return': 12, 'contribution': 5000}
        data = json.loads(self.call('post', '/api/v1/calc/compound/', {'inputs': inputs}).content)
        self.assertEqual(data['result']['model'], 'compound-projection')
        self.assertIn('calculated_at', data['result'])
        solved = json.loads(self.call('post', '/api/v1/calc/compound/', {'inputs': {'years': 10, 'annual_return': 12, 'target': 1000000}, 'solve': {'kind': 'contribution_for_target'}}).content)
        self.assertIn('solution', solved)
        bad = self.call('post', '/api/v1/calc/compound/', {'inputs': {'years': 0}})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(json.loads(bad.content)['fields'][0]['field'], 'years')
        compared = json.loads(self.call('post', '/api/v1/calc/compare/', {'inputs': inputs, 'scenarios': [{'name': 'Lower', 'overrides': {'annual_return': 6}}]}).content)
        self.assertEqual(len(compared['scenarios']), 2)
        self.assertEqual(self.call('post', '/api/v1/calc/compare/', {'inputs': inputs, 'scenarios': []}).status_code, 400)

    def test_calculator_is_rate_limited(self):
        for _ in range(60):
            self.call('post', '/api/v1/calc/compound/', {'inputs': {'years': 1}})
        self.assertEqual(self.call('post', '/api/v1/calc/compound/', {'inputs': {'years': 1}}).status_code, 429)
