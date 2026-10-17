from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from content.models import (EditorialReview, Lesson, LessonRevision, MediaAsset, Module,
    ModuleRevision, ModuleLearningRequirement, Playbook, PlaybookRevision,
    PlaybookModuleRecommendation, PublicationEvent, RelatedContentRelationship,
    Source, SourceSnapshot)

class EditorialIntegrityTests(TestCase):
    def test_published_pointer_requires_governed_service(self):
        playbook=Playbook.objects.create(slug='pointer-guard')
        revision=PlaybookRevision.objects.create(playbook=playbook,revision_number=1,title='Pointer')
        playbook.current_published_revision=revision
        with self.assertRaises(ValidationError):
            playbook.save(update_fields=['current_published_revision','updated_at'])

    def test_draft_revision_and_owned_records_remain_editable(self):
        module=Module.objects.create(slug='draft-editable')
        revision=ModuleRevision.objects.create(module=module,revision_number=1,title='Draft')
        revision.title='Draft edited'
        revision.save()
        lesson=Lesson.objects.create(slug='draft-target')
        target=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Lesson')
        requirement=ModuleLearningRequirement.objects.create(module_revision=revision,target_kind='lesson',lesson_revision=target,position=1)
        requirement.position=2
        requirement.save()
        self.assertEqual(ModuleLearningRequirement.objects.get(pk=requirement.pk).position,2)

    def test_reviewed_revision_and_revision_owned_records_are_immutable(self):
        module=Module.objects.create(slug='reviewed')
        revision=ModuleRevision.objects.create(module=module,revision_number=1,title='Reviewed')
        lesson=Lesson.objects.create(slug='reviewed-target')
        target=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Lesson')
        requirement=ModuleLearningRequirement.objects.create(module_revision=revision,target_kind='lesson',lesson_revision=target,position=1)
        revision.status='in_review'
        with self.assertRaises(ValidationError):
            revision.save(update_fields=['status'])
        revision._allow_lifecycle_transition=True
        revision.save(update_fields=['status'])
        revision.title='Silently changed'
        with self.assertRaises(ValidationError):
            revision.save()
        with self.assertRaises(ValidationError):
            revision.delete()
        with self.assertRaises(ValidationError):
            ModuleRevision.objects.filter(pk=revision.pk).update(title='Bulk mutation')
        requirement.position=2
        with self.assertRaises(ValidationError):
            requirement.save()
        with self.assertRaises(ValidationError):
            requirement.delete()

    def test_revision_sequence_is_unique_per_identity(self):
        lesson=Lesson.objects.create(slug='money-basics')
        LessonRevision.objects.create(lesson=lesson,revision_number=1,title='First')
        with self.assertRaises(ValidationError):
            LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Duplicate')
    def test_requirement_kind_must_match_exact_revision_foreign_key(self):
        module=Module.objects.create(slug='module-one')
        module_revision=ModuleRevision.objects.create(module=module,revision_number=1,title='One')
        lesson=Lesson.objects.create(slug='lesson-one')
        lesson_revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Lesson')
        with self.assertRaises(ValidationError):
            ModuleLearningRequirement.objects.create(module_revision=module_revision,target_kind='practice',lesson_revision=lesson_revision,position=1)
    def test_playbook_recommendation_membership_is_unique(self):
        playbook=Playbook.objects.create(slug='saving')
        playbook_revision=PlaybookRevision.objects.create(playbook=playbook,revision_number=1,title='Saving')
        module=Module.objects.create(slug='saving-module')
        module_revision=ModuleRevision.objects.create(module=module,revision_number=1,title='Saving')
        PlaybookModuleRecommendation.objects.create(playbook_revision=playbook_revision,module_revision=module_revision,position=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlaybookModuleRecommendation.objects.create(playbook_revision=playbook_revision,module_revision=module_revision,position=2)

    def test_reviewed_historical_relationship_cannot_be_bulk_changed_or_removed(self):
        playbook=Playbook.objects.create(slug='history-links')
        revision=PlaybookRevision.objects.create(playbook=playbook,revision_number=1,title='History')
        module=Module.objects.create(slug='history-module')
        target=ModuleRevision.objects.create(module=module,revision_number=1,title='Target')
        relation=PlaybookModuleRecommendation.objects.create(playbook_revision=revision,module_revision=target,position=1)
        revision.status='in_review'; revision._allow_lifecycle_transition=True; revision.save(); revision._allow_lifecycle_transition=False
        with self.assertRaises(ValidationError):
            PlaybookModuleRecommendation.objects.filter(pk=relation.pk).update(position=2)
        with self.assertRaises(ValidationError):
            PlaybookModuleRecommendation.objects.filter(pk=relation.pk).delete()
        self.assertEqual(PlaybookModuleRecommendation.objects.get(pk=relation.pk).module_revision_id,target.pk)

    def test_revision_owned_record_cannot_be_reparented_out_of_reviewed_revision(self):
        module = Module.objects.create(slug='reparent')
        reviewed = ModuleRevision.objects.create(module=module, revision_number=1, title='Reviewed')
        draft = ModuleRevision.objects.create(module=module, revision_number=2, title='Draft')
        target = LessonRevision.objects.create(lesson=Lesson.objects.create(slug='reparent-lesson'), revision_number=1, title='Lesson')
        record = ModuleLearningRequirement.objects.create(module_revision=reviewed, target_kind='lesson', lesson_revision=target, position=1)
        record.position = 2
        record.save()
        reviewed.status = 'published'; reviewed._allow_lifecycle_transition = True; reviewed.save(update_fields=['status']); reviewed._allow_lifecycle_transition = False
        record.module_revision = draft
        with self.assertRaises(ValidationError): record.save()
        record.position = 3
        with self.assertRaises(ValidationError): record.save()
        with self.assertRaises(ValidationError): record.delete()
        with self.assertRaises(ValidationError): type(record).objects.filter(pk=record.pk).update(module_revision=draft)
        self.assertEqual(ModuleLearningRequirement.objects.get(pk=record.pk).module_revision_id, reviewed.pk)

    def test_requirement_classification_allow_list(self):
        module = Module.objects.create(slug='classification')
        parent = ModuleRevision.objects.create(module=module, revision_number=1, title='Classifications')
        lesson = LessonRevision.objects.create(lesson=Lesson.objects.create(slug='classification-lesson'), revision_number=1, title='Lesson')
        for position, value in enumerate(('required', 'optional', 'recommended'), 1):
            target = LessonRevision.objects.create(lesson=Lesson.objects.create(slug=f'classification-lesson-{position}'), revision_number=1, title='Lesson')
            ModuleLearningRequirement.objects.create(module_revision=parent, target_kind='lesson', lesson_revision=target, classification=value, position=position)
        invalid = ModuleLearningRequirement(module_revision=parent, target_kind='lesson', lesson_revision=lesson, classification='blocking', position=4)
        with self.assertRaises(ValidationError): invalid.full_clean()
        with self.assertRaises(ValidationError): invalid.save()

    def test_lesson_block_allow_list_and_validation(self):
        lesson = Lesson.objects.create(slug='block-validation')
        valid = [{'key': '00000000-0000-0000-0000-000000000001', 'type': 'paragraph', 'position': 0, 'payload': {'text': 'A paragraph.'}}]
        revision = LessonRevision.objects.create(lesson=lesson, revision_number=1, title='Valid', blocks=valid)
        self.assertEqual(revision.blocks, valid)
        invalid_payloads = [
            ['not an object'],
            [{'key': '00000000-0000-0000-0000-000000000002', 'type': 'unknown', 'position': 0, 'payload': {'text': 'x'}}],
            [{'key': '00000000-0000-0000-0000-000000000003', 'type': 'paragraph', 'position': 0}],
            [{'key': '00000000-0000-0000-0000-000000000004', 'type': 'paragraph', 'position': 0, 'payload': {'text': {'nested': 'not text'}}}],
            [{'key': '00000000-0000-0000-0000-000000000005', 'type': 'paragraph', 'position': 0, 'payload': {'text': 'x', 'html': '<b>x</b>'}}],
            [{'key': 'not-a-uuid', 'type': 'paragraph', 'position': 0, 'payload': {'text': 'x'}}],
            [{'key': '00000000-0000-0000-0000-000000000006', 'type': 'paragraph', 'position': -1, 'payload': {'text': 'x'}}],
        ]
        for idx, blocks in enumerate(invalid_payloads, 2):
            with self.subTest(blocks=blocks), self.assertRaises(ValidationError):
                LessonRevision.objects.create(lesson=lesson, revision_number=idx, title='Invalid', blocks=blocks)

    def test_publication_and_review_events_are_append_only_through_queryset(self):
        from django.contrib.auth import get_user_model
        user=get_user_model().objects.create_user('event@example.com','strong-password-123')
        lesson=Lesson.objects.create(slug='event-target')
        revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Event')
        review=EditorialReview.objects.create(content_kind='lesson',lesson_revision=revision,reviewer=user,role_snapshot='Reviewer',action='reviewed')
        event=PublicationEvent.objects.create(content_kind='lesson',lesson_revision=revision,actor=user,role_snapshot='Publisher',action='published')
        for model, obj in ((EditorialReview,review),(PublicationEvent,event)):
            with self.assertRaises(ValidationError): model.objects.filter(pk=obj.pk).update(action='rewritten')
            with self.assertRaises(ValidationError): model.objects.filter(pk=obj.pk).delete()
            with self.assertRaises(ValidationError): obj.delete()

    def test_source_snapshot_survives_mutable_source_catalog_changes(self):
        from django.contrib.auth import get_user_model
        user=get_user_model().objects.create_user('source-reviewer@example.com','strong-password-123')
        source=Source.objects.create(source_key='central-bank-guide',title='Original title',url_or_reference='ref:original',version_reference='v1')
        lesson=Lesson.objects.create(slug='sourced-lesson')
        revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Sourced')
        reviewed=timezone.now()
        snapshot=SourceSnapshot.objects.create(source=source,content_kind='lesson',lesson_revision=revision,
            reviewed_at=reviewed,reviewer=user,retrieved_at=reviewed)
        source.source_key='updated-key'; source.title='Changed'; source.url_or_reference='ref:changed'; source.version_reference='v2'; source.save()
        snapshot.refresh_from_db()
        self.assertEqual((snapshot.source_identity_snapshot,snapshot.title_snapshot,snapshot.url_snapshot,snapshot.version_snapshot),
            ('central-bank-guide','Original title','ref:original','v1'))
        self.assertEqual(snapshot.retrieved_at,reviewed)
        self.assertEqual(snapshot.reviewer_id,user.pk)

    def test_media_asset_is_immutable_version_and_protected_when_referenced(self):
        asset=MediaAsset.objects.create(asset_key='opaque-v1',media_kind='image',mime_type='image/png',byte_size=12,checksum='sha256:abc',rights_metadata={'attribution':'editorial source'})
        playbook=Playbook.objects.create(slug='media-owner')
        revision=PlaybookRevision.objects.create(playbook=playbook,revision_number=1,title='Media',cover_asset=asset)
        asset.checksum='sha256:changed'
        with self.assertRaises(ValidationError): asset.save()
        with self.assertRaises(ValidationError): MediaAsset.objects.filter(pk=asset.pk).update(checksum='sha256:changed')
        with self.assertRaises(Exception): asset.delete()
        with self.assertRaises(Exception): MediaAsset.objects.filter(pk=asset.pk).delete()
        self.assertEqual(PlaybookRevision.objects.get(pk=revision.pk).cover_asset_id,asset.pk)

class EditorialGovernanceTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        User=get_user_model()
        self.author=User.objects.create_user('author@example.com','strong-password-123',is_staff=True)
        self.approver=User.objects.create_user('approver@example.com','strong-password-123',is_staff=True)
        self.reviewer=User.objects.create_user('reviewer@example.com','strong-password-123',is_staff=True)
        self.author.is_verified=lambda: True
        self.approver.is_verified=lambda: True
        self.reviewer.is_verified=lambda: True
        author_role,_=Group.objects.get_or_create(name='Author/Editor')
        approver_role,_=Group.objects.get_or_create(name='Approver/Publisher')
        reviewer_role,_=Group.objects.get_or_create(name='Reviewer')
        self.author.groups.add(author_role)
        self.approver.groups.add(approver_role)
        self.reviewer.groups.add(reviewer_role)
        playbook=Playbook.objects.create(slug='governed')
        self.revision=PlaybookRevision.objects.create(playbook=playbook,revision_number=1,title='Governed',author=self.author)
    def test_distinct_mfa_verified_approver_publishes_exact_revision(self):
        from content.services import submit_for_review, review_revision, approve_and_publish
        submit_for_review(revision=self.revision,actor=self.author)
        review = review_revision(revision=self.revision, actor=self.reviewer)
        approve_and_publish(revision=self.revision,actor=self.approver)
        self.revision.refresh_from_db()
        self.assertEqual(self.revision.status,'published')
        self.assertEqual(self.revision.playbook.current_published_revision_id,self.revision.pk)
        from discovery.models import SearchProjection
        self.assertTrue(SearchProjection.objects.filter(playbook_revision=self.revision).exists())
        self.assertTrue(EditorialReview.objects.filter(pk=review.pk, action='reviewed', playbook_revision=self.revision).exists())
    def test_publication_without_review_fails(self):
        from content.services import submit_for_review, approve_and_publish
        submit_for_review(revision=self.revision, actor=self.author)
        with self.assertRaises(ValidationError): approve_and_publish(revision=self.revision, actor=self.approver)
    def test_review_of_other_revision_does_not_authorize_publication(self):
        from content.services import submit_for_review, review_revision, approve_and_publish
        from django.core.exceptions import ValidationError
        submit_for_review(revision=self.revision, actor=self.author)
        other = PlaybookRevision.objects.create(playbook=self.revision.playbook, revision_number=2, title='Other', author=self.author)
        submit_for_review(revision=other, actor=self.author)
        review_revision(revision=other, actor=self.reviewer)
        with self.assertRaises(ValidationError): approve_and_publish(revision=self.revision, actor=self.approver)
    def test_reviewer_and_approver_must_differ(self):
        from content.services import submit_for_review, review_revision, approve_and_publish
        from django.core.exceptions import PermissionDenied
        submit_for_review(revision=self.revision, actor=self.author)
        review_revision(revision=self.revision, actor=self.reviewer)
        self.reviewer.groups.add(self.approver.groups.get(name='Approver/Publisher'))
        with self.assertRaises(PermissionDenied): approve_and_publish(revision=self.revision, actor=self.reviewer)
    def test_staff_without_verified_otp_cannot_submit(self):
        from content.services import submit_for_review
        self.author.is_verified=lambda: False
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            submit_for_review(revision=self.revision,actor=self.author)
    def test_same_person_cannot_approve_own_revision(self):
        from content.services import submit_for_review, approve_and_publish
        from django.core.exceptions import PermissionDenied
        submit_for_review(revision=self.revision,actor=self.author)
        self.author.groups.add(self.approver.groups.get(name='Approver/Publisher'))
        with self.assertRaises(PermissionDenied):
            approve_and_publish(revision=self.revision,actor=self.author)


    def test_related_content_kind_uses_exact_foreign_key_target(self):
        lesson=Lesson.objects.create(slug='related-lesson')
        revision=LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Related')
        with self.assertRaises(IntegrityError), transaction.atomic():
            RelatedContentRelationship.objects.create(source_kind='lesson',source_lesson=revision,target_kind='module',target_lesson=revision,relationship_kind='related')
