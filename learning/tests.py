from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from content.models import Lesson, LessonRevision
from learning.models import LearningJourney
from learning.services import create_note, owned_notes
from content.models import Module, ModuleRevision, ModuleLearningRequirement, PracticeActivity, PracticeActivityRevision
from practice.services import create_attempt, submit_attempt
from learning.models import RequirementEvidence

User = get_user_model()

class NoteOwnershipIsolationTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user('alice@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.bob = User.objects.create_user('bob@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        lesson = Lesson.objects.create(slug='sample')
        self.revision = LessonRevision.objects.create(lesson=lesson,revision_number=1,title='Sample',blocks=[{'key':'00000000-0000-0000-0000-000000000001','type':'paragraph','position':0,'payload':{'text':'A quote.'}}])
        self.journey = LearningJourney.objects.create(owner=self.alice)
    def test_note_lists_are_owner_scoped(self):
        note=create_note(user=self.alice,kind='note',body='Private',lesson_revision=self.revision)
        self.assertEqual(list(owned_notes(self.alice)),[note])
        self.assertFalse(owned_notes(self.bob).exists())
    def test_foreign_journey_attachment_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            create_note(user=self.bob,kind='note',body='No',journey=self.journey)
    def test_highlight_requires_exact_block_and_quote(self):
        with self.assertRaises(ValidationError):
            create_note(user=self.alice,kind='highlight',lesson_revision=self.revision,block_key='00000000-0000-0000-0000-000000000001',anchor_data={'selected_quote':''})
        note=create_note(user=self.alice,kind='highlight',lesson_revision=self.revision,block_key='00000000-0000-0000-0000-000000000001',anchor_data={'selected_quote':'A quote.'})
        self.assertEqual(note.lesson_revision_id,self.revision.pk)
        self.assertEqual(note.block_key,'00000000-0000-0000-0000-000000000001')
    def test_highlight_rejects_missing_block_or_quote(self):
        with self.assertRaises(ValidationError):
            create_note(user=self.alice,kind='highlight',lesson_revision=self.revision,block_key='missing',anchor_data={'selected_quote':'A quote.'})
        with self.assertRaises(ValidationError):
            create_note(user=self.alice,kind='highlight',lesson_revision=self.revision,block_key='00000000-0000-0000-0000-000000000001',anchor_data={'selected_quote':'not present'})
    def test_offsets_are_hints_and_must_be_well_formed(self):
        with self.assertRaises(ValidationError):
            create_note(user=self.alice,kind='highlight',lesson_revision=self.revision,block_key='00000000-0000-0000-0000-000000000001',anchor_data={'selected_quote':'A quote.','start_offset':9,'end_offset':2})

class RequirementEvidenceImmutabilityTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('evidence@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        module=Module.objects.create(slug='evidence-module')
        self.module_revision=ModuleRevision.objects.create(module=module,revision_number=1,title='Evidence')
        activity=PracticeActivity.objects.create(slug='evidence-activity')
        self.practice_revision=PracticeActivityRevision.objects.create(activity=activity,revision_number=1,title='Activity',response_schema={'schema_version':1,'questions':[]})
        self.requirement=ModuleLearningRequirement.objects.create(module_revision=self.module_revision,target_kind='practice',practice_revision=self.practice_revision,position=1)
        self.attempt=create_attempt(user=self.owner,practice_revision=self.practice_revision)
        submit_attempt(user=self.owner,attempt_id=self.attempt.pk)

    def test_accepted_attempt_satisfies_one_requirement_and_evidence_is_immutable(self):
        from learning.services import record_requirement_evidence
        evidence=record_requirement_evidence(user=self.owner,module_revision=self.module_revision,requirement=self.requirement,attempt=self.attempt)
        self.assertEqual(evidence.state,'accepted')
        with self.assertRaises(ValidationError):
            RequirementEvidence.objects.filter(pk=evidence.pk).update(state='rejected')
        with self.assertRaises(ValidationError):
            RequirementEvidence.objects.filter(pk=evidence.pk).delete()
        evidence.refresh_from_db()
        self.assertEqual(evidence.state,'accepted')

    def test_one_accepted_attempt_cannot_satisfy_a_second_requirement(self):
        from learning.services import record_requirement_evidence
        record_requirement_evidence(user=self.owner,module_revision=self.module_revision,requirement=self.requirement,attempt=self.attempt)
        other_module=Module.objects.create(slug='second-evidence-module')
        other_revision=ModuleRevision.objects.create(module=other_module,revision_number=1,title='Second')
        other_requirement=ModuleLearningRequirement.objects.create(module_revision=other_revision,target_kind='practice',practice_revision=self.practice_revision,position=1)
        with self.assertRaises(ValidationError):
            record_requirement_evidence(user=self.owner,module_revision=other_revision,requirement=other_requirement,attempt=self.attempt)

    def test_evidence_cannot_be_assigned_to_another_owner(self):
        with self.assertRaises(ValidationError):
            RequirementEvidence.objects.create(owner=User.objects.create_user('other@example.com','strong-password-123'),
                module_revision=self.module_revision,requirement=self.requirement,practice_revision=self.practice_revision,
                attempt=self.attempt,state='accepted')
