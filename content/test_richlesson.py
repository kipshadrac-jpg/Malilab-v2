import uuid

from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, TestCase

from config.test_6b11 import audit
from content.models import LessonRevision, validate_lesson_blocks
from content.richtext import (RichTextError, body_from_blocks, parse_body, plain_text, render_blocks,
                              render_inline, validate_payload)
from content.test_studio import StudioBase

BODY = """## Why a budget helps
A budget tells your money **where to go**. It takes ==ten minutes== a month.

Short paragraphs are easier to read on a phone.

### Three habits
- Track spending
- Pay yourself ==green:first==
- Review monthly

1. Write down income
2. List fixed costs

> tip: Start with just one category.
> key: Small steps beat perfect plans.

| Option | Typical return | Access |
| --- | --- | --- |
| Sacco | 8% | Slow |
| Money market fund | 10% | Fast |

## Next steps
Pick one habit today <script>alert(1)</script>."""


class ParserTests(SimpleTestCase):
    def test_all_five_block_types_are_produced(self):
        types = [b['type'] for b in parse_body(BODY)]
        self.assertEqual(types, ['heading', 'paragraph', 'paragraph', 'heading', 'list', 'list', 'callout', 'callout',
                                 'table', 'heading', 'paragraph'])
        self.assertEqual(set(types), {'heading', 'paragraph', 'list', 'callout', 'table'})

    def test_blocks_pass_the_model_validator_and_round_trip(self):
        blocks = parse_body(BODY)
        validate_lesson_blocks(blocks)
        self.assertEqual(parse_body(body_from_blocks(blocks), blocks), blocks)

    def test_existing_keys_are_kept_by_position(self):
        first = parse_body('One.\n\nTwo.')
        second = parse_body('One changed.\n\nTwo.\n\nThree.', first)
        self.assertEqual([b['key'] for b in second[:2]], [b['key'] for b in first])
        self.assertNotIn(second[2]['key'], [b['key'] for b in first])

    def test_plain_paragraphs_behave_as_before(self):
        blocks = parse_body('First paragraph.\n\nSecond paragraph.')
        self.assertEqual([(b['type'], b['payload']) for b in blocks],
                         [('paragraph', {'text': 'First paragraph.'}), ('paragraph', {'text': 'Second paragraph.'})])

    def test_helpful_errors(self):
        for bad, words in [('', 'at least one'), ('| a | b |\n| c |', 'same number of cells'),
                           ('| a | b |', 'heading row'), ('> tip:', 'cannot be empty'),
                           ('- ' + 'x' * 600, 'too long'), ('## ', 'cannot be empty')]:
            with self.subTest(bad=bad), self.assertRaises(RichTextError) as ctx:
                parse_body(bad)
            self.assertIn(words, str(ctx.exception))

    def test_each_tone_word_starts_a_new_box_and_other_lines_continue_it(self):
        boxes = parse_body('> tip: One.\n> still one\n> warning: Two.')
        self.assertEqual([(b['payload']['tone'], b['payload']['text']) for b in boxes],
                         [('tip', 'One. still one'), ('warning', 'Two.')])

    def test_unknown_callout_word_is_just_a_note(self):
        block = parse_body('> shout: hello')[0]
        self.assertEqual(block['payload'], {'tone': 'note', 'text': 'shout: hello'})


class SchemaTests(SimpleTestCase):
    K = str(uuid.UUID(int=1))

    def block(self, btype, payload):
        return [{'key': self.K, 'type': btype, 'position': 0, 'payload': payload}]

    def test_old_paragraph_shape_is_still_valid(self):
        validate_lesson_blocks(self.block('paragraph', {'text': 'Hi'}))

    def test_a_heading_needs_its_level_and_nothing_else(self):
        for payload in ({'text': 'x'}, {'text': 'x', 'level': 1}, {'text': 'x', 'level': True}, {'text': 'x', 'level': 2, 'html': '<b>'}):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                validate_lesson_blocks(self.block('heading', payload))
        validate_lesson_blocks(self.block('heading', {'text': 'x', 'level': 3}))

    def test_other_malformed_payloads_are_refused(self):
        bad = [('list', {'items': [], 'ordered': False}), ('list', {'items': ['a'], 'ordered': 'no'}),
               ('list', {'items': [1], 'ordered': False}), ('callout', {'tone': 'red', 'text': 'x'}),
               ('callout', {'tone': 'tip'}), ('table', {'header': ['a'], 'rows': [['1']]}),
               ('table', {'header': ['a', 'b'], 'rows': [['1']]}), ('table', {'header': ['a', 'b'], 'rows': []}),
               ('image', {'text': 'x'}), ('paragraph', {'text': 'x', 'style': 'red'})]
        for btype, payload in bad:
            with self.subTest(btype=btype, payload=payload), self.assertRaises(ValidationError):
                validate_lesson_blocks(self.block(btype, payload))

    def test_validate_payload_raises_plain_errors(self):
        with self.assertRaises(RichTextError):
            validate_payload('table', {'header': ['a', 'b'], 'rows': [['1']]})


