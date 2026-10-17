from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from content.models import PracticeActivity, PracticeActivityRevision
from practice.models import PracticeResponse
from practice.services import create_attempt, delete_response, get_owned_attempt, save_response, submit_attempt

User=get_user_model()

class PracticeOwnershipTests(TestCase):
    def setUp(self):
        self.alice=User.objects.create_user('alice@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        self.bob=User.objects.create_user('bob@example.com','strong-password-123',email_verified=True,email_verified_at=timezone.now())
        activity=PracticeActivity.objects.create(slug='budget-reflection')
        self.revision=PracticeActivityRevision.objects.create(activity=activity,revision_number=1,title='Reflection',response_schema={'schema_version': 1, 'questions': [{'id':'amount','type':'decimal_amount','label':'Amount','required':True,'constraints':{'currency':'KES'}}]})
    def test_attempt_history_cannot_cross_account_boundary(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        self.assertEqual(get_owned_attempt(user=self.alice,attempt_id=attempt.pk),attempt)
        with self.assertRaises(Exception):
            get_owned_attempt(user=self.bob,attempt_id=attempt.pk)
    def test_unverified_account_cannot_persist_attempt(self):
        user=User.objects.create_user('new@example.com','strong-password-123')
        with self.assertRaises(PermissionDenied):
            create_attempt(user=user,practice_revision=self.revision)
    def test_attempt_remains_pinned_to_its_exact_revision(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        later=PracticeActivityRevision.objects.create(
            activity=self.revision.activity, revision_number=2, title='Updated reflection',
            response_schema={'schema_version': 1, 'questions': [{'id':'amount','type':'decimal_amount','label':'Amount','required':True,'constraints':{'currency':'KES'}}]},
        )
        attempt.refresh_from_db()
        self.assertEqual(attempt.practice_revision_id,self.revision.pk)
        self.assertNotEqual(attempt.practice_revision_id,later.pk)
        self.assertEqual(get_owned_attempt(user=self.alice,attempt_id=attempt.pk).practice_revision_id,self.revision.pk)
    def test_saved_response_is_exact_decimal_string_and_update_before_submit(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        response=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='1250.40')
        self.assertEqual(response.value,'1250.40')
    def test_started_attempt_can_be_edited_then_submitted(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        response=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='2.50')
        self.assertEqual(response.value,'2.50')
        response=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='3.50')
        attempt=submit_attempt(user=self.alice,attempt_id=attempt.pk,responses={'amount':'3.50'})
        self.assertEqual(attempt.state,'submitted')
        with self.assertRaises(ValidationError):
            save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='4')
        response.value='999'
        with self.assertRaises(ValidationError):
            response.save()
        with self.assertRaises(ValidationError):
            PracticeResponse.objects.filter(pk=response.pk).update(value='999')
        with self.assertRaises(ValidationError):
            delete_response(user=self.alice,response_id=response.pk)
        with self.assertRaises(ValidationError):
            PracticeResponse.objects.filter(pk=response.pk).delete()
        with self.assertRaises(ValidationError):
            attempt.delete()
    def test_invalid_submission_does_not_partially_replace_saved_draft(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        saved=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='1.25')
        with self.assertRaises(ValidationError):
            submit_attempt(user=self.alice,attempt_id=attempt.pk,responses={'amount':'2.50','unknown':'bad'})
        attempt.refresh_from_db()
        saved.refresh_from_db()
        self.assertEqual(attempt.state,'started')
        self.assertIsNone(attempt.submitted_at)
        self.assertEqual(saved.value,'1.25')
    def test_cross_owner_response_mutation_is_rejected(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        response=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='1')
        with self.assertRaises(Exception):
            save_response(user=self.bob,attempt_id=attempt.pk,prompt_key='amount',value='2')
        with self.assertRaises(Exception):
            delete_response(user=self.bob,response_id=response.pk)

class PracticeSchemaValidationTests(PracticeOwnershipTests):
    # Reuse authenticated owner and pinned test revision fixtures.
    def test_schema_rejects_duplicate_question_ids_and_unknown_keys(self):
        from practice.schema import validate_schema
        q={'id':'answer','type':'short_text','label':'Answer','required':False,'constraints':{'max_length':20}}
        with self.assertRaises(ValidationError):
            validate_schema({'schema_version':1,'questions':[q,q]})
        with self.assertRaises(ValidationError):
            validate_schema({'schema_version':1,'questions':[dict(q,unexpected=True)]})

    def test_approved_prs_limits_are_enforced(self):
        from practice.schema import validate_schema, validate_response_set
        def q(**kw):
            base={'id':'a','type':'short_text','label':'A','required':False,'constraints':{'max_length':280}}
            base.update(kw); return base
        def schema(*qs): return {'schema_version':1,'questions':list(qs)}
        validate_schema(schema(q()))
        validate_schema(schema(q(id='b',type='long_text',constraints={'max_length':10_000})))
        validate_schema(schema(q(label='L'*500)))
        for bad in (q(constraints={'max_length':281}), q(type='long_text',constraints={'max_length':10_001}), q(label='L'*501)):
            with self.assertRaises(ValidationError):
                validate_schema(schema(bad))
        def choice(n): return q(type='single_choice',constraints=None,options=[{'id':f'o{i}','label':f'Option {i}'} for i in range(n)])
        def strip(d):
            d=dict(d); d.pop('constraints',None); return d
        validate_schema(schema(strip(choice(100))))
        with self.assertRaises(ValidationError):
            validate_schema(schema(strip(choice(101))))
        bad_option=strip(choice(1)); bad_option['options'][0]['label']='O'*501
        with self.assertRaises(ValidationError):
            validate_schema(schema(bad_option))
        validate_schema(schema(*[q(id=f'q{i}') for i in range(100)]))
        with self.assertRaises(ValidationError):
            validate_schema(schema(*[q(id=f'q{i}') for i in range(101)]))

    def test_schema_total_size_is_capped(self):
        from practice.schema import validate_schema
        questions=[{'id':f'q{i}','type':'single_choice','label':'L','required':False,
                    'options':[{'id':f'o{n}','label':'x'*500} for n in range(100)]} for i in range(100)]
        with self.assertRaises(ValidationError):
            validate_schema({'schema_version':1,'questions':questions})

    def test_kes_amounts_allow_at_most_two_decimal_places(self):
        from practice.schema import validate_answer
        q={'id':'amount','type':'decimal_amount','label':'Amount','required':True,'constraints':{'currency':'KES'}}
        for ok in ('0','12','12.5','12.50','1250.40'):
            self.assertEqual(validate_answer(q,ok),ok)
        for bad in ('1250.405','1.234','1e3','1,000','+5',' 5','05','-0','5.'):
            with self.assertRaises(ValidationError):
                validate_answer(q,bad)

    def test_failed_submit_preserves_draft_and_started_state(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        response=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='12.50')
        with self.assertRaises(ValidationError):
            submit_attempt(user=self.alice,attempt_id=attempt.pk,responses={'amount':'01.00'})
        attempt.refresh_from_db()
        response.refresh_from_db()
        self.assertEqual(attempt.state,'started')
        self.assertEqual(response.value,'12.50')

    def test_repeat_submit_is_rejected_without_changing_submitted_attempt(self):
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        submitted=submit_attempt(user=self.alice,attempt_id=attempt.pk,responses={'amount':'12'})
        timestamp=submitted.submitted_at
        with self.assertRaises(ValidationError):
            submit_attempt(user=self.alice,attempt_id=attempt.pk,responses={'amount':'13'})
        submitted.refresh_from_db()
        self.assertEqual(submitted.submitted_at,timestamp)
        self.assertEqual(submitted.responses.get(prompt_key='amount').value,'12')

class PracticeViewTests(PracticeOwnershipTests):
    def setUp(self):
        super().setUp()
        self.revision.status='published'
        self.revision._allow_lifecycle_transition=True
        self.revision.save()
        self.activity=PracticeActivity.objects.get(pk=self.revision.activity_id)
        self.activity.current_published_revision=self.revision
        self.activity.status='published'
        self.activity._allow_pointer_update=True
        self.activity.save()

    def test_public_exact_revision_and_authenticated_start_flow(self):
        from django.test import Client
        from django.urls import reverse
        response=Client().get(reverse('practice-activity', args=[self.activity.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reflection')
        client=Client()
        client.force_login(self.alice)
        started=client.post(reverse('practice-start', args=[self.activity.slug]))
        self.assertEqual(started.status_code, 302)
        attempt=self.alice.practice_attempts.get()
        self.assertEqual(attempt.practice_revision_id, self.revision.pk)
        page=client.get(started.url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Submit Practice')

    def test_submit_route_preserves_draft_on_error_and_confirms_submission(self):
        from django.test import Client
        from django.urls import reverse
        self.client=Client(); self.client.force_login(self.alice)
        attempt=create_attempt(user=self.alice,practice_revision=self.revision)
        saved=save_response(user=self.alice,attempt_id=attempt.pk,prompt_key='amount',value='22.10')
        failed=self.client.post(reverse('practice-submit',args=[attempt.pk]),{})
        self.assertEqual(failed.status_code,400)
        attempt.refresh_from_db(); saved.refresh_from_db()
        self.assertEqual(attempt.state,'started')
        self.assertEqual(saved.value,'22.10')
        success=self.client.post(reverse('practice-submit',args=[attempt.pk]),{'amount':'23.10'})
        self.assertEqual(success.status_code,302)
        attempt.refresh_from_db()
        self.assertEqual(attempt.state,'submitted')
        self.assertEqual(attempt.responses.get(prompt_key='amount').value,'23.10')
