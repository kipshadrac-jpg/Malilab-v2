from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from content.models import Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision
from learning.models import LessonCompletion, ModuleCompletion

User = get_user_model()
KEY = '00000000-0000-0000-0000-0000000000c1'


def publish(rev, identity):
    rev.status = 'published'; rev._allow_lifecycle_transition = True; rev.save()
    identity.current_published_revision = rev; identity.status = 'published'
    identity._allow_pointer_update = True; identity.save()


def learner(email):
    return User.objects.create_user(email, 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


class LessonCompletionTests(TestCase):
    def setUp(self):
        self.lesson = Lesson.objects.create(slug='read-me')
        self.rev = LessonRevision.objects.create(lesson=self.lesson, revision_number=1, title='Read me',
            blocks=[{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': 'Some text.'}}])
        publish(self.rev, self.lesson)
        self.module, self.mrev = self.make_module('mod-a', 'Module A')
        self.user = learner('reader1@example.com')
        self.c = Client(); self.c.force_login(self.user)

    def make_module(self, slug, title):
        module = Module.objects.create(slug=slug)
        mrev = ModuleRevision.objects.create(module=module, revision_number=1, title=title)
        req = ModuleLearningRequirement.objects.create(module_revision=mrev, target_kind='lesson',
                                                       lesson_revision=self.rev, classification='required', position=1)
        publish(mrev, module)
        return module, mrev

    def test_anonymous_cannot_mark_complete(self):
        response = Client().post('/lessons/read-me/complete/')
        self.assertEqual(response.status_code, 302); self.assertIn('sign-in', response['Location'])
        self.assertFalse(LessonCompletion.objects.exists())

    def test_button_shows_then_is_replaced_by_confirmation(self):
        self.assertContains(self.c.get('/lessons/read-me/?module=mod-a'), 'Mark this lesson as complete')
        self.assertEqual(self.c.post('/lessons/read-me/complete/', {'module': 'mod-a'}).status_code, 302)
        page = self.c.get('/lessons/read-me/?module=mod-a')
        self.assertContains(page, 'You marked this lesson complete')
        self.assertNotContains(page, 'Mark this lesson as complete')

    def test_completion_is_pinned_linked_and_idempotent(self):
        self.c.post('/lessons/read-me/complete/'); self.c.post('/lessons/read-me/complete/')
        row = LessonCompletion.objects.get()
        req = self.mrev.learning_requirements.get()
        self.assertEqual((row.owner_id, row.lesson_revision_id, row.requirement_id, row.evidence_kind),
                         (self.user.pk, self.rev.pk, req.pk, 'learner_marked_complete'))

    def test_required_lesson_blocks_then_completes_the_module(self):
        self.c.post('/modules/mod-a/completion/')
        self.assertEqual(ModuleCompletion.objects.get().outcome, 'incomplete')
        self.c.post('/lessons/read-me/complete/')
        self.c.post('/modules/mod-a/completion/')
        self.assertEqual(ModuleCompletion.objects.latest('evaluated_at').outcome, 'complete')

    def test_one_click_covers_every_module_that_requires_the_lesson(self):
        self.make_module('mod-b', 'Module B')
        self.c.post('/lessons/read-me/complete/')
        self.assertEqual(LessonCompletion.objects.filter(owner=self.user).count(), 2)

    def test_lesson_added_to_a_second_module_later_can_still_be_recorded(self):
        self.c.post('/lessons/read-me/complete/')
        self.make_module('mod-c', 'Module C')
        self.assertContains(self.c.get('/lessons/read-me/'), 'Mark this lesson as complete')
        self.c.post('/lessons/read-me/complete/')
        self.assertEqual(LessonCompletion.objects.filter(owner=self.user).count(), 2)
        self.assertNotContains(self.c.get('/lessons/read-me/'), 'Mark this lesson as complete')

    def test_another_learner_is_not_credited(self):
        self.c.post('/lessons/read-me/complete/')
        other = learner('reader2@example.com'); oc = Client(); oc.force_login(other)
        oc.post('/modules/mod-a/completion/')
        self.assertEqual(ModuleCompletion.objects.get(owner=other).outcome, 'incomplete')
        self.assertContains(oc.get('/lessons/read-me/'), 'Mark this lesson as complete')

    def test_unpublished_lesson_cannot_be_marked(self):
        Lesson.objects.create(slug='hidden')
        self.assertEqual(self.c.post('/lessons/hidden/complete/').status_code, 404)

    def test_get_is_not_allowed(self):
        self.assertEqual(self.c.get('/lessons/read-me/complete/').status_code, 405)
