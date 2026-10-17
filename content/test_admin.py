import json
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from content.models import Lesson, LessonRevision, PracticeActivityRevision
from content.services import ROLE_GROUPS

User = get_user_model()


def staff_client(email, role):
    from django_otp.plugins.otp_totp.models import TOTPDevice
    user = User.objects.create_user(email, 'strong-password-123', is_staff=True)
    user.groups.add(Group.objects.get_or_create(name=ROLE_GROUPS[role])[0])
    device = TOTPDevice.objects.create(user=user, name='t', confirmed=True)
    client = Client()
    client.force_login(user)
    session = client.session
    session['otp_device_id'] = device.persistent_id
    session.save()
    return user, client


def action(client, model, name, pks):
    return client.post(f'/admin/content/{model}/', {'action': name, '_selected_action': pks})


class AuthoringToPublicReaderTests(TestCase):
    def setUp(self):
        self.author, self.author_c = staff_client('author@example.com', 'author_editor')
        self.reviewer, self.reviewer_c = staff_client('reviewer@example.com', 'reviewer')
        self.approver, self.approver_c = staff_client('approver@example.com', 'approver_publisher')

    def make_lesson(self):
        self.assertEqual(self.author_c.post('/admin/content/lesson/add/', {'slug': 'saving-basics', '_save': 'Save'}).status_code, 302)
        lesson = Lesson.objects.get(slug='saving-basics')
        response = self.author_c.post('/admin/content/lessonrevision/add/', {
            'lesson': lesson.pk, 'title': 'Saving basics', 'summary': 'Intro',
            'body': 'First paragraph about saving.\n\nSecond paragraph about sacco.', '_save': 'Save'})
        self.assertEqual(response.status_code, 302, getattr(response, 'content', b'')[:500])
        return LessonRevision.objects.get(lesson=lesson)

    def test_author_creates_draft_with_structured_blocks(self):
        rev = self.make_lesson()
        self.assertEqual((rev.status, rev.revision_number, rev.author_id), ('draft', 1, self.author.pk))
        self.assertEqual([b['payload']['text'] for b in rev.blocks], ['First paragraph about saving.', 'Second paragraph about sacco.'])
        self.assertEqual(self.client.get('/lessons/saving-basics/').status_code, 404)   # draft is not public

    def test_full_flow_author_review_publish_then_public_reader_and_search(self):
        rev = self.make_lesson()
        action(self.author_c, 'lessonrevision', 'submit_for_review_action', [rev.pk])
        rev.refresh_from_db(); self.assertEqual(rev.status, 'in_review')
        action(self.approver_c, 'lessonrevision', 'publish_action', [rev.pk])        # no review yet
        rev.refresh_from_db(); self.assertEqual(rev.status, 'in_review')
        action(self.reviewer_c, 'lessonrevision', 'review_action', [rev.pk])
        action(self.approver_c, 'lessonrevision', 'publish_action', [rev.pk])
        rev.refresh_from_db(); self.assertEqual(rev.status, 'published')
        page = Client().get('/lessons/saving-basics/')
        self.assertContains(page, 'First paragraph about saving.')
        self.assertContains(Client().get('/search/?q=sacco'), 'Saving basics')

    def test_author_cannot_publish_or_review_own_work(self):
        rev = self.make_lesson()
        author2, author2_c = staff_client('a2@example.com', 'approver_publisher')
        action(self.author_c, 'lessonrevision', 'submit_for_review_action', [rev.pk])
        action(self.author_c, 'lessonrevision', 'publish_action', [rev.pk])
        rev.refresh_from_db(); self.assertEqual(rev.status, 'in_review')

    def test_submitted_revision_is_read_only(self):
        rev = self.make_lesson()
        action(self.author_c, 'lessonrevision', 'submit_for_review_action', [rev.pk])
        response = self.author_c.post(f'/admin/content/lessonrevision/{rev.pk}/change/', {
            'lesson': rev.lesson_id, 'title': 'Changed', 'summary': '', 'body': 'x', '_save': 'Save'})
        self.assertIn(response.status_code, (302, 403))
        rev.refresh_from_db(); self.assertEqual(rev.title, 'Saving basics')

    def test_reviewer_and_learner_cannot_create_content(self):
        self.assertEqual(self.reviewer_c.post('/admin/content/lesson/add/', {'slug': 'nope', '_save': 'Save'}).status_code, 403)
        learner = User.objects.create_user('l@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        c = Client(); c.force_login(learner)
        self.assertNotEqual(c.get('/admin/content/lesson/').status_code, 200)
        self.assertFalse(Lesson.objects.filter(slug='nope').exists())

    def test_practice_schema_is_validated_in_the_form(self):
        self.author_c.post('/admin/content/practiceactivity/add/', {'slug': 'budget', '_save': 'Save'})
        from content.models import PracticeActivity
        act = PracticeActivity.objects.get(slug='budget')
        base = {'activity': act.pk, 'title': 'Budget', 'instructions': 'i', 'prompt': 'p', 'safety_text': '', '_save': 'Save'}
        bad = self.author_c.post('/admin/content/practiceactivityrevision/add/', {**base, 'response_schema': '{"questions": []}'})
        self.assertEqual(bad.status_code, 200)
        self.assertFalse(PracticeActivityRevision.objects.exists())
        good_schema = {'schema_version': 1, 'questions': [{'id': 'income', 'type': 'decimal_amount', 'label': 'Income', 'required': True, 'constraints': {'currency': 'KES'}}]}
        ok = self.author_c.post('/admin/content/practiceactivityrevision/add/', {**base, 'response_schema': json.dumps(good_schema)})
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(PracticeActivityRevision.objects.get().author_id, self.author.pk)

    def test_changelist_pages_render_for_each_role(self):
        for client in (self.author_c, self.reviewer_c, self.approver_c):
            for model in ('lessonrevision', 'modulerevision', 'playbookrevision', 'practiceactivityrevision'):
                self.assertEqual(client.get(f'/admin/content/{model}/').status_code, 200, model)
        for model in ('modulerevision', 'playbookrevision'):
            self.assertEqual(self.author_c.get(f'/admin/content/{model}/add/').status_code, 200, model)


class CreateStaffCommandTests(TestCase):
    def test_creates_staff_with_role_and_confirmed_device(self):
        out = StringIO()
        with mock.patch('getpass.getpass', return_value='a-Strong-pass-12345'):
            call_command('create_staff', 'Editor@Example.com', '--roles', 'author_editor,reviewer', stdout=out)
        user = User.objects.get(email='editor@example.com')
        self.assertTrue(user.is_staff and user.email_verified)
        self.assertEqual(set(user.groups.values_list('name', flat=True)), {'Author/Editor', 'Reviewer'})
        self.assertTrue(user.totpdevice_set.filter(confirmed=True).exists())
        self.assertIn('otpauth://', out.getvalue())

    def test_unknown_role_is_rejected(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('create_staff', 'x@example.com', '--roles', 'god')
