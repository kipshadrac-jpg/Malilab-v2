"""End-to-end learner journey across slices 6B.1-6B.10, using the real routes and staff screens.

Content is authored/published through the governance services (three different staff),
then a learner reads, practises, is evaluated by staff, completes the Module, takes notes,
writes a plan and finds content by search.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.utils import timezone

from content.models import (Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision,
                            Playbook, PlaybookModuleRecommendation, PlaybookRevision,
                            PracticeActivity, PracticeActivityRevision)
from content.services import ROLE_GROUPS, approve_and_publish, review_revision, submit_for_review
from content.test_admin import staff_client
from learning.models import ModuleCompletion, Note, RequirementEvidence
from planning.models import MyPlan
from practice.models import PracticeAttempt

User = get_user_model()
KEY = '00000000-0000-0000-0000-0000000000b1'
LESSON_TEXT = 'A sacco is a member-owned savings and credit society.'


def staff(email, role):
    user = User.objects.create_user(email, 'strong-password-123', is_staff=True)
    user.groups.add(Group.objects.get_or_create(name=ROLE_GROUPS[role])[0])
    user.is_verified = lambda: True
    return user


def learner(email):
    return User.objects.create_user(email, 'strong-password-123', email_verified=True, email_verified_at=timezone.now())


class FullLearnerJourneyTests(TestCase):
    def setUp(self):
        self.author = staff('j-author@example.com', 'author_editor')
        self.reviewer = staff('j-reviewer@example.com', 'reviewer')
        self.approver = staff('j-approver@example.com', 'approver_publisher')
        self.publish_all()

    def publish(self, rev):
        submit_for_review(revision=rev, actor=self.author)
        review_revision(revision=rev, actor=self.reviewer)
        approve_and_publish(revision=rev, actor=self.approver)
        rev.refresh_from_db()

    def publish_all(self):
        lesson = Lesson.objects.create(slug='sacco-basics')
        self.lesson_rev = LessonRevision.objects.create(
            lesson=lesson, revision_number=1, title='Sacco basics', summary='Intro to saccos', author=self.author,
            blocks=[{'key': KEY, 'type': 'paragraph', 'position': 0, 'payload': {'text': LESSON_TEXT}}])
        self.publish(self.lesson_rev)
        activity = PracticeActivity.objects.create(slug='sacco-budget')
        self.practice_rev = PracticeActivityRevision.objects.create(
            activity=activity, revision_number=1, title='Sacco budget practice', author=self.author,
            instructions='Think about your own situation.', prompt='What can you save?',
            response_schema={'schema_version': 1, 'questions': [
                {'id': 'monthly_saving', 'type': 'decimal_amount', 'label': 'Monthly saving', 'required': True, 'constraints': {'currency': 'KES'}},
                {'id': 'reason', 'type': 'short_text', 'label': 'Why?', 'required': True, 'constraints': {'max_length': 280}}]})
        self.publish(self.practice_rev)
        module = Module.objects.create(slug='saving-with-saccos')
        self.module_rev = ModuleRevision.objects.create(module=module, revision_number=1, title='Saving with saccos',
                                                         description='A first module.', author=self.author)
        self.req_practice = ModuleLearningRequirement.objects.create(
            module_revision=self.module_rev, target_kind='practice', practice_revision=self.practice_rev, classification='required', position=1)
        ModuleLearningRequirement.objects.create(
            module_revision=self.module_rev, target_kind='lesson', lesson_revision=self.lesson_rev, classification='recommended', position=2)
        self.publish(self.module_rev)
        playbook = Playbook.objects.create(slug='i-want-to-save')
        self.playbook_rev = PlaybookRevision.objects.create(playbook=playbook, revision_number=1, title='I want to start saving',
                                                             summary='Where do I begin?', scenario='You earn irregularly.', author=self.author)
        PlaybookModuleRecommendation.objects.create(playbook_revision=self.playbook_rev, module_revision=self.module_rev, position=1)
        self.publish(self.playbook_rev)

    # ------------------------------------------------------------------ public reading (6B.1-6B.3, 6B.10)
    def test_public_visitor_can_browse_read_and_search_but_not_practise(self):
        anon = Client()
        self.assertContains(anon.get('/playbooks/'), 'I want to start saving')
        self.assertContains(anon.get('/playbooks/i-want-to-save/'), 'Saving with saccos')
        module_page = anon.get('/modules/saving-with-saccos/')
        self.assertContains(module_page, 'Sacco basics')
        self.assertContains(anon.get('/lessons/sacco-basics/?module=saving-with-saccos'), LESSON_TEXT)
        self.assertContains(anon.get('/search/?q=sacco'), 'Sacco basics')
        self.assertContains(anon.get('/practice/sacco-budget/'), 'Sign in')
        start = anon.post('/practice/sacco-budget/attempts/')
        self.assertEqual(start.status_code, 302)
        self.assertIn('sign-in', start['Location'])
        self.assertFalse(PracticeAttempt.objects.exists())

    # ------------------------------------------------------------------ the whole learner path (6B.4-6B.9)
    def test_learner_practises_is_evaluated_completes_module_and_keeps_notes_and_plan(self):
        user = learner('journey-learner@example.com')
        c = Client(); c.force_login(user)

        # Practice: start, bad save keeps draft, good saves, incomplete submit refused, submit succeeds
        start = c.post('/practice/sacco-budget/attempts/')
        self.assertEqual(start.status_code, 302)
        attempt = PracticeAttempt.objects.get(owner=user)
        self.assertEqual(attempt.practice_revision_id, self.practice_rev.pk)
        self.assertEqual(c.get(f'/practice/attempts/{attempt.pk}/').status_code, 200)
        self.assertEqual(c.post(f'/practice/attempts/{attempt.pk}/responses/', {'question_id': 'monthly_saving', 'monthly_saving': '12.345'}).status_code, 400)
        self.assertEqual(attempt.responses.count(), 0)
        self.assertEqual(c.post(f'/practice/attempts/{attempt.pk}/responses/', {'question_id': 'monthly_saving', 'monthly_saving': '1500.50'}).status_code, 302)
        too_early = c.post(f'/practice/attempts/{attempt.pk}/submit/', {'monthly_saving': '1500.50'})
        self.assertEqual(too_early.status_code, 400)
        attempt.refresh_from_db(); self.assertEqual(attempt.state, 'started')
        self.assertEqual(attempt.responses.get().value, '1500.50')         # draft survived the failed submit
        c.post(f'/practice/attempts/{attempt.pk}/responses/', {'question_id': 'reason', 'reason': 'To build an emergency fund'})
        done = c.post(f'/practice/attempts/{attempt.pk}/submit/', {'monthly_saving': '1500.50', 'reason': 'To build an emergency fund'})
        self.assertEqual(done.status_code, 302)
        attempt.refresh_from_db(); self.assertEqual(attempt.state, 'submitted')

        # Submission alone is NOT evidence: Module stays incomplete
        c.post('/modules/saving-with-saccos/completion/')
        self.assertEqual(ModuleCompletion.objects.filter(owner=user).latest('evaluated_at').outcome, 'incomplete')
        self.assertFalse(RequirementEvidence.objects.exists())

        # Staff (real MFA path) evaluate and accept
        _, staff_c = staff_client('j-evaluator@example.com', 'reviewer')
        self.assertContains(staff_c.get('/staff/evaluations/'), 'Sacco budget practice')
        detail = staff_c.get(f'/staff/evaluations/{attempt.pk}/')
        self.assertContains(detail, '1500.50')
        accept = staff_c.post(f'/staff/evaluations/{attempt.pk}/', {'requirement': self.req_practice.pk, 'decision': 'accepted', 'note': 'Good'})
        self.assertEqual(accept.status_code, 302)
        evidence = RequirementEvidence.objects.get()
        self.assertEqual((evidence.owner_id, evidence.state), (user.pk, 'accepted'))

        # Module now completes; Progress shows the evidence and the completion
        c.post('/modules/saving-with-saccos/completion/')
        self.assertEqual(ModuleCompletion.objects.filter(owner=user).latest('evaluated_at').outcome, 'complete')
        progress = c.get('/progress/')
        self.assertContains(progress, 'Sacco budget practice')
        self.assertContains(progress, '· complete ·')

        # Notes stay pinned to the exact lesson revision and block
        note_resp = c.post('/lessons/sacco-basics/notes/', {'kind': 'highlight', 'body': 'Remember this', 'block_key': KEY, 'selected_quote': 'member-owned savings'})
        self.assertEqual(note_resp.status_code, 302)
        note = Note.objects.get(owner=user)
        self.assertEqual((note.lesson_revision_id, note.block_key), (self.lesson_rev.pk, KEY))
        self.assertContains(c.get(f'/notes/{note.pk}/source/'), LESSON_TEXT)

        # My Plan appends immutable revisions
        c.post('/my-plan/', {'target': 'Save 20,000 KES a month', 'assumptions': 'Stable income', 'strategy_path': 'Join a sacco'})
        plan = MyPlan.objects.get(owner=user)
        c.post(f'/my-plan/{plan.pk}/', {'target': 'Save 25,000 KES a month'})
        self.assertEqual(plan.revisions.count(), 2)
        self.assertEqual(plan.revisions.get(revision_number=1).target['text'], 'Save 20,000 KES a month')

        # Another learner sees none of it
        other = learner('journey-other@example.com')
        oc = Client(); oc.force_login(other)
        self.assertEqual(oc.get(f'/practice/attempts/{attempt.pk}/').status_code, 404)
        self.assertEqual(oc.get(f'/my-plan/{plan.pk}/').status_code, 404)
        self.assertEqual(oc.get(f'/notes/{note.pk}/source/').status_code, 404)
        self.assertNotContains(oc.get('/progress/'), 'Sacco budget practice')
        self.assertNotContains(oc.get('/notes/'), 'Remember this')

    # ------------------------------------------------------------------ rejection path
    def test_rejected_attempt_never_completes_the_module(self):
        user = learner('journey-rejected@example.com')
        c = Client(); c.force_login(user)
        c.post('/practice/sacco-budget/attempts/')
        attempt = PracticeAttempt.objects.get(owner=user)
        c.post(f'/practice/attempts/{attempt.pk}/responses/', {'question_id': 'monthly_saving', 'monthly_saving': '100'})
        c.post(f'/practice/attempts/{attempt.pk}/responses/', {'question_id': 'reason', 'reason': 'x'})
        c.post(f'/practice/attempts/{attempt.pk}/submit/', {'monthly_saving': '100', 'reason': 'x'})
        _, staff_c = staff_client('j-evaluator2@example.com', 'reviewer')
        staff_c.post(f'/staff/evaluations/{attempt.pk}/', {'requirement': self.req_practice.pk, 'decision': 'rejected'})
        c.post('/modules/saving-with-saccos/completion/')
        self.assertEqual(ModuleCompletion.objects.filter(owner=user).latest('evaluated_at').outcome, 'incomplete')