class RenderTests(SimpleTestCase):
    def test_inline_markup(self):
        html = render_inline('**key** and ==yellow== and ==blue:cool== and ==neon:no==')
        self.assertIn('<strong>key</strong>', html)
        self.assertIn('<mark class="hl hl-yellow">yellow</mark>', html)
        self.assertIn('<mark class="hl hl-blue">cool</mark>', html)
        self.assertNotIn('hl-neon', html)

    def test_html_is_always_escaped(self):
        html = str(render_blocks(parse_body('<script>alert(1)</script> **<img src=x onerror=alert(1)>**\n\n- <b>x</b>\n\n| <i>a</i> | b |\n| 1 | <u>2</u> |')))
        for raw in ('<script', '<img', '<b>', '<i>', '<u>'):
            self.assertNotIn(raw, html)
        self.assertIn('&lt;script&gt;', html)

    def test_headings_rotate_through_colours_and_never_skip_a_level(self):
        html = str(render_blocks(parse_body('### Early\n\n## A\n\n## B\n\n### Under B\n\n## C')))
        self.assertIn('<h2 class="lh lh-0">Early</h2>', html)     # a level 3 with no level 2 above becomes level 2
        self.assertIn('<h2 class="lh lh-1">A</h2>', html)
        self.assertIn('<h2 class="lh lh-2">B</h2>', html)
        self.assertIn('<h3 class="lh lh-2">Under B</h3>', html)
        self.assertIn('<h2 class="lh lh-3">C</h2>', html)

    def test_callouts_carry_a_text_label(self):
        html = str(render_blocks(parse_body('> warning: Never share your PIN.\n\n> example: Wanjiku saves 500.')))
        self.assertIn('callout-warning', html)
        self.assertIn('Watch out', html)
        self.assertIn('Example', html)

    def test_tables_have_header_cells_and_scroll_region(self):
        html = str(render_blocks(parse_body('| A | B |\n| 1 | 2 |')))
        self.assertIn('<th scope="col">A</th>', html)
        self.assertIn('role="region"', html)

    def test_plain_text_strips_markup_for_search_and_notes(self):
        blocks = parse_body('A **bold** ==word==.\n\n- one\n- two\n\n| H1 | H2 |\n| c1 | c2 |')
        self.assertEqual(plain_text(blocks[0]), 'A bold word.')
        self.assertEqual(plain_text(blocks[1]), 'one\ntwo')
        self.assertIn('c1 c2', plain_text(blocks[2]))


class RichLessonEndToEnd(StudioBase):
    def publish_rich(self):
        rev = self.new_lesson(title='Budget basics', body=BODY)
        return self.publish('lesson', rev)

    def test_studio_saves_rich_blocks_and_reopens_the_same_text(self):
        rev = self.new_lesson(title='Budget basics', body=BODY)
        self.assertEqual({b['type'] for b in rev.blocks}, {'heading', 'paragraph', 'list', 'callout', 'table'})
        page = self.author_c.get(f'/studio/lesson/{rev.pk}/edit/')
        self.assertContains(page, '## Why a budget helps')
        self.assertContains(page, '&gt; tip: Start with just one category.')
        self.assertContains(page, 'How to format a lesson')

    def test_a_bad_table_shows_a_message_not_an_error_page(self):
        response = self.author_c.post('/studio/new/lesson/', {'title': 'Bad', 'summary': '', 'body': '| a | b |\n| 1 |'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'same number of cells')
        self.assertFalse(LessonRevision.objects.filter(title='Bad').exists())

    def test_the_review_preview_shows_colour_and_structure(self):
        rev = self.new_lesson(title='Budget basics', body=BODY)
        self.act(self.author_c, 'lesson', rev, 'submit')
        page = self.reviewer_c.get(f'/studio/lesson/{rev.pk}/')
        self.assertContains(page, 'class="lh lh-0"')
        self.assertContains(page, '<mark class="hl hl-yellow">ten minutes</mark>')
        self.assertContains(page, 'callout-tip')

    def test_public_page_is_formatted_safe_and_accessible(self):
        self.publish_rich()
        response = Client().get('/lessons/budget-basics/')
        self.assertContains(response, '<h2 class="lh lh-0">Why a budget helps</h2>')
        self.assertContains(response, '<h2 class="lh lh-1">Next steps</h2>')
        self.assertContains(response, '<strong>where to go</strong>')
        self.assertContains(response, '<mark class="hl hl-green">first</mark>')
        self.assertContains(response, '<th scope="col">Typical return</th>')
        self.assertContains(response, 'content/lesson.css')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)')
        self.assertEqual(audit(response), [])

    def test_search_finds_words_inside_lists_and_tables(self):
        self.publish_rich()
        self.assertContains(Client().get('/search/?q=sacco'), 'Budget basics')
        self.assertContains(Client().get('/search/?q=fixed+costs'), 'Budget basics')

    def test_a_learner_can_highlight_inside_a_list_without_the_markup(self):
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        rev = self.publish_rich()
        user = get_user_model().objects.create_user('rich@example.com', 'strong-password-123', email_verified=True,
                                                    email_verified_at=timezone.now())
        learner = Client()
        learner.force_login(user)
        picker = learner.get('/lessons/budget-basics/notes/')
        self.assertContains(picker, 'Track spending')
        list_block = next(b for b in rev.blocks if b['type'] == 'list' and not b['payload']['ordered'])
        para_block = next(b for b in rev.blocks if b['type'] == 'paragraph')
        ok = learner.post('/lessons/budget-basics/notes/', {'kind': 'highlight', 'body': 'x', 'block_key': list_block['key'],
                                                           'selected_quote': 'Pay yourself first'})
        self.assertEqual(ok.status_code, 302, ok.content[:600])
        ok = learner.post('/lessons/budget-basics/notes/', {'kind': 'highlight', 'body': 'x', 'block_key': para_block['key'],
                                                           'selected_quote': 'where to go'})
        self.assertEqual(ok.status_code, 302)
        wrong = learner.post('/lessons/budget-basics/notes/', {'kind': 'highlight', 'body': 'x', 'block_key': para_block['key'],
                                                              'selected_quote': 'Track spending'})
        self.assertEqual(wrong.status_code, 400)
        note = user.notes.filter(block_key=list_block['key']).get()
        self.assertIsNotNone(note.pk)
