from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from content.models import Lesson, LessonRevision

User = get_user_model()
K1, K2 = '00000000-0000-0000-0000-0000000000d1', '00000000-0000-0000-0000-0000000000d2'


class NotesParagraphPickerTests(TestCase):
    def setUp(self):
        lesson = Lesson.objects.create(slug='picker')
        self.rev = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='Picker lesson', blocks=[
            {'key': K1, 'type': 'paragraph', 'position': 0, 'payload': {'text': 'First paragraph about budgets.'}},
            {'key': K2, 'type': 'paragraph', 'position': 1, 'payload': {'text': 'Second paragraph about sacco loans.'}}])
        self.rev.status = 'published'; self.rev._allow_lifecycle_transition = True; self.rev.save()
        lesson.current_published_revision = self.rev; lesson.status = 'published'; lesson._allow_pointer_update = True; lesson.save()
        self.user = User.objects.create_user('np@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.client.force_login(self.user)

    def test_learner_picks_a_paragraph_instead_of_typing_a_key(self):
        page = self.client.get('/lessons/picker/notes/')
        self.assertContains(page, 'Paragraph 1: First paragraph about budgets.')
        self.assertContains(page, 'Paragraph 2: Second paragraph about sacco loans.')
        self.assertContains(page, f'value="{K2}"')
        self.assertNotContains(page, 'block key')

    def test_highlight_through_the_picker_is_pinned_to_the_chosen_paragraph(self):
        self.client.post('/lessons/picker/notes/', {'kind': 'highlight', 'body': 'x', 'block_key': K2, 'selected_quote': 'sacco loans'})
        note = self.user.notes.get()
        self.assertEqual((note.lesson_revision_id, note.block_key), (self.rev.pk, K2))

    def test_quote_from_a_different_paragraph_is_refused(self):
        response = self.client.post('/lessons/picker/notes/', {'kind': 'highlight', 'body': 'x', 'block_key': K1, 'selected_quote': 'sacco loans'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.user.notes.exists())
