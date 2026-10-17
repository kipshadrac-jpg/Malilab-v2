from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from content.authoring import start_revision_from
from content.models import (Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision)
from content.services import ROLE_GROUPS, approve_and_publish, review_revision, submit_for_review
from content.test_admin import action, staff_client

User = get_user_model()
KEY = '00000000-0000-0000-0000-0000000000a1'


def staff(email, role):
    user = User.objects.create_user(email, 'strong-password-123', is_staff=True)
    user.groups.add(Group.objects.get_or_create(name=ROLE_GROUPS[role])[0])
    user.is_verified = lambda: True
    return user


class StartRevisionTests(TestCase):
    def setUp(self):
        self.author = staff('au@example.com', 'author_editor')
        self.reviewer = staff('re@example.com', 'reviewer')
        self.approver = staff('ap@example.com', 'approver_publisher')

    def publish(self, rev):
        submit_for_review(revision=rev, actor=self.author)
        review_revision(revision=rev, actor=self.reviewer)
        approve_and_publish(revision=rev, actor=self.approver)
        rev.refresh_from_db()

    def lesson(self, slug='l1', text='Original text.'):
        lesson = Lesson.objects.create(slug=slug)
        rev = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='T', author=self.author,
                                            blocks=[{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': text}}])
        self.publish(rev)
        return lesson, rev

    def test_copy_creates_draft_with_same_blocks_and_leaves_source_untouched(self):
        lesson, rev = self.lesson()
        new = start_revision_from(revision=rev, actor=self.author)
        self.assertEqual((new.status, new.revision_number, new.author_id), ('draft', 2, self.author.pk))
        self.assertEqual(new.blocks, rev.blocks)
        self.assertIsNot(new.blocks, rev.blocks)
        rev.refresh_from_db(); self.assertEqual(rev.status, 'published')
        lesson.refresh_from_db(); self.assertEqual(lesson.current_published_revision_id, rev.pk)

    def test_only_one_unpublished_revision_at_a_time(self):
        _, rev = self.lesson()
        start_revision_from(revision=rev, actor=self.author)
        with self.assertRaises(ValidationError):
            start_revision_from(revision=rev, actor=self.author)

    def test_only_author_role_may_copy(self):
        _, rev = self.lesson()
        with self.assertRaises(PermissionDenied):
            start_revision_from(revision=rev, actor=self.reviewer)

    def test_module_copy_repoints_requirements_to_current_published_lesson(self):
        lesson, rev1 = self.lesson()
        module = Module.objects.create(slug='m1')
        mrev = ModuleRevision.objects.create(module=module, revision_number=1, title='M', author=self.author)
        ModuleLearningRequirement.objects.create(module_revision=mrev, target_kind='lesson', lesson_revision=rev1, position=1)
        self.publish(mrev)
        rev2 = start_revision_from(revision=rev1, actor=self.author)
        rev2.blocks = [{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': 'Corrected text.'}}]
        rev2.save()
        self.publish(rev2)
        new_module = start_revision_from(revision=mrev, actor=self.author)
        req = new_module.learning_requirements.get()
        self.assertEqual(req.lesson_revision_id, rev2.pk)
        self.assertEqual(mrev.learning_requirements.get().lesson_revision_id, rev1.pk)   # history unchanged

    def test_admin_action_creates_new_draft(self):
        author, author_c = staff_client('adm-au@example.com', 'author_editor')
        lesson = Lesson.objects.create(slug='adm')
        rev = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='T', author=author,
                                            blocks=[{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': 'Hi.'}}])
        rev.status = 'published'; rev._allow_lifecycle_transition = True; rev.save()
        action(author_c, 'lessonrevision', 'start_new_draft_action', [rev.pk])
        self.assertEqual(lesson.revisions.filter(status='draft', revision_number=2).count(), 1)
