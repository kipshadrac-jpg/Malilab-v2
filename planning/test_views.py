from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.utils import timezone
from planning.models import MyPlan

User=get_user_model()

class MyPlanViewTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('planner@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.other=User.objects.create_user('otherplanner@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.client.force_login(self.owner)

    def test_create_and_append_immutable_revisions(self):
        response=self.client.post('/my-plan/',{'target':'My chosen target','assumptions':'My assumptions','strategy_path':'A possible path'})
        self.assertEqual(response.status_code,302)
        plan=MyPlan.objects.get(owner=self.owner)
        first=plan.current_revision
        self.client.post(f'/my-plan/{plan.pk}/',{'target':'Updated target','assumptions':'New assumptions','strategy_path':'Another path'})
        plan.refresh_from_db()
        self.assertEqual(plan.revisions.count(),2)
        self.assertEqual(plan.revisions.get(pk=first.pk).target['text'],'My chosen target')
        self.assertEqual(plan.current_revision.revision_number,2)

    def test_another_account_cannot_read_plan_history(self):
        self.client.post('/my-plan/',{'target':'Private target'})
        plan=MyPlan.objects.get(owner=self.owner)
        other=Client(); other.force_login(self.other)
        self.assertEqual(other.get(f'/my-plan/{plan.pk}/').status_code,404)
