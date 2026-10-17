from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.utils import timezone

from config.test_6b11 import audit
from content.models import (EditorialReview, Lesson, LessonRevision, Module, ModuleLearningRequirement,
                            ModuleRevision, PlaybookModuleRecommendation, PlaybookRevision, PracticeActivityRevision)
from content.test_admin import staff_client

User = get_user_model()

PRACTICE = {
    'title': 'Budget check', 'instructions': 'Fill in your numbers.', 'prompt': 'Think of last month.',
    'safety_text': 'This is not advice.', 'row_count': '5',
    'q0_label': 'Monthly income', 'q0_type': 'decimal_amount', 'q0_required': 'on', 'q0_min': '0',
    'q1_label': 'Main goal', 'q1_type': 'single_choice', 'q1_options': 'Save more\nInvest', 'q1_required': 'on',
    'q2_label': 'Anything else?', 'q2_type': 'long_text',
}


class StudioBase(TestCase):
    def setUp(self):
        self.author, self.author_c = staff_client('author@example.com', 'author_editor')
        self.reviewer, self.reviewer_c = staff_client('reviewer@example.com', 'reviewer')
        self.approver, self.approver_c = staff_client('approver@example.com', 'approver_publisher')
        self.admin, self.admin_c = staff_client('admin@example.com', 'administrator')

    def new_lesson(self, title='Saving basics', body='First paragraph about saving.\n\nSecond paragraph about sacco.'):
        response = self.author_c.post('/studio/new/lesson/', {'title': title, 'summary': 'Intro', 'body': body})
        self.assertEqual(response.status_code, 302, response.content[:1500])
        return LessonRevision.objects.filter(title=title).order_by('-pk').first()

    def new_practice(self, **overrides):
        response = self.author_c.post('/studio/new/practice/', {**PRACTICE, **overrides})
        self.assertEqual(response.status_code, 302, response.content[:1500])
        return PracticeActivityRevision.objects.order_by('-pk').first()

    def act(self, client, kind, rev, name, comment=''):
        return client.post(f'/studio/{kind}/{rev.pk}/{name}/', {'comment': comment})

    def publish(self, kind, rev):
        self.act(self.author_c, kind, rev, 'submit')
        self.act(self.reviewer_c, kind, rev, 'review')
        self.act(self.approver_c, kind, rev, 'publish')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'published')
        return rev


class AccessTests(StudioBase):
    def test_anonymous_visitors_are_sent_to_the_staff_sign_in(self):
        response = Client().get('/studio/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/login/?next=/studio/')

    def test_learners_cannot_tell_the_studio_exists(self):
        learner = User.objects.create_user('learner@example.com', 'Learner-pass-123', email_verified=True, email_verified_at=timezone.now())
        client = Client()
        client.force_login(learner)
        self.assertEqual(client.get('/studio/').status_code, 404)
        self.assertEqual(client.get('/studio/new/lesson/').status_code, 404)

    def test_staff_without_the_authenticator_step_are_sent_to_sign_in(self):
        user = User.objects.create_user('nootp@example.com', 'Staff-pass-123', is_staff=True)
        client = Client()
        client.force_login(user)
        self.assertEqual(client.get('/studio/').status_code, 302)

    def test_staff_with_no_editorial_role_see_nothing(self):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        user = User.objects.create_user('norole@example.com', 'Staff-pass-123', is_staff=True)
        device = TOTPDevice.objects.create(user=user, name='t', confirmed=True)
        client = Client()
        client.force_login(user)
        session = client.session
        session['otp_device_id'] = device.persistent_id
        session.save()
        self.assertEqual(client.get('/studio/').status_code, 404)

    def test_every_role_sees_only_its_own_work(self):
        author, reviewer = self.author_c.get('/studio/'), self.reviewer_c.get('/studio/')
        approver, admin = self.approver_c.get('/studio/'), self.admin_c.get('/studio/')
        self.assertContains(author, 'Make something new')
        self.assertContains(author, 'Your drafts')
        self.assertContains(author, 'Publish at least one first')       # module and playbook wait for published parts
        self.assertNotContains(author, 'Waiting for your review')
        self.assertNotContains(author, 'Ready to publish')
        self.assertContains(reviewer, 'Waiting for your review')
        self.assertNotContains(reviewer, 'Make something new')
        self.assertNotContains(reviewer, 'Ready to publish')
        self.assertContains(approver, 'Ready to publish')
        self.assertNotContains(approver, 'Make something new')
        self.assertNotContains(approver, 'Waiting for your review')
        self.assertContains(admin, 'Staff accounts')
        self.assertContains(admin, 'author@example.com')
        self.assertNotContains(admin, 'Make something new')

    def test_pages_are_never_cached_and_offer_sign_out(self):
        response = self.author_c.get('/studio/')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertContains(response, 'action="/admin/logout/"')

    def test_unknown_kinds_and_actions_are_not_found(self):
        rev = self.new_lesson()
        self.assertEqual(self.author_c.get('/studio/new/banana/').status_code, 404)
        self.assertEqual(self.author_c.get('/studio/banana/1/').status_code, 404)
        self.assertEqual(self.author_c.post(f'/studio/lesson/{rev.pk}/explode/').status_code, 404)

    def test_actions_are_post_only_and_need_a_csrf_token(self):
        rev = self.new_lesson()
        self.assertEqual(self.author_c.get(f'/studio/lesson/{rev.pk}/submit/').status_code, 405)
        self.author_c.handler.enforce_csrf_checks = True
        self.assertEqual(self.author_c.post(f'/studio/lesson/{rev.pk}/submit/').status_code, 403)
        self.assertEqual(self.author_c.post('/studio/new/lesson/', {'title': 'X', 'body': 'Y'}).status_code, 403)
        self.author_c.handler.enforce_csrf_checks = False
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'draft')


