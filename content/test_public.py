import uuid
import json

from django.db import connection
from django.test import TestCase
from django.urls import reverse

from content.models import (
    Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision,
    Playbook, PlaybookModuleRecommendation, PlaybookRevision,
)


def publish(revision, identity, pointer='current_published_revision'):
    revision.status = 'published'
    revision._allow_lifecycle_transition = True
    revision.save(update_fields=['status'])
    revision._allow_lifecycle_transition = False
    setattr(identity, pointer, revision)
    identity.status = 'published'
    identity._allow_pointer_update = True
    identity.save(update_fields=[pointer, 'status', 'updated_at'])
    identity._allow_pointer_update = False


class PublicReaderTests(TestCase):
    def setUp(self):
        self.playbook = Playbook.objects.create(slug='saving-path')
        self.playbook_revision = PlaybookRevision.objects.create(
            playbook=self.playbook, revision_number=1, title='A saving path',
            summary='A supported summary.', scenario='An approved scenario.',
        )
        self.module = Module.objects.create(slug='saving-module')
        self.module_revision = ModuleRevision.objects.create(
            module=self.module, revision_number=1, title='Saving basics', description='A module.',
        )
        PlaybookModuleRecommendation.objects.create(
            playbook_revision=self.playbook_revision,
            module_revision=self.module_revision, position=1, rationale='Editorial rationale.',
        )
        self.lessons = []
        for slug, title, position in [('last-lesson', 'Last lesson', 30), ('first-lesson', 'First lesson', 10), ('middle-lesson', 'Middle lesson', 20)]:
            identity = Lesson.objects.create(slug=slug)
            revision = LessonRevision.objects.create(
                lesson=identity, revision_number=1, title=title,
                blocks=[{'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                         'payload': {'text': title + ' body.'}}],
            )
            publish(revision, identity)
            ModuleLearningRequirement.objects.create(
                module_revision=self.module_revision, target_kind='lesson',
                lesson_revision=revision, position=position,
            )
            self.lessons.append((identity, revision))
        hidden_module = Module.objects.create(slug='hidden-module')
        hidden_module_revision = ModuleRevision.objects.create(module=hidden_module, revision_number=1, title='Hidden')
        PlaybookModuleRecommendation.objects.create(playbook_revision=self.playbook_revision, module_revision=hidden_module_revision, position=2)
        hidden_lesson = Lesson.objects.create(slug='hidden-lesson')
        hidden_lesson_revision = LessonRevision.objects.create(lesson=hidden_lesson, revision_number=1, title='Private title')
        ModuleLearningRequirement.objects.create(module_revision=self.module_revision, target_kind='lesson', lesson_revision=hidden_lesson_revision, position=40)
        publish(self.module_revision, self.module)
        publish(self.playbook_revision, self.playbook)

    def test_playbook_shows_only_safe_recommendations(self):
        response = self.client.get(reverse('playbook-detail', args=['saving-path']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A saving path')
        self.assertContains(response, 'Saving basics')
        response = self.client.get('/playbooks/saving-path/')
        self.assertNotContains(response, 'Hidden')

    def test_only_current_published_playbooks_are_resolvable(self):
        for status in ('draft', 'in_review', 'rejected', 'superseded'):
            identity = Playbook.objects.create(slug='blocked-' + status)
            revision = PlaybookRevision.objects.create(playbook=identity, revision_number=1, title='Hidden')
            revision.status = status
            revision._allow_lifecycle_transition = True
            revision.save(update_fields=['status'])
            revision._allow_lifecycle_transition = False
            identity.status = 'published'
            identity._allow_pointer_update = True
            identity.current_published_revision = revision
            identity.save(update_fields=['status', 'current_published_revision', 'updated_at'])
            identity._allow_pointer_update = False
            response = self.client.get('/playbooks/blocked-' + status + '/')
            self.assertEqual(response.status_code, 404)
        self.playbook.current_published_revision = None
        self.playbook._allow_pointer_update = True
        self.playbook.save(update_fields=['current_published_revision', 'updated_at'])
        self.playbook._allow_pointer_update = False
        self.assertEqual(self.client.get('/playbooks/saving-path/').status_code, 404)

    def test_revision_from_another_identity_cannot_be_exposed(self):
        other = Playbook.objects.create(slug='other-path')
        other_revision = PlaybookRevision.objects.create(playbook=other, revision_number=1, title='Other')
        publish(other_revision, other)
        self.playbook.current_published_revision = other_revision
        self.playbook._allow_pointer_update = True
        self.playbook.save(update_fields=['current_published_revision', 'updated_at'])
        self.playbook._allow_pointer_update = False
        self.assertEqual(self.client.get('/playbooks/saving-path/').status_code, 404)

    def test_module_lists_exact_current_lessons_in_position_order(self):
        response = self.client.get('/modules/saving-module/')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertLess(body.index('First lesson'), body.index('Middle lesson'))
        self.assertLess(body.index('Middle lesson'), body.index('Last lesson'))
        self.assertContains(response, '?module=saving-module')

    def test_playbook_context_is_validated_and_returnable(self):
        response = self.client.get('/modules/saving-module/?playbook=saving-path')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A saving path')
        self.assertContains(response, '&amp;playbook=saving-path')
        lesson = self.client.get('/lessons/first-lesson/?module=saving-module&playbook=saving-path')
        self.assertEqual(lesson.status_code, 200)
        self.assertContains(lesson, 'Return to A saving path')
        self.assertEqual(self.client.get('/modules/saving-module/?playbook=missing').status_code, 404)

    def test_unpublished_lesson_is_not_listed_or_resolvable(self):
        self.assertNotContains(self.client.get('/modules/saving-module/'), 'Private title')
        self.assertEqual(self.client.get('/lessons/hidden-lesson/').status_code, 404)

    def test_lesson_escapes_html_orders_paragraphs_and_supports_empty_body(self):
        identity = Lesson.objects.create(slug='xss-lesson')
        revision = LessonRevision.objects.create(lesson=identity, revision_number=1, title='Safe text', blocks=[
            {'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 2, 'payload': {'text': '<script>alert(1)</script>'}},
            {'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 1, 'payload': {'text': 'Earlier paragraph.'}},
        ])
        publish(revision, identity)
        response = self.client.get('/lessons/xss-lesson/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>')
        body = response.content.decode()
        self.assertLess(body.index('Earlier paragraph.'), body.index('&lt;script&gt;'))
        empty = Lesson.objects.create(slug='empty-lesson')
        empty_revision = LessonRevision.objects.create(lesson=empty, revision_number=1, title='Empty reading', blocks=[])
        publish(empty_revision, empty)
        self.assertContains(self.client.get('/lessons/empty-lesson/'), 'no reading content yet')

    def test_unsupported_corrupt_blocks_fail_closed(self):
        identity, revision = self.lessons[1]
        with connection.cursor() as cursor:
            cursor.execute('UPDATE content_lessonrevision SET blocks = %s WHERE id = %s', [json.dumps([{'type': 'video', 'payload': {'url': 'javascript:alert(1)'}}]), revision.pk])
        response = self.client.get('/lessons/first-lesson/')
        self.assertContains(response, 'temporarily unavailable')
        self.assertNotContains(response, 'javascript:')

    def test_lesson_navigation_uses_only_selected_module_revision(self):
        _, middle = self.lessons[2]
        response = self.client.get('/lessons/middle-lesson/?module=saving-module')
        self.assertContains(response, 'first-lesson/')
        self.assertContains(response, 'last-lesson/')
        self.assertNotContains(self.client.get('/lessons/first-lesson/?module=saving-module'), 'rel="prev"')
        self.assertNotContains(self.client.get('/lessons/last-lesson/?module=saving-module'), 'rel="next"')
        self.assertEqual(self.client.get('/lessons/middle-lesson/?module=missing/').status_code, 404)

    def test_automatic_context_ignores_mismatched_module_pointer(self):
        target_identity, target_revision = self.lessons[1]
        unrelated_module = Module.objects.create(slug='unpublished-owner')
        unrelated_revision = ModuleRevision.objects.create(
            module=unrelated_module, revision_number=1, title='Unrelated revision',
        )
        neighbor_revisions = []
        for slug, title, position in (
            ('foreign-prev', 'Foreign previous', 1),
            ('first-lesson', 'Target duplicate', 2),
            ('foreign-next', 'Foreign next', 3),
        ):
            if slug == 'first-lesson':
                lesson_revision = target_revision
            else:
                lesson = Lesson.objects.create(slug=slug)
                lesson_revision = LessonRevision.objects.create(
                    lesson=lesson, revision_number=1, title=title,
                    blocks=[{'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                             'payload': {'text': title}}],
                )
                publish(lesson_revision, lesson)
            ModuleLearningRequirement.objects.create(
                module_revision=unrelated_revision, target_kind='lesson',
                lesson_revision=lesson_revision, position=position,
            )
            neighbor_revisions.append(lesson_revision)
        unrelated_revision.status = 'published'
        unrelated_revision._allow_lifecycle_transition = True
        unrelated_revision.save(update_fields=['status'])

        # Model guards correctly prevent this state; simulate corrupted stored
        # editorial data so the public request exercises the ownership boundary.
        Module.objects.filter(pk=self.module.pk).update(
            current_published_revision=unrelated_revision,
        )
        response = self.client.get('/lessons/first-lesson/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'foreign-prev/')
        self.assertNotContains(response, 'foreign-next/')
        self.assertNotContains(response, 'rel="prev"')
        self.assertNotContains(response, 'rel="next"')
        self.assertEqual(self.client.get('/lessons/first-lesson/?module=saving-module').status_code, 404)

    def test_multiple_valid_module_contexts_suppress_ambiguous_navigation(self):
        _, target_revision = self.lessons[1]
        other_module = Module.objects.create(slug='second-module')
        other_revision = ModuleRevision.objects.create(module=other_module, revision_number=1, title='Second')
        neighbor = Lesson.objects.create(slug='second-neighbor')
        neighbor_revision = LessonRevision.objects.create(
            lesson=neighbor, revision_number=1, title='Second neighbor',
            blocks=[{'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                     'payload': {'text': 'Second neighbor'}}],
        )
        publish(neighbor_revision, neighbor)
        ModuleLearningRequirement.objects.create(module_revision=other_revision, target_kind='lesson', lesson_revision=target_revision, position=1)
        ModuleLearningRequirement.objects.create(module_revision=other_revision, target_kind='lesson', lesson_revision=neighbor_revision, position=2)
        publish(other_revision, other_module)
        response = self.client.get('/lessons/first-lesson/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'second-neighbor/')
        self.assertNotContains(response, 'rel="prev"')
        self.assertNotContains(response, 'rel="next"')

    def test_navigation_never_uses_a_stale_module_revision(self):
        _, target_revision = self.lessons[1]
        old_revision = ModuleRevision.objects.create(module=self.module, revision_number=2, title='Old sequence')
        current_revision = ModuleRevision.objects.create(module=self.module, revision_number=3, title='Current sequence')
        old_neighbor = Lesson.objects.create(slug='stale-next')
        old_neighbor_revision = LessonRevision.objects.create(
            lesson=old_neighbor, revision_number=1, title='Stale next',
            blocks=[{'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                     'payload': {'text': 'Stale next'}}],
        )
        current_neighbor = Lesson.objects.create(slug='current-next')
        current_neighbor_revision = LessonRevision.objects.create(
            lesson=current_neighbor, revision_number=1, title='Current next',
            blocks=[{'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                     'payload': {'text': 'Current next'}}],
        )
        publish(old_neighbor_revision, old_neighbor)
        publish(current_neighbor_revision, current_neighbor)
        for module_revision, neighbor_revision in (
            (old_revision, old_neighbor_revision),
            (current_revision, current_neighbor_revision),
        ):
            ModuleLearningRequirement.objects.create(
                module_revision=module_revision, target_kind='lesson',
                lesson_revision=target_revision, position=1,
            )
            ModuleLearningRequirement.objects.create(
                module_revision=module_revision, target_kind='lesson',
                lesson_revision=neighbor_revision, position=2,
            )
        publish(old_revision, self.module)
        publish(current_revision, self.module)
        response = self.client.get('/lessons/first-lesson/?module=saving-module')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'current-next/')
        self.assertNotContains(response, 'stale-next/')

    def test_malformed_stored_lesson_blocks_fail_closed_against_model_contract(self):
        _, revision = self.lessons[1]
        valid = {'key': str(uuid.uuid4()), 'type': 'paragraph', 'position': 0,
                 'payload': {'text': 'Should not be rendered'}}
        malformed = [
            {k: v for k, v in valid.items() if k != 'key'},
            {**valid, 'key': 'not-a-uuid'},
            {k: v for k, v in valid.items() if k != 'type'},
            {**valid, 'type': 'heading'},
            {k: v for k, v in valid.items() if k != 'position'},
            {**valid, 'position': True},
            {**valid, 'position': -1},
            {**valid, 'position': '0'},
            {**valid, 'payload': {'text': '<script>bad()</script>', 'extra': 'field'}},
            {**valid, 'payload': {}},
            {**valid, 'payload': {'text': ''}},
            {**valid, 'payload': {'text': 12}},
            {**valid, 'unexpected': 'field'},
            [valid, {**valid, 'key': str(uuid.uuid4()), 'position': 0}],
            [valid, {**valid, 'key': valid['key'], 'position': 1}],
        ]
        for blocks in malformed:
            with self.subTest(blocks=blocks):
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE content_lessonrevision SET blocks = %s WHERE id = %s',
                        [json.dumps([blocks] if isinstance(blocks, dict) else blocks), revision.pk],
                    )
                response = self.client.get('/lessons/first-lesson/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'temporarily unavailable')
                self.assertNotContains(response, 'Should not be rendered')
                self.assertNotContains(response, '<script>bad()')

    def test_missing_and_malformed_routes_are_safe_404s(self):
        for path in ('/playbooks/missing/', '/modules/missing/', '/lessons/missing/', '/lessons/%3Cscript%3E/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


class EmptyPublicTests(TestCase):
    def test_empty_home_and_catalog_pages_are_graceful(self):
        for path, expected in [('/', 'no published Playbooks'), ('/playbooks/', 'no published Playbooks'), ('/modules/', 'no published Modules')]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
