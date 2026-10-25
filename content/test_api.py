"""Patch 15: the read-only JSON the Android app uses."""
import json

from django.test import Client, TestCase, override_settings

from config.test_6b11 import SiteFixtureMixin, publish
from content.models import (Module, ModuleRevision, Playbook, PlaybookModuleRecommendation, PlaybookRevision)


@override_settings(SECURE_SSL_REDIRECT=False)
class PlaybookApiTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()
        self.client = Client()
        identity = Playbook.objects.create(slug='boda-saving')
        self.rich = PlaybookRevision.objects.create(
            playbook=identity, revision_number=1, title='Save from age 20', summary='A plan.', scenario='You ride daily.',
            assumptions=['A notebook', '  '],
            discovery_metadata={'guide': {'steps': [{'title': 'Write it down', 'text': 'Do **this**.\n\n- a\n- b'},
                                                    {'title': 'Bonus', 'text': 'Extra', 'optional': True},
                                                    {'title': '', 'text': 'ignored'}],
                                          'outcome': 'You now have a plan.'}})
        PlaybookModuleRecommendation.objects.create(playbook_revision=self.rich, module_revision=self.module_rev,
                                                    position=1, rationale='Go deeper.')
        publish(self.rich, identity)

    def test_list_has_only_published_playbooks_with_the_card_fields(self):
        Playbook.objects.create(slug='draft-only')      # an identity with no published revision never appears
        response = self.client.get('/api/v1/playbooks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        rows = {r['slug']: r for r in json.loads(response.content)['playbooks']}
        self.assertEqual(set(rows), {'pb', 'boda-saving'})
        card = rows['boda-saving']
        self.assertEqual((card['title'], card['summary'], card['goal'], card['step_count']),
                         ('Save from age 20', 'A plan.', 'You ride daily.', 2))
        self.assertIsNone(card['cover_url'])
        self.assertEqual(rows['pb']['step_count'], 0)

    def test_detail_has_needs_steps_outcome_and_modules(self):
        data = json.loads(self.client.get('/api/v1/playbooks/boda-saving/').content)
        self.assertEqual(data['needs'], ['A notebook'])
        self.assertEqual([s['title'] for s in data['steps']], ['Write it down', 'Bonus'])
        self.assertEqual([s['n'] for s in data['steps']], [1, 2])
        self.assertTrue(data['steps'][1]['optional'])
        self.assertIn('**this**', data['steps'][0]['text'])
        self.assertEqual(data['outcome'], 'You now have a plan.')
        self.assertEqual(data['modules'], [{'slug': 'mod', 'title': 'Saving module', 'rationale': 'Go deeper.'}])

    def test_old_playbooks_without_steps_still_work(self):
        data = json.loads(self.client.get('/api/v1/playbooks/pb/').content)
        self.assertEqual((data['steps'], data['needs'], data['outcome']), ([], [], ''))
        self.assertEqual(data['goal'], 'Sc')

    def test_unknown_and_unpublished_are_not_found_as_json(self):
        Playbook.objects.create(slug='nothing-yet')
        for slug in ('missing', 'nothing-yet'):
            response = self.client.get(f'/api/v1/playbooks/{slug}/')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.content), {'error': 'not_found'})

    def test_read_only(self):
        self.assertEqual(self.client.post('/api/v1/playbooks/', {}).status_code, 405)
        self.assertEqual(self.client.delete('/api/v1/playbooks/pb/').status_code, 405)
