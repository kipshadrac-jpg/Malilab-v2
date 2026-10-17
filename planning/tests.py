from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from planning.services import append_revision, create_plan
from learning.models import LearningJourney

User=get_user_model()
class PlanOwnershipAndHistoryTests(TestCase):
    def setUp(self):
        self.alice=User.objects.create_user('alice@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.bob=User.objects.create_user('bob@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.plan=create_plan(user=self.alice)
    def test_each_edit_appends_immutable_revision_pointer(self):
        first=append_revision(user=self.alice,plan=self.plan,target={'amount':'10.00','currency':'KES'},assumptions={},strategy_path={})
        second=append_revision(user=self.alice,plan=self.plan,target={'amount':'12.00','currency':'KES'},assumptions={},strategy_path={},predecessor=first)
        self.plan.refresh_from_db()
        self.assertEqual(second.predecessor_id,first.pk)
        self.assertEqual(self.plan.current_revision_id,second.pk)
        self.assertEqual(first.target['amount'],'10.00')
        first.target={'amount':'999'}
        with self.assertRaises(ValidationError):
            first.save()
    def test_foreign_journey_cannot_be_attached(self):
        foreign=LearningJourney.objects.create(owner=self.bob)
        with self.assertRaises(PermissionDenied):
            append_revision(user=self.alice,plan=self.plan,target={},assumptions={},strategy_path={},journey=foreign)
    def test_owner_cannot_be_reassigned_on_persisted_plan(self):
        self.plan.owner=self.bob
        with self.assertRaises(ValidationError):
            self.plan.save()
    def test_direct_revision_cannot_attach_foreign_private_record(self):
        foreign=LearningJourney.objects.create(owner=self.bob)
        from planning.models import PlanRevision
        with self.assertRaises(ValidationError):
            PlanRevision.objects.create(plan=self.plan,revision_number=1,target={},assumptions={},strategy_path={},journey=foreign)
