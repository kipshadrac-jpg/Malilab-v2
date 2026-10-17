from django.db import connection, IntegrityError, transaction
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.contrib.auth import get_user_model
from django.apps import apps
from content.models import Lesson, LessonRevision
from content.models import Module, ModuleRevision, ModuleLearningRequirement, PracticeActivity, PracticeActivityRevision
from discovery.models import SearchProjection
from discovery.services import rebuild_published_projection

User = get_user_model()

@skipUnlessDBFeature('supports_transactions')
class PostgreSQLPhase6AIntegrationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('This integration layer requires PostgreSQL.')

    def test_postgresql_backend_schema_migrations_constraints_and_gin(self):
        self.assertEqual(connection.vendor, 'postgresql')
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('server_version_num')::int")
            self.assertGreaterEqual(cursor.fetchone()[0], 140000)
            cursor.execute("SELECT count(*) FROM django_migrations WHERE app IN ('accounts','content','practice','calculations','planning','learning','discovery')")
            self.assertGreaterEqual(cursor.fetchone()[0], 16)
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            actual_tables = {row[0] for row in cursor.fetchall()}
            cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='discovery_searchprojection' AND column_name='filter_metadata'")
            self.assertEqual(cursor.fetchone()[0], 'jsonb')
        expected_tables = {model._meta.db_table for model in apps.get_models(include_auto_created=True)} | {'django_migrations'}
        self.assertEqual(actual_tables, expected_tables)
        indexes = connection.introspection.get_constraints(connection.cursor(), 'discovery_searchprojection')
        self.assertTrue(any(name == 'search_vector_gin_idx' and info.get('type') == 'gin' for name, info in indexes.items()))
        self.assertIn('search_projection_target_kind_match', indexes)
        self.assertIn('search_lesson_revision_uniq', indexes)
        evidence_indexes = connection.introspection.get_constraints(connection.cursor(), 'learning_requirementevidence')
        self.assertIn('evidence_attempt_accepted_uniq', evidence_indexes)
        self.assertTrue(evidence_indexes['evidence_attempt_accepted_uniq'].get('unique'))
        self.assertIn('evidence_attempt_requirement_uniq', evidence_indexes)
        module_constraints = connection.introspection.get_constraints(connection.cursor(), 'content_modulerevision')
        self.assertIn('module_revision_positive', module_constraints)
        self.assertIn('module_revision_uniq', module_constraints)
        with connection.cursor() as cursor:
            cursor.execute("SELECT indexdef FROM pg_indexes WHERE schemaname='public' AND indexname='evidence_attempt_accepted_uniq'")
            self.assertIn('WHERE', cursor.fetchone()[0])

    def test_projection_populates_vector_and_only_current_published_revision(self):
        lesson = Lesson.objects.create(slug='pg-search-sacco')
        old = LessonRevision.objects.create(lesson=lesson, revision_number=1, status='published', title='Old', blocks=[{'key':'00000000-0000-0000-0000-000000000001','type':'paragraph','position':0,'payload':{'text':'SACCO guide'}}])
        lesson.current_published_revision = old
        lesson._allow_pointer_update = True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update = False
        projection = rebuild_published_projection(content_kind='lesson', revision=old)
        self.assertIsNotNone(projection.search_vector)
        with connection.cursor() as cursor:
            cursor.execute('SELECT search_vector @@ plainto_tsquery(\'english\', %s) FROM discovery_searchprojection WHERE id=%s', ['sacco', projection.pk])
            self.assertTrue(cursor.fetchone()[0])
        new = LessonRevision.objects.create(lesson=lesson, revision_number=2, status='published', title='T-bill', blocks=[{'key':'00000000-0000-0000-0000-000000000002','type':'paragraph','position':0,'payload':{'text':'Treasury bill guide'}}])
        lesson.current_published_revision = new
        lesson._allow_pointer_update = True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update = False
        current = rebuild_published_projection(content_kind='lesson', revision=new)
        self.assertEqual(SearchProjection.objects.count(), 1)
        self.assertEqual(current.lesson_revision_id, new.pk)
        unpublished = LessonRevision.objects.create(lesson=lesson, revision_number=3, status='draft', title='Private', blocks=[])
        self.assertIsNone(rebuild_published_projection(content_kind='lesson', revision=unpublished))
        self.assertEqual(SearchProjection.objects.count(), 1)

    def test_postgresql_conditional_unique_rejects_duplicate_current_projection(self):
        lesson = Lesson.objects.create(slug='pg-unique')
        revision = LessonRevision.objects.create(lesson=lesson, revision_number=1, status='published', title='One')
        lesson.current_published_revision = revision
        lesson._allow_pointer_update = True
        lesson.save(update_fields=['current_published_revision','updated_at'])
        lesson._allow_pointer_update = False
        rebuild_published_projection(content_kind='lesson', revision=revision)
        with self.assertRaises(Exception):
            SearchProjection.objects.create(content_kind='lesson', lesson_revision=revision, title='duplicate', searchable_text='duplicate')

    def test_postgresql_rejects_invalid_search_target_at_database_boundary(self):
        lesson = Lesson.objects.create(slug='pg-invalid-search-target')
        revision = LessonRevision.objects.create(lesson=lesson, revision_number=1, status='draft', title='Private')
        with self.assertRaises(IntegrityError), transaction.atomic():
            SearchProjection.objects.create(content_kind='module', lesson_revision=revision, title='wrong target', searchable_text='private')

    def test_postgresql_rejects_invalid_requirement_classification_at_database_boundary(self):
        module_revision = ModuleRevision.objects.create(module=Module.objects.create(slug='pg-classification'), revision_number=1, title='Module')
        practice_revision = PracticeActivityRevision.objects.create(activity=PracticeActivity.objects.create(slug='pg-classification-practice'), revision_number=1, title='Practice')
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO content_modulelearningrequirement (module_revision_id, target_kind, lesson_revision_id, practice_revision_id, classification, position, completion_condition_key, active, created_at) VALUES (%s, 'practice', NULL, %s, 'blocking', 1, '', true, NOW())", [module_revision.pk, practice_revision.pk])
