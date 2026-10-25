"""Patch 16: read-only JSON for modules."""
import json

from django.test import Client, TestCase, override_settings

from config.test_6b11 import SiteFixtureMixin
from content.models import Module


@override_settings(SECURE_SSL_REDIRECT=False)
class ModuleApiTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()
        self.client = Client()

    def test_list_shows_published_modules_with_lesson_counts(self):
        Module.objects.create(slug='draft-module')
        response = self.client.get('/api/v1/modules/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['modules'],
                         [{'slug': 'mod', 'title': 'Saving module', 'description': 'D', 'lesson_count': 1}])

    def test_detail_lists_the_lessons_in_order(self):
        data = json.loads(self.client.get('/api/v1/modules/mod/').content)
        self.assertEqual(data['lessons'], [{'n': 1, 'slug': 'les', 'title': 'Sacco basics', 'summary': 'Intro'}])
        self.assertEqual(data['lesson_count'], 1)

    def test_unknown_or_unpublished_is_json_404(self):
        Module.objects.create(slug='draft-module')
        for slug in ('nope', 'draft-module'):
            response = self.client.get(f'/api/v1/modules/{slug}/')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(json.loads(response.content), {'error': 'not_found'})

    def test_read_only(self):
        self.assertEqual(self.client.post('/api/v1/modules/', {}).status_code, 405)
