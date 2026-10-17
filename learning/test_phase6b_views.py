from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone

User=get_user_model()

class LearningViewSmokeTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('reader@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())

    def test_private_pages_render_for_verified_account(self):
        client=Client(); client.force_login(self.user)
        for path, heading in [('/notes/','My Notes'),('/progress/','Progress'),('/my-plan/','My Plan')]:
            response=client.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertContains(response,heading)

    def test_note_highlight_is_saved_and_returns_to_pinned_revision(self):
        from content.models import Lesson, LessonRevision
        lesson=Lesson.objects.create(slug='note-reader')
        revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Pinned Lesson',blocks=[{'key':'00000000-0000-0000-0000-000000000001','type':'paragraph','position':0,'payload':{'text':'A precise source quote.'}}])
        revision.status='published'; revision._allow_lifecycle_transition=True; revision.save()
        lesson.current_published_revision=revision; lesson.status='published'; lesson._allow_pointer_update=True; lesson.save()
        self.client.force_login(self.user)
        response=self.client.post('/lessons/note-reader/notes/', {'kind':'highlight','body':'My thought','block_key':'00000000-0000-0000-0000-000000000001','selected_quote':'precise source quote'})
        self.assertEqual(response.status_code,302)
        note=self.user.notes.get()
        self.assertEqual(note.lesson_revision_id,revision.pk)
        self.assertEqual(note.block_key,'00000000-0000-0000-0000-000000000001')
        self.assertEqual(note.lesson_revision.blocks[0]['payload']['text'],'A precise source quote.')
        source=self.client.get(f'/notes/{note.pk}/source/')
        self.assertContains(source,'Pinned Lesson')
        self.assertContains(source,'A precise source quote.')
