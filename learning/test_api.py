"""Patch 18: lessons and progress for the app."""
import json

from django.test import Client, TestCase, override_settings

from accounts.api import issue_token
from config.test_6b11 import SiteFixtureMixin
from content.models import Lesson
from learning.models import LessonCompletion


@override_settings(SECURE_SSL_REDIRECT=False)
class LessonApiTests(SiteFixtureMixin, TestCase):
    def setUp(self):
        self.build_site()
        self.client = Client()
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + issue_token(self.user)}

    def test_lesson_is_public_and_has_its_blocks(self):
        data = json.loads(self.client.get('/api/v1/lessons/les/').content)
        self.assertEqual((data['slug'], data['title'], data['summary']), ('les', 'Sacco basics', 'Intro'))
        self.assertEqual(data['blocks'][0]['type'], 'paragraph')
        self.assertEqual(data['blocks'][0]['payload'], {'text': 'A sacco is a savings society.'})

    def test_unknown_or_unpublished_lesson_is_404(self):
        Lesson.objects.create(slug='draft-lesson')
        self.assertEqual(self.client.get('/api/v1/lessons/nope/').status_code, 404)
        self.assertEqual(self.client.get('/api/v1/lessons/draft-lesson/').status_code, 404)
        self.assertEqual(self.client.post('/api/v1/lessons/nope/complete/', **self.auth).status_code, 404)

    def test_progress_and_completion_need_a_signed_in_learner(self):
        self.assertEqual(self.client.get('/api/v1/progress/').status_code, 401)
        self.assertEqual(self.client.post('/api/v1/lessons/les/complete/').status_code, 401)

    def test_progress_starts_empty(self):
        data = json.loads(self.client.get('/api/v1/progress/', **self.auth).content)
        self.assertEqual(data['lessons'], [])
        self.assertEqual(data['modules'], [{'slug': 'mod', 'done': 0, 'total': 1, 'practice_done': 0, 'practice_total': 1, 'complete': False}])

    def test_marking_the_only_lesson_is_repeatable_and_the_required_practice_still_counts(self):
        first = self.client.post('/api/v1/lessons/les/complete/', **self.auth)
        self.assertEqual(first.status_code, 200)
        data = json.loads(first.content)
        self.assertEqual(data['completed'], 'les')
        self.assertEqual(data['lessons'], ['les'])
        self.assertEqual(data['modules'], [{'slug': 'mod', 'done': 1, 'total': 1, 'practice_done': 0, 'practice_total': 1, 'complete': False}])
        count = LessonCompletion.objects.count()
        self.client.post('/api/v1/lessons/les/complete/', **self.auth)
        self.assertEqual(LessonCompletion.objects.count(), count)
        again = json.loads(self.client.get('/api/v1/progress/', **self.auth).content)
        # The module also has a required practice, so finishing the lesson alone does not complete it.
        self.assertFalse(again['modules'][0]['complete'])

    def test_one_learners_progress_is_not_anothers(self):
        self.client.post('/api/v1/lessons/les/complete/', **self.auth)
        from django.utils import timezone
        from accounts.models import UserAccount
        other = UserAccount.objects.create_user('other@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        data = json.loads(self.client.get('/api/v1/progress/', HTTP_AUTHORIZATION='Bearer ' + issue_token(other)).content)
        self.assertEqual(data['lessons'], [])