class LessonStudioTests(StudioBase):
    def test_author_creates_a_lesson_draft(self):
        rev = self.new_lesson()
        self.assertEqual((rev.status, rev.revision_number, rev.author_id), ('draft', 1, self.author.pk))
        self.assertEqual(rev.lesson.slug, 'saving-basics')
        self.assertEqual([b['payload']['text'] for b in rev.blocks], ['First paragraph about saving.', 'Second paragraph about sacco.'])
        page = self.author_c.get(f'/studio/lesson/{rev.pk}/')
        self.assertContains(page, 'First paragraph about saving.')
        self.assertContains(page, 'Send for review')
        self.assertEqual(Client().get('/lessons/saving-basics/').status_code, 404)   # drafts are not public

    def test_same_title_gets_a_new_address(self):
        self.new_lesson()
        second = self.new_lesson()
        self.assertEqual(second.lesson.slug, 'saving-basics-2')

    def test_empty_lesson_is_refused_with_a_clear_message(self):
        response = self.author_c.post('/studio/new/lesson/', {'title': 'Empty', 'body': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
        self.assertFalse(Lesson.objects.exists())

    def test_editing_keeps_paragraph_identity(self):
        rev = self.new_lesson()
        first_key = rev.blocks[0]['key']
        response = self.author_c.post(f'/studio/lesson/{rev.pk}/edit/', {
            'title': 'Saving basics', 'summary': 'New intro', 'body': 'Changed first.\n\nSecond paragraph about sacco.\n\nThird.'})
        self.assertEqual(response.status_code, 302)
        rev.refresh_from_db()
        self.assertEqual(len(rev.blocks), 3)
        self.assertEqual(rev.blocks[0]['key'], first_key)
        self.assertEqual(rev.summary, 'New intro')

    def test_only_the_author_can_edit_and_only_while_draft(self):
        rev = self.new_lesson()
        other, other_c = staff_client('author2@example.com', 'author_editor')
        self.assertEqual(other_c.get(f'/studio/lesson/{rev.pk}/edit/').status_code, 404)
        self.assertEqual(self.reviewer_c.get(f'/studio/lesson/{rev.pk}/edit/').status_code, 404)
        self.act(self.author_c, 'lesson', rev, 'submit')
        self.assertEqual(self.author_c.get(f'/studio/lesson/{rev.pk}/edit/').status_code, 404)

    def test_other_roles_cannot_start_content(self):
        for client in (self.reviewer_c, self.approver_c, self.admin_c):
            self.assertEqual(client.post('/studio/new/lesson/', {'title': 'No', 'body': 'No'}).status_code, 404)
        self.assertFalse(Lesson.objects.exists())

    def test_reviewers_do_not_see_drafts_but_the_administrator_does(self):
        rev = self.new_lesson()
        self.assertEqual(self.reviewer_c.get(f'/studio/lesson/{rev.pk}/').status_code, 404)
        self.assertEqual(self.approver_c.get(f'/studio/lesson/{rev.pk}/').status_code, 404)
        self.assertEqual(self.admin_c.get(f'/studio/lesson/{rev.pk}/').status_code, 200)


class WorkflowTests(StudioBase):
    def test_full_flow_from_draft_to_public_page_and_search(self):
        rev = self.new_lesson()
        self.act(self.author_c, 'lesson', rev, 'submit')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'in_review')
        self.assertContains(self.reviewer_c.get('/studio/'), 'Saving basics')
        self.assertNotContains(self.approver_c.get('/studio/'), 'Saving basics')       # not reviewed yet
        self.act(self.approver_c, 'lesson', rev, 'publish')                             # too early
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'in_review')
        self.act(self.reviewer_c, 'lesson', rev, 'review', 'Reads well.')
        self.assertNotContains(self.reviewer_c.get('/studio/'), 'Saving basics')
        self.assertContains(self.approver_c.get('/studio/'), 'Saving basics')
        self.act(self.approver_c, 'lesson', rev, 'publish')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'published')
        self.assertContains(Client().get('/lessons/saving-basics/'), 'First paragraph about saving.')
        self.assertContains(Client().get('/search/?q=sacco'), 'Saving basics')
        page = self.admin_c.get('/studio/')
        self.assertContains(page, 'Recent publications')
        self.assertContains(page, 'Lesson: Saving basics')

    def test_the_author_cannot_review_or_publish_their_own_work(self):
        rev = self.new_lesson()
        self.act(self.author_c, 'lesson', rev, 'submit')
        self.act(self.author_c, 'lesson', rev, 'review')
        self.act(self.author_c, 'lesson', rev, 'publish')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'in_review')
        self.assertFalse(EditorialReview.objects.exists())

    def test_reviewer_returns_with_a_reason_and_the_author_starts_a_new_draft(self):
        rev = self.new_lesson()
        self.act(self.author_c, 'lesson', rev, 'submit')
        self.act(self.reviewer_c, 'lesson', rev, 'return', '')          # a reason is required
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'in_review')
        self.act(self.reviewer_c, 'lesson', rev, 'return', 'Please add a worked example.')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'returned')
        event = EditorialReview.objects.get()
        self.assertEqual((event.action, event.comment), ('changes_requested', 'Please add a worked example.'))
        home = self.author_c.get('/studio/')
        self.assertContains(home, 'Returned to you')
        page = self.author_c.get(f'/studio/lesson/{rev.pk}/')
        self.assertContains(page, 'Please add a worked example.')
        self.assertContains(page, 'Start a new draft from this')
        self.act(self.author_c, 'lesson', rev, 'new-draft')
        newer = LessonRevision.objects.get(lesson=rev.lesson, revision_number=2)
        self.assertEqual((newer.status, newer.author_id), ('draft', self.author.pk))
        self.assertEqual(newer.blocks, rev.blocks)
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'returned')                         # history is untouched
        self.publish('lesson', newer)
        self.assertEqual(Lesson.objects.get(pk=rev.lesson_id).current_published_revision_id, newer.pk)

    def test_approver_can_return_after_review_but_reviewer_cannot_after_passing_it(self):
        rev = self.new_lesson()
        self.act(self.author_c, 'lesson', rev, 'submit')
        self.act(self.reviewer_c, 'lesson', rev, 'review')
        self.act(self.reviewer_c, 'lesson', rev, 'return', 'Changed my mind.')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'in_review')
        self.act(self.approver_c, 'lesson', rev, 'return', 'Tone is off for beginners.')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'returned')

    def test_a_published_lesson_can_be_corrected_through_a_new_draft(self):
        rev = self.publish('lesson', self.new_lesson())
        self.act(self.author_c, 'lesson', rev, 'new-draft')
        draft = LessonRevision.objects.get(lesson=rev.lesson, revision_number=2)
        self.assertEqual(draft.status, 'draft')
        self.act(self.author_c, 'lesson', rev, 'new-draft')               # one unpublished revision at a time
        self.assertEqual(LessonRevision.objects.filter(lesson=rev.lesson).count(), 2)
        self.author_c.post(f'/studio/lesson/{draft.pk}/edit/', {'title': 'Saving basics', 'summary': '', 'body': 'Corrected text about sacco.'})
        self.publish('lesson', draft)
        self.assertContains(Client().get('/lessons/saving-basics/'), 'Corrected text about sacco.')

    def test_sending_an_incomplete_item_for_review_explains_what_is_missing(self):
        module = Module.objects.create(slug='empty-module')
        rev = ModuleRevision.objects.create(module=module, revision_number=1, title='Empty module', author=self.author)
        response = self.author_c.post(f'/studio/module/{rev.pk}/submit/', {}, follow=True)
        self.assertContains(response, 'Choose at least one lesson or practice activity')
        rev.refresh_from_db()
        self.assertEqual(rev.status, 'draft')


