"""Patch 13: playbook step cards (goal, what you need, steps, where this leaves you) and the AI that writes them."""
from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase

from config.test_6b11 import audit
from content import guide
from content.authoring import start_revision_from
from content.models import ModuleRevision, PlaybookRevision
from content.test_ai_assistant import AssistantBase
from content.test_studio import StudioBase

STEPS = """### Open your M-Pesa statement

Dial *334# or open the app and download the last **three months**.

Total what went out each month. Example: KES 42,000 out against KES 50,000 in.

- Rent and fare
- Airtime and data
- Food

### Move savings first (optional)

Set a standing order for ==orange:pay day==.

Done looks like a saved reminder."""


class ParsingTests(SimpleTestCase):
    def test_steps_parse_and_round_trip(self):
        steps = guide.parse_steps(STEPS)
        self.assertEqual([s['title'] for s in steps], ['Open your M-Pesa statement', 'Move savings first'])
        self.assertEqual([s['optional'] for s in steps], [False, True])
        self.assertEqual(guide.parse_steps(guide.steps_to_text(steps)), steps)

    def test_bad_steps_say_what_is_wrong(self):
        for text, words in [('Some text first', 'Start every step'), ('### \nx', 'no title'), ('### A', 'no text'),
                            ('### A\n\n' + 'x' * 800, 'too long'),
                            ('\n'.join(f'### S{i}\n\nok' for i in range(13)), 'at most 12')]:
            with self.subTest(text=text[:20]), self.assertRaises(ValidationError) as ctx:
                guide.parse_steps(text)
            self.assertIn(words, ' '.join(ctx.exception.messages))

    def test_needs_are_one_per_line(self):
        self.assertEqual(guide.parse_needs('- A pay slip\n\n30 minutes'), ['A pay slip', '30 minutes'])
        with self.assertRaises(ValidationError):
            guide.parse_needs('\n'.join(['x'] * 11))

    def test_rendering_escapes_everything(self):
        html = guide.render_text('<script>alert(1)</script> **bold**\n\n- ==pink:<b>x</b>==')
        self.assertNotIn('<script>', html)
        self.assertNotIn('<b>', html)
        self.assertIn('<strong>bold</strong>', html)
        self.assertIn('<ul><li>', html)

    def test_playbooks_without_a_guide_are_fine(self):
        class Old:
            assumptions, discovery_metadata = None, 'junk'
        result = guide.guide_of(Old())
        self.assertFalse(result['has_steps'])
        self.assertEqual(result['needs'], [])


class StudioPlaybookTests(StudioBase):
    def make_module(self):
        lesson = self.publish('lesson', self.new_lesson())
        self.author_c.post('/studio/new/module/', {'title': 'Start saving', 'description': 'A first module.',
                                                    f'inc_lesson-{lesson.pk}': 'on', f'pos_lesson-{lesson.pk}': '1'})
        return self.publish('module', ModuleRevision.objects.get(title='Start saving'))

    def post(self, module, **extra):
        data = {'title': 'Budget in a day', 'summary': 'Build a first budget.', 'scenario': 'You earn KES 50,000 and it vanishes.',
                'needs': '- Your M-Pesa statement\n- 30 minutes', 'steps': STEPS, 'outcome': 'You now have a plan.\n\nRepeat monthly.',
                f'inc_module-{module.pk}': 'on', f'pos_module-{module.pk}': '1', f'rat_module-{module.pk}': 'Go deeper.'}
        data.update(extra)
        return self.author_c.post('/studio/new/playbook/', data)

    def test_guide_is_saved_shown_in_the_editor_and_goes_live(self):
        module = self.make_module()
        response = self.post(module)
        self.assertEqual(response.status_code, 302, response.content[:1500])
        rev = PlaybookRevision.objects.get(title='Budget in a day')
        self.assertEqual(rev.assumptions, ['Your M-Pesa statement', '30 minutes'])
        self.assertEqual(len(rev.discovery_metadata['guide']['steps']), 2)
        self.assertContains(self.author_c.get(f'/studio/playbook/{rev.pk}/edit/'), '### Open your M-Pesa statement')
        self.assertContains(self.author_c.get(f'/studio/playbook/{rev.pk}/'), 'Where this leaves you')
        self.publish('playbook', rev)
        page = Client().get(f'/playbooks/{rev.playbook.slug}/')
        for text in ('Goal', 'What you need', 'Your M-Pesa statement', 'Open your M-Pesa statement', 'Optional',
                     'Where this leaves you', 'Repeat monthly.', 'Go deeper: recommended modules', 'Start saving', 'pg-step'):
            self.assertContains(page, text)
        self.assertEqual(audit(page), [])

    def test_a_new_revision_keeps_the_guide(self):
        module = self.make_module()
        self.post(module)
        rev = self.publish('playbook', PlaybookRevision.objects.get(title='Budget in a day'))
        actor = rev.author
        actor.is_verified = lambda: True      # the copy service needs a verified staff member
        new = start_revision_from(revision=rev, actor=actor)
        self.assertEqual(new.discovery_metadata['guide']['steps'][0]['title'], 'Open your M-Pesa statement')
        self.assertEqual(new.assumptions, rev.assumptions)

    def test_markup_in_steps_is_shown_as_text(self):
        module = self.make_module()
        self.post(module, steps='### <script>alert(1)</script>\n\n<img src=x onerror=alert(1)> **ok**')
        rev = self.publish('playbook', PlaybookRevision.objects.get(title='Budget in a day'))
        page = Client().get(f'/playbooks/{rev.playbook.slug}/')
        self.assertNotContains(page, '<script>alert(1)')
        self.assertNotContains(page, '<img src=x')
        self.assertContains(page, '&lt;script&gt;')

    def test_bad_steps_are_explained_and_nothing_is_saved(self):
        module = self.make_module()
        response = self.post(module, steps='### Only a title')
        self.assertContains(response, 'has a title but no text')
        self.assertFalse(PlaybookRevision.objects.exists())

    def test_steps_are_optional_so_a_simple_playbook_still_works(self):
        module = self.make_module()
        self.assertEqual(self.post(module, needs='', steps='', outcome='').status_code, 302)
        rev = PlaybookRevision.objects.get(title='Budget in a day')
        self.assertNotIn('guide', rev.discovery_metadata)
        self.publish('playbook', rev)
        self.assertContains(Client().get(f'/playbooks/{rev.playbook.slug}/'), 'You earn KES 50,000')


