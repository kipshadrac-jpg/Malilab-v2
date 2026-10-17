from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from content.models import Module, ModuleLearningRequirement, ModuleRevision, PracticeActivity, PracticeActivityRevision
from practice.services import create_attempt, submit_attempt
from .evaluation import evaluate_attempt, pending_attempts
from .models import RequirementEvidence

User = get_user_model()


def make_staff(email, *, mfa=True, role=True):
    user = User.objects.create_user(email, 'strong-password-123', is_staff=True)
    if role:
        group, _ = Group.objects.get_or_create(name='Reviewer')
        user.groups.add(group)
    user.is_verified = (lambda: mfa)
    return user


class EvaluationServiceTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user('learner@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())
        module = Module.objects.create(slug='eval-module')
        self.module_revision = ModuleRevision.objects.create(module=module, revision_number=1, title='Eval module')
        activity = PracticeActivity.objects.create(slug='eval-activity')
        self.practice = PracticeActivityRevision.objects.create(activity=activity, revision_number=1, title='Eval practice', response_schema={'schema_version': 1, 'questions': []})
        self.requirement = ModuleLearningRequirement.objects.create(module_revision=self.module_revision, target_kind='practice', practice_revision=self.practice, position=1)
        self.attempt = create_attempt(user=self.learner, practice_revision=self.practice)
        submit_attempt(user=self.learner, attempt_id=self.attempt.pk)
        self.staff = make_staff('staff@example.com')

    def test_submission_alone_creates_no_evidence_and_is_pending(self):
        self.assertFalse(RequirementEvidence.objects.exists())
        self.assertEqual(list(pending_attempts()), [self.attempt])

    def test_staff_acceptance_creates_evidence_for_learner_and_leaves_queue(self):
        ev = evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='accepted', note='ok')
        self.assertEqual((ev.owner_id, ev.state, ev.attempt_id), (self.learner.pk, 'accepted', self.attempt.pk))
        self.assertEqual(ev.evaluation_context['evaluator_id'], self.staff.pk)
        self.assertEqual(list(pending_attempts()), [])

    def test_learner_and_unverified_or_roleless_staff_cannot_evaluate(self):
        for actor in (self.learner, make_staff('nomfa@example.com', mfa=False), make_staff('norole@example.com', role=False)):
            with self.assertRaises(PermissionDenied):
                evaluate_attempt(evaluator=actor, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='accepted')
        self.assertFalse(RequirementEvidence.objects.exists())

    def test_cannot_evaluate_twice_or_with_bad_decision(self):
        evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='rejected')
        with self.assertRaises(ValidationError):
            evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='accepted')
        with self.assertRaises(ValidationError):
            evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='maybe')

    def test_started_attempt_cannot_be_evaluated(self):
        started = create_attempt(user=self.learner, practice_revision=self.practice)
        with self.assertRaises(ValidationError):
            evaluate_attempt(evaluator=self.staff, attempt_id=started.pk, requirement_id=self.requirement.pk, decision='accepted')

    def test_accepted_evidence_completes_module(self):
        from .services import evaluate_module_completion
        evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='accepted')
        self.assertEqual(evaluate_module_completion(user=self.learner, module_revision=self.module_revision).outcome, 'complete')

    def test_rejected_evidence_does_not_complete_module(self):
        from .services import evaluate_module_completion
        evaluate_attempt(evaluator=self.staff, attempt_id=self.attempt.pk, requirement_id=self.requirement.pk, decision='rejected')
        self.assertEqual(evaluate_module_completion(user=self.learner, module_revision=self.module_revision).outcome, 'incomplete')


class EvaluationRouteTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user('l2@example.com', 'strong-password-123', email_verified=True, email_verified_at=timezone.now())

    def test_routes_are_hidden_from_anonymous_and_learners(self):
        self.assertEqual(self.client.get('/staff/evaluations/').status_code, 404)
        self.client.force_login(self.learner)
        self.assertEqual(self.client.get('/staff/evaluations/').status_code, 404)
        self.assertEqual(self.client.get('/staff/evaluations/1/').status_code, 404)

    def test_mfa_reviewer_sees_queue(self):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        staff = User.objects.create_user('rev@example.com', 'strong-password-123', is_staff=True)
        staff.groups.add(Group.objects.get_or_create(name='Reviewer')[0])
        device = TOTPDevice.objects.create(user=staff, name='test', confirmed=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/staff/evaluations/').status_code, 404)  # logged in but no MFA yet
        session = self.client.session
        session['otp_device_id'] = device.persistent_id
        session.save()
        response = self.client.get('/staff/evaluations/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Practice evaluations')
