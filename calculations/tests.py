from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from calculations.models import LabTool, CalculatorDefinition, FormulaVersion
from calculations.services import save_result
from content.models import PracticeActivity, PracticeActivityRevision
from practice.models import PracticeAttempt

User=get_user_model()
class FormulaAndResultTests(TestCase):
    def setUp(self):
        self.alice=User.objects.create_user('alice@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.bob=User.objects.create_user('bob@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        tool=LabTool.objects.create(slug='foundation-tool',title='Foundation')
        definition=CalculatorDefinition.objects.create(lab_tool=tool,key='generic')
        self.formula=FormulaVersion.objects.create(definition=definition,version_key='v1',state='active')
        activity=PracticeActivity.objects.create(slug='foundation-practice')
        revision=PracticeActivityRevision.objects.create(activity=activity,revision_number=1,title='Practice')
        self.attempt=PracticeAttempt.objects.create(owner=self.alice,practice_revision=revision)
    def test_result_requires_active_formula_and_decimal_snapshot_strings(self):
        result=save_result(user=self.alice,formula_version=self.formula,inputs={'amount':'12.30'},outputs={'total':'13.07'},practice_attempt=self.attempt,currency='KES')
        self.assertEqual(result.outputs['total'],'13.07')
        self.assertEqual(result.currency,'KES')
    def test_cross_account_attempt_reference_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            save_result(user=self.bob,formula_version=self.formula,inputs={},outputs={},practice_attempt=self.attempt)
    def test_model_boundary_rejects_cross_account_attempt_reference(self):
        from django.core.exceptions import ValidationError
        from calculations.models import CalculationResult
        with self.assertRaises(ValidationError):
            CalculationResult.objects.create(owner=self.bob,formula_version=self.formula,practice_attempt=self.attempt,inputs={},outputs={})
    def test_draft_formula_cannot_be_used(self):
        self.formula.state='draft'
        with self.assertRaises(ValidationError):
            save_result(user=self.alice,formula_version=self.formula,inputs={},outputs={})
