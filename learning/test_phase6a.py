from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from content.models import Module, ModuleRevision, ModuleLearningRequirement, PracticeActivity, PracticeActivityRevision
from practice.models import PracticeAttempt
from practice.services import submit_attempt
from learning.models import LearningJourney, RequirementEvidence
from learning.services import append_journey_step, evaluate_module_completion, record_requirement_evidence

User = get_user_model()

class Phase6AJourneyIntegrityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('journey@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.other = User.objects.create_user('other-journey@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.journey = LearningJourney.objects.create(owner=self.owner)
        activity = PracticeActivity.objects.create(slug='journey-practice')
        self.revision = PracticeActivityRevision.objects.create(activity=activity, revision_number=1, title='Practice',response_schema={'schema_version':1,'questions':[]})

    def _attempt(self, owner=None):
        return PracticeAttempt.objects.create(owner=owner or self.owner, practice_revision=self.revision)

    def test_valid_targets_append_in_deterministic_order(self):
        first = append_journey_step(user=self.owner, journey=self.journey, target_kind='practice', target=self.revision, step_type='read')
        attempt = self._attempt()
        second = append_journey_step(user=self.owner, journey=self.journey, target_kind='attempt', target=attempt, step_type='practice')
        self.assertEqual((first.sequence, second.sequence), (1, 2))
        self.assertEqual(list(self.journey.steps.values_list('sequence', flat=True)), [1, 2])

    def test_wrong_target_kind_and_mismatched_target_rejected(self):
        with self.assertRaises(ValidationError):
            append_journey_step(user=self.owner, journey=self.journey, target_kind='module', target=self.revision, step_type='read')

    def test_private_target_from_other_owner_rejected(self):
        with self.assertRaises(PermissionDenied):
            append_journey_step(user=self.owner, journey=self.journey, target_kind='attempt', target=self._attempt(self.other), step_type='practice')

    def test_step_cannot_be_mutated_or_deleted(self):
        step = append_journey_step(user=self.owner, journey=self.journey, target_kind='practice', target=self.revision, step_type='read')
        linked_target = step.target_ref.practice_target
        linked_target.target = PracticeActivityRevision.objects.create(activity=self.revision.activity, revision_number=2, title='Later practice',response_schema={'schema_version':1,'questions':[]})
        with self.assertRaises(ValidationError):
            linked_target.save()
        registry = step.target_ref
        registry.target_kind = 'lesson'
        with self.assertRaises(ValidationError):
            registry.save()
        linked_target.refresh_from_db()
        registry.refresh_from_db()
        self.assertEqual(step.target_ref.practice_target.target_id, self.revision.pk)
        step.state = 'done'
        with self.assertRaises(ValidationError):
            step.save()
        with self.assertRaises(ValidationError):
            step.delete()
        with self.assertRaises(ValidationError):
            type(step).objects.filter(pk=step.pk).update(state='done')

class Phase6AEvidenceAndCompletionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('evidence@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.other = User.objects.create_user('other-evidence@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        self.module = Module.objects.create(slug='evidence-module')
        self.module_revision = ModuleRevision.objects.create(module=self.module, revision_number=1, title='Module')
        self.module_revision_2 = ModuleRevision.objects.create(module=self.module, revision_number=2, title='Module v2')
        self.activity = PracticeActivity.objects.create(slug='evidence-practice')
        self.practice_revision = PracticeActivityRevision.objects.create(activity=self.activity, revision_number=1, title='Practice',response_schema={'schema_version':1,'questions':[]})
        self.other_practice_revision = PracticeActivityRevision.objects.create(activity=self.activity, revision_number=2, title='Practice v2',response_schema={'schema_version':1,'questions':[]})
        self.recommended_practice_revision = PracticeActivityRevision.objects.create(activity=self.activity, revision_number=3, title='Practice v3',response_schema={'schema_version':1,'questions':[]})
        self.required = ModuleLearningRequirement.objects.create(module_revision=self.module_revision, target_kind='practice', practice_revision=self.practice_revision, classification='required', position=1)
        self.optional = ModuleLearningRequirement.objects.create(module_revision=self.module_revision, target_kind='practice', practice_revision=self.other_practice_revision, classification='optional', position=2)
        self.recommended = ModuleLearningRequirement.objects.create(module_revision=self.module_revision, target_kind='practice', practice_revision=self.recommended_practice_revision, classification='recommended', position=3)
        self.attempt = self._submitted(self.owner, self.practice_revision)

    def _submitted(self, owner, revision):
        attempt = PracticeAttempt.objects.create(owner=owner, practice_revision=revision)
        return submit_attempt(user=owner, attempt_id=attempt.pk, response_summary={'answer': 'submitted'})

    def _evidence(self, *, owner=None, module_revision=None, requirement=None, practice_revision=None, attempt=None):
        return RequirementEvidence(owner=owner or self.owner, module_revision=module_revision or self.module_revision,
            requirement=requirement or self.required, practice_revision=practice_revision or self.practice_revision,
            attempt=attempt or self.attempt, state='accepted', evaluated_at=timezone.now())

    def test_valid_exact_submitted_evidence(self):
        evidence = record_requirement_evidence(user=self.owner, module_revision=self.module_revision, requirement=self.required, attempt=self.attempt)
        self.assertEqual(evidence.practice_revision_id, self.practice_revision.pk)

    def test_wrong_revision_requirement_practice_attempt_and_owner_rejected(self):
        cases = [
            self._evidence(module_revision=self.module_revision_2),
            self._evidence(requirement=self.optional),
            self._evidence(practice_revision=self.other_practice_revision),
            self._evidence(attempt=self._submitted(self.owner, self.other_practice_revision)),
            self._evidence(owner=self.other),
        ]
        for evidence in cases:
            with self.subTest(evidence=evidence):
                with self.assertRaises(ValidationError):
                    evidence.full_clean()

    def test_unsubmitted_attempt_is_not_evidence(self):
        attempt = PracticeAttempt.objects.create(owner=self.owner, practice_revision=self.practice_revision)
        with self.assertRaises(ValidationError):
            self._evidence(attempt=attempt).full_clean()

    def test_one_accepted_attempt_cannot_credit_another_requirement(self):
        record_requirement_evidence(user=self.owner, module_revision=self.module_revision, requirement=self.required, attempt=self.attempt)
        with self.assertRaises(ValidationError):
            record_requirement_evidence(user=self.owner, module_revision=self.module_revision, requirement=self.optional, attempt=self.attempt)

    def test_module_completion_exact_required_set_only(self):
        missing = evaluate_module_completion(user=self.owner, module_revision=self.module_revision)
        self.assertEqual(missing.outcome, 'incomplete')
        record_requirement_evidence(user=self.owner, module_revision=self.module_revision, requirement=self.required, attempt=self.attempt)
        complete = evaluate_module_completion(user=self.owner, module_revision=self.module_revision)
        self.assertEqual(complete.outcome, 'complete')
        self.assertEqual(len(complete.evidence_snapshot['requirements']), 3)
        self.assertFalse(complete.evidence_snapshot['requirements'][1]['satisfied'])
        self.assertFalse(complete.evidence_snapshot['requirements'][2]['satisfied'])

    def test_evidence_from_another_module_revision_does_not_count(self):
        other_req = ModuleLearningRequirement.objects.create(module_revision=self.module_revision_2, target_kind='practice', practice_revision=self.practice_revision, classification='required', position=1)
        evidence = record_requirement_evidence(user=self.owner, module_revision=self.module_revision_2, requirement=other_req, attempt=self.attempt)
        self.assertEqual(evidence.module_revision_id, self.module_revision_2.pk)
        self.assertEqual(evaluate_module_completion(user=self.owner, module_revision=self.module_revision).outcome, 'incomplete')

    def test_completion_snapshot_cannot_be_fabricated_or_changed(self):
        with self.assertRaises(ValidationError):
            from learning.models import ModuleCompletion
            ModuleCompletion.objects.create(owner=self.owner, module_revision=self.module_revision, outcome='complete', evidence_snapshot={'module_revision_id': self.module_revision.pk, 'requirements': [], 'complete': True})