class AIPlaybookTests(AssistantBase):
    def make_module(self):
        lesson = self.publish('lesson', self.new_lesson())
        self.generate(brief={'kind': 'module'}, results=({'title': 'Saving module', 'description': 'd', 'to_verify': [],
                                                          'items': [{'key': f'lesson-{lesson.pk}', 'classification': 'required'}]},))
        return self.publish('module', ModuleRevision.objects.get())

    def result(self, module, **extra):
        data = {'title': 'Budget in a day', 'summary': 'Build a first budget.', 'scenario': 'You earn KES 50,000.',
                'needs': ['Your M-Pesa statement', '30 minutes'], 'outcome': 'You now have a plan.',
                'steps': [{'title': 'Open your statement', 'text': 'Download it.\n\n- Rent\n- Fare'},
                          {'title': '# List fixed costs', 'text': '## Rent first.\n\nThen fare.'},
                          {'title': 'Move savings first', 'text': 'Do it on pay day.'},
                          {'title': 'Review next month', 'text': 'Adjust.', 'optional': True}],
                'to_verify': ['Typical Sacco dividend'], 'items': [{'key': f'module-{module.pk}', 'rationale': 'Go deeper.'}]}
        data.update(extra)
        return data

    def test_the_ai_writes_the_step_cards(self):
        module = self.make_module()
        response = self.generate(brief={'kind': 'playbook', 'topic': 'Budget', 'length': 'medium'}, results=(self.result(module),))
        self.assertEqual(response.status_code, 302, response.content[:800])
        rev = PlaybookRevision.objects.get(title='Budget in a day')
        steps = rev.discovery_metadata['guide']['steps']
        self.assertEqual([s['title'] for s in steps][:2], ['Open your statement', 'List fixed costs'])
        self.assertTrue(steps[3]['optional'])
        self.assertNotIn('#', steps[1]['text'])
        self.assertEqual(rev.assumptions, ['Your M-Pesa statement', '30 minutes'])
        self.assertIn('Number of steps: 6 to 8', self.calls.call_args[0][1])
        self.assertEqual(self.calls.call_args[0][3], 8000)

    def test_a_playbook_without_steps_is_sent_back_once_then_refused(self):
        module = self.make_module()
        bare = self.result(module, steps=[])
        response = self.generate(brief={'kind': 'playbook', 'topic': 'Budget'}, results=(bare, bare))
        self.assertContains(response, 'at least 4 real hands-on steps')
        self.assertEqual(self.calls.call_count, 2)
        self.assertFalse(PlaybookRevision.objects.exists())

    def test_the_repair_pass_can_fix_missing_steps(self):
        module = self.make_module()
        response = self.generate(brief={'kind': 'playbook', 'topic': 'Budget'},
                                 results=(self.result(module, steps=[]), self.result(module)))
        self.assertEqual(response.status_code, 302, response.content[:800])
        self.assertTrue(PlaybookRevision.objects.filter(title='Budget in a day').exists())
