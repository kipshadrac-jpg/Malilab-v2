from django.core.exceptions import ValidationError
from django.test import TestCase
from content.models import Lesson, LessonRevision
from discovery.models import SearchProjection
from discovery.services import rebuild_revision_projection

class PublicSearchProjectionTests(TestCase):
    def test_only_current_published_editorial_revision_is_projected(self):
        lesson=Lesson.objects.create(slug='public-lesson')
        revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Public',status='published')
        self.assertIsNone(rebuild_revision_projection(content_kind='lesson',revision=revision,title='Public',searchable_text='Public text'))
        lesson.current_published_revision=revision
        lesson._allow_pointer_update=True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update=False
        projection=rebuild_revision_projection(content_kind='lesson',revision=revision,title='Public',searchable_text='Public text')
        self.assertEqual(projection.lesson_revision_id,revision.pk)
        self.assertEqual(SearchProjection.objects.count(),1)
    def test_private_kind_cannot_enter_search(self):
        with self.assertRaises(ValidationError):
            rebuild_revision_projection(content_kind='note',revision=None,title='private',searchable_text='private')
    def test_superseded_projection_is_removed(self):
        lesson=Lesson.objects.create(slug='rotating-public')
        first=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='First',status='published')
        lesson.current_published_revision=first
        lesson._allow_pointer_update=True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update=False
        rebuild_revision_projection(content_kind='lesson',revision=first,title='First',searchable_text='First')
        second=LessonRevision.objects.create(lesson=lesson,revision_number=2,title='Second',status='published')
        lesson.current_published_revision=second
        lesson._allow_pointer_update=True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update=False
        rebuild_revision_projection(content_kind='lesson',revision=second,title='Second',searchable_text='Second')
        self.assertEqual(SearchProjection.objects.count(),1)
        self.assertEqual(SearchProjection.objects.get().lesson_revision_id,second.pk)