class PracticeStudioTests(StudioBase):
    def test_questions_become_a_valid_strict_schema(self):
        rev = self.new_practice()
        questions = rev.response_schema['questions']
        self.assertEqual([q['id'] for q in questions], ['monthly_income', 'main_goal', 'anything_else'])
        self.assertEqual(questions[0], {'id': 'monthly_income', 'type': 'decimal_amount', 'label': 'Monthly income',
                                        'required': True, 'constraints': {'currency': 'KES', 'minimum': '0'}})
        self.assertEqual(questions[1]['options'], [{'id': 'save_more', 'label': 'Save more'}, {'id': 'invest', 'label': 'Invest'}])
        self.assertEqual((questions[2]['required'], questions[2]['constraints']), (False, {'max_length': 2000}))

    def test_bad_questions_are_explained_and_nothing_is_saved(self):
        bad = self.author_c.post('/studio/new/practice/', {**PRACTICE, 'q1_options': 'Only one'})
        self.assertContains(bad, 'give at least two options')
        none = self.author_c.post('/studio/new/practice/', {'title': 'No questions', 'row_count': '5'})
        self.assertContains(none, 'Add at least one question')
        number = self.author_c.post('/studio/new/practice/', {**PRACTICE, 'q0_min': 'abc'})
        self.assertContains(number, 'must be an amount')
        self.assertFalse(PracticeActivityRevision.objects.exists())

    def test_more_question_rows_can_be_added_without_losing_typed_answers(self):
        response = self.author_c.post('/studio/new/practice/', {**PRACTICE, 'add_rows': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Question 10 text')
        self.assertContains(response, 'value="Monthly income"')
        self.assertFalse(PracticeActivityRevision.objects.exists())

    def test_editing_keeps_existing_question_ids(self):
        rev = self.new_practice()
        page = self.author_c.get(f'/studio/practice/{rev.pk}/edit/')
        self.assertContains(page, 'value="monthly_income"')
        data = {**PRACTICE, 'q0_id': 'monthly_income', 'q0_label': 'Total monthly income', 'q1_id': 'main_goal', 'q2_id': 'anything_else'}
        self.assertEqual(self.author_c.post(f'/studio/practice/{rev.pk}/edit/', data).status_code, 302)
        rev.refresh_from_db()
        self.assertEqual(rev.response_schema['questions'][0]['id'], 'monthly_income')
        self.assertEqual(rev.response_schema['questions'][0]['label'], 'Total monthly income')

    def test_published_practice_is_reachable_by_learners(self):
        rev = self.publish('practice', self.new_practice())
        self.assertContains(Client().get(f'/practice/{rev.activity.slug}/'), 'Budget check')


class ModuleAndPlaybookStudioTests(StudioBase):
    def build_parts(self):
        lesson = self.publish('lesson', self.new_lesson())
        practice = self.publish('practice', self.new_practice())
        return lesson, practice

    def test_module_and_playbook_wait_until_there_is_something_to_use(self):
        self.assertContains(self.author_c.get('/studio/new/module/'), 'Publish at least one first')
        self.assertContains(self.author_c.get('/studio/new/playbook/'), 'Publish at least one module first')
        self.assertFalse(Module.objects.exists())

    def test_module_is_built_from_published_parts_in_the_chosen_order(self):
        lesson, practice = self.build_parts()
        page = self.author_c.get('/studio/new/module/')
        self.assertContains(page, 'Saving basics')
        self.assertContains(page, 'Budget check')
        response = self.author_c.post('/studio/new/module/', {
            'title': 'Start saving', 'description': 'A first module.',
            f'inc_lesson-{lesson.pk}': 'on', f'pos_lesson-{lesson.pk}': '2', f'cls_lesson-{lesson.pk}': 'required',
            f'inc_practice-{practice.pk}': 'on', f'pos_practice-{practice.pk}': '1', f'cls_practice-{practice.pk}': 'recommended'})
        self.assertEqual(response.status_code, 302, response.content[:1500])
        module = ModuleRevision.objects.get(title='Start saving')
        rows = list(module.learning_requirements.order_by('position'))
        self.assertEqual([(r.target_kind, r.position, r.classification) for r in rows],
                         [('practice', 1, 'recommended'), ('lesson', 2, 'required')])
        self.assertEqual(rows[1].lesson_revision_id, lesson.pk)

    def test_module_needs_at_least_one_choice(self):
        self.build_parts()
        response = self.author_c.post('/studio/new/module/', {'title': 'Nothing chosen', 'description': ''})
        self.assertContains(response, 'Choose at least one lesson or practice activity')
        self.assertFalse(ModuleRevision.objects.exists())

    def test_editing_a_module_replaces_its_choices(self):
        lesson, practice = self.build_parts()
        self.author_c.post('/studio/new/module/', {'title': 'Start saving', 'description': '',
                                                    f'inc_lesson-{lesson.pk}': 'on', f'pos_lesson-{lesson.pk}': '1',
                                                    f'inc_practice-{practice.pk}': 'on', f'pos_practice-{practice.pk}': '2'})
        module = ModuleRevision.objects.get(title='Start saving')
        self.assertEqual(module.learning_requirements.count(), 2)
        self.author_c.post(f'/studio/module/{module.pk}/edit/', {'title': 'Start saving', 'description': 'Edited',
                                                                 f'inc_practice-{practice.pk}': 'on', f'pos_practice-{practice.pk}': '1'})
        module.refresh_from_db()
        self.assertEqual(module.description, 'Edited')
        self.assertEqual(list(module.learning_requirements.values_list('target_kind', flat=True)), ['practice'])

    def test_playbook_recommends_published_modules_and_goes_live(self):
        lesson, practice = self.build_parts()
        self.author_c.post('/studio/new/module/', {'title': 'Start saving', 'description': 'A first module.',
                                                    f'inc_lesson-{lesson.pk}': 'on', f'pos_lesson-{lesson.pk}': '1'})
        module = self.publish('module', ModuleRevision.objects.get(title='Start saving'))
        self.assertContains(Client().get(f'/modules/{module.module.slug}/'), 'Saving basics')
        missing = self.author_c.post('/studio/new/playbook/', {'title': 'I want to save', 'summary': '', f'inc_module-{module.pk}': 'on'})
        self.assertContains(missing, 'This field is required')
        response = self.author_c.post('/studio/new/playbook/', {
            'title': 'I want to save', 'summary': 'For people who want a first emergency fund.', 'scenario': 'You just got paid.',
            f'inc_module-{module.pk}': 'on', f'pos_module-{module.pk}': '1', f'rat_module-{module.pk}': 'Start here.'})
        self.assertEqual(response.status_code, 302, response.content[:1500])
        playbook = PlaybookRevision.objects.get(title='I want to save')
        self.assertEqual(PlaybookModuleRecommendation.objects.get(playbook_revision=playbook).rationale, 'Start here.')
        self.publish('playbook', playbook)
        page = Client().get(f'/playbooks/{playbook.playbook.slug}/')
        self.assertContains(page, 'For people who want a first emergency fund.')
        self.assertContains(page, 'Start saving')


class StudioAccessibilityTests(StudioBase):
    def setUp(self):
        super().setUp()
        self.failures = []

    def check(self, client, path):
        response = client.get(path)
        if response.status_code != 200:
            self.failures.append(f'{path}: HTTP {response.status_code}')
            return
        self.failures += [f'{path}: {problem}' for problem in audit(response)]

    def test_studio_pages_meet_basic_accessibility_rules(self):
        lesson = self.new_lesson()
        practice = self.new_practice()
        self.act(self.author_c, 'lesson', lesson, 'submit')
        for client, path in [
                (self.author_c, '/studio/'), (self.author_c, '/studio/new/lesson/'), (self.author_c, '/studio/new/practice/'),
                (self.author_c, f'/studio/practice/{practice.pk}/'), (self.author_c, f'/studio/practice/{practice.pk}/edit/'),
                (self.author_c, '/studio/new/module/'), (self.reviewer_c, '/studio/'),
                (self.reviewer_c, f'/studio/lesson/{lesson.pk}/'), (self.approver_c, '/studio/'), (self.admin_c, '/studio/')]:
            self.check(client, path)
        self.act(self.reviewer_c, 'lesson', lesson, 'review')
        self.check(self.approver_c, f'/studio/lesson/{lesson.pk}/')
        published = self.publish('practice', practice)
        self.author_c.post('/studio/new/module/', {'title': 'Mod', 'description': '', f'inc_practice-{published.pk}': 'on',
                                                    f'pos_practice-{published.pk}': '1'})
        module = ModuleRevision.objects.get(title='Mod')
        for path in (f'/studio/module/{module.pk}/', f'/studio/module/{module.pk}/edit/', '/studio/new/module/'):
            self.check(self.author_c, path)
        self.publish('module', module)
        self.check(self.author_c, '/studio/new/playbook/')
        self.check(self.admin_c, '/studio/')
        self.assertEqual(self.failures, [], '\n'.join(self.failures))
