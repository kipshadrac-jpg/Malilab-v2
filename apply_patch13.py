"""Applies the patch-13 edits (playbook step cards) in place. Checks first; changes nothing if a file looks different."""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')

PLAYBOOK_STYLE = '''PLAYBOOK_STYLE = """HOW A PLAYBOOK MUST BE WRITTEN (a hands-on guide the reader FOLLOWS, not a lesson to read)
A playbook always has this shape, in order: GOAL, WHAT YOU NEED, STEPS (one at a time), WHERE THIS LEAVES YOU, then the modules to go deeper. It must be long enough and detailed enough that a person with no help could finish the job by following it.
- `scenario` is the GOAL card: two to four short lines. Start from a real situation the reader recognises, then say what they will have done by the end ("By the end you will have a written monthly budget and a standing order for savings").
- `needs` is WHAT YOU NEED: three to six short items, one per entry (a real list, never one string with items run together). Things to have ready: an M-Pesa statement from the last 3 months, your pay slip, 30 minutes, a notebook or phone notes. Use an empty list only if nothing is genuinely needed.
- `steps` is the heart of the playbook. Write the number of steps the brief asks for (never fewer than 4). Every step is something the reader DOES, not something they read about: "Open your M-Pesa statement and total last month's spending", not "Understand your spending". Each step has:
  * `title`: starts with a verb, specific, under 90 characters.
  * `text`: two to four short paragraphs, a blank line between them, each paragraph two to four lines and one idea. Paragraph 1 says exactly what to do. Paragraph 2 says how: which app, menu, document or calculation, in order. Then a worked example with KES amounts, and what "done" looks like so the reader can tell they finished the step. Use a `- ` list of three to five items when the content is a sequence or a checklist. **Bold** the one key point in a step, and use at most one `==orange:...==` highlight for an action or deadline, `==pink:...==` for a risk or cost, `==green:...==` for a good outcome.
  * `optional`: true only for a genuine bonus step the reader can skip. Leave it out for every normal step.
- Steps follow the order a person would really do them, and each builds on the one before it. Do not repeat the same advice in two steps.
- `outcome` is WHERE THIS LEAVES YOU: two or three short paragraphs. What the reader now has or knows, what to repeat and how often (weekly, monthly), and the one thing to do next. Mention that the modules listed below go deeper.
- `summary`: one or two sentences (under 300 characters) for the playbook card.
- Everything is plain text. No HTML, no markdown links, no images, no `#` headings inside `text`.
- If this involves borrowing, investing or insurance, include one plain sentence in the relevant step or in `outcome` saying this is education, not personal advice, and name the risk."""

STEP_COUNTS = {'short': '4 to 5', 'medium': '6 to 8', 'long': '9 to 12'}
'''

PLAYBOOK_TOOL = '''def playbook_tool():
    step = {'type': 'object', 'additionalProperties': False, 'required': ['title', 'text'], 'properties': {
        'title': {'type': 'string', 'description': 'An action the reader takes, starting with a verb. Under 90 characters.'},
        'text': {'type': 'string', 'description': 'Two to four short paragraphs separated by a blank line; optional "- " bullet lines; **bold** for the key point. Plain text.'},
        'optional': {'type': 'boolean', 'description': 'True only for a genuine bonus step. Leave out otherwise.'}}}
    return {'name': 'submit_draft', 'description': 'Submit the finished playbook draft.', 'input_schema': {
        'type': 'object', 'additionalProperties': False,
        'required': ['title', 'summary', 'scenario', 'needs', 'steps', 'outcome', 'items', 'to_verify'],
        'properties': {
            'title': {'type': 'string'}, 'summary': {'type': 'string', 'description': 'One or two sentences (under 300 characters).'},
            'scenario': {'type': 'string', 'description': 'The GOAL card: the real situation, then what the reader will have done by the end. Two to four short lines.'},
            'needs': {'type': 'array', 'items': {'type': 'string'}, 'description': 'WHAT YOU NEED: three to six short items, one per entry.'},
            'steps': {'type': 'array', 'items': step, 'description': 'The ordered hands-on steps (at least 4).'},
            'outcome': {'type': 'string', 'description': 'WHERE THIS LEAVES YOU: two or three short paragraphs.'},
            'items': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False, 'required': ['key', 'rationale'], 'properties': {
                'key': {'type': 'string'}, 'rationale': {'type': 'string', 'description': 'One sentence on why this module is worth going deeper on.'}}}},
            'to_verify': {'type': 'array', 'items': {'type': 'string'}}}}}


'''

EXTRAS = '''def _step_text(text):
    return '\\n'.join(line.lstrip().lstrip('#').strip() if line.lstrip().startswith('#') else line for line in text.splitlines()).strip()


def playbook_extras(result):
    """The needs list, step cards and closing paragraph, written in the Studio's own text syntax."""
    needs = [n.strip() for n in (result.get('needs') or []) if isinstance(n, str) and n.strip()][:10]
    steps = []
    for s in (result.get('steps') or [])[:12]:
        if isinstance(s, dict) and isinstance(s.get('title'), str) and isinstance(s.get('text'), str):
            title = ' '.join(s['title'].replace('#', '').split())[:120]
            if title:
                steps.append({'title': title, 'text': _step_text(s['text']), 'optional': bool(s.get('optional'))})
    return {'needs': '\\n'.join(needs), 'steps': steps_to_text(steps), 'outcome': _text(result.get('outcome'), 2000)}


def picker_data(kind, result, editor):'''

# (path, old, new, done-marker)
EDITS = [
    ('content/studio/editors.py',
     "from content.richtext import RichTextError, body_from_blocks, parse_body\n",
     "from content.richtext import RichTextError, body_from_blocks, parse_body\nfrom content.guide import clean_outcome, initial_steps_text, parse_needs, parse_steps, with_guide\n",
     'from content.guide import'),
    ('content/studio/editors.py',
     """    scenario = forms.CharField(label='The situation this playbook starts from', required=False,
                               widget=forms.Textarea(attrs={'rows': 5}))
""",
     """    scenario = forms.CharField(label='Goal: the real situation, and what the learner will have done by the end', required=False,
                               widget=forms.Textarea(attrs={'rows': 5}),
                               help_text='Two to four short lines. Shown first, in the Goal card.')
    needs = forms.CharField(label='What you need (one item per line)', required=False, widget=forms.Textarea(attrs={'rows': 5}),
                            help_text='Things to have ready: a document, numbers, an app, some time. Three to six lines.')
    steps = forms.CharField(label='Steps', required=False, widget=forms.Textarea(attrs={'rows': 24}),
                            help_text='Start each step with a heading line: ### Open your M-Pesa statement. Add (optional) after the title for a bonus step. '
                                      'Under it write two to four short paragraphs, a blank line between them; use - for bullets, **bold** for the key point, '
                                      'and ==orange:text== (or green, pink, blue, yellow) to highlight a few words.')
    outcome = forms.CharField(label='Where this leaves you', required=False, widget=forms.Textarea(attrs={'rows': 4}),
                              help_text='Two or three short lines: what the learner now has, and the one thing to do next.')

    parsed_steps = ()

    def clean_needs(self):
        return '\\n'.join(parse_needs(self.cleaned_data.get('needs', '')))

    def clean_steps(self):
        text = self.cleaned_data.get('steps', '')
        self.parsed_steps = parse_steps(text) if text.strip() else []
        return text

    def clean_outcome(self):
        return clean_outcome(self.cleaned_data.get('outcome', ''))
""", 'def clean_needs'),
    ('content/studio/editors.py',
     "        return {'title': self.revision.title, 'summary': self.revision.summary, 'scenario': self.revision.scenario}\n",
     """        steps_text, outcome = initial_steps_text(self.revision)
        return {'title': self.revision.title, 'summary': self.revision.summary, 'scenario': self.revision.scenario,
                'needs': '\\n'.join(n for n in (self.revision.assumptions or []) if isinstance(n, str)),
                'steps': steps_text, 'outcome': outcome}
""", 'initial_steps_text(self.revision)'),
    ('content/studio/editors.py',
     "        fields = dict(title=d['title'], summary=d['summary'], scenario=d['scenario'])\n",
     """        steps = parse_steps(d['steps']) if d['steps'].strip() else []
        meta = with_guide(self.revision.discovery_metadata if self.revision else {}, steps, d['outcome'])
        fields = dict(title=d['title'], summary=d['summary'], scenario=d['scenario'],
                      assumptions=parse_needs(d['needs']), discovery_metadata=meta)
""", 'with_guide(self.revision'),
    ('content/templates/studio/revision.html',
     "{% if preview.scenario %}<p>{{ preview.scenario }}</p>{% endif %}",
     '{% include "content/_playbook_guide.html" with revision=rev %}\n    <h3 class="pg-more-h">Recommended modules</h3>', '_playbook_guide.html'),
    ('content/studio/ai_views.py', "label='Length (lessons)'", "label='Length (lessons and playbooks)'", 'lessons and playbooks'),
    # ---- AI assistant
    ('content/studio/ai.py',
     "from content.richtext import RichTextError, parse_body\n",
     "from content.richtext import RichTextError, parse_body\nfrom content.guide import steps_to_text\n", 'import steps_to_text'),
    ('content/studio/ai.py', "def lesson_tool():", PLAYBOOK_STYLE + "\n\ndef lesson_tool():", 'PLAYBOOK_STYLE = '),
    ('content/studio/ai.py',
     "STYLES = {'lesson': LESSON_STYLE, 'practice': PRACTICE_STYLE, 'module': PICKER_STYLE, 'playbook': PICKER_STYLE}",
     "STYLES = {'lesson': LESSON_STYLE, 'practice': PRACTICE_STYLE, 'module': PICKER_STYLE,\n          'playbook': PLAYBOOK_STYLE + '\\n\\n' + PICKER_STYLE}", "'playbook': PLAYBOOK_STYLE"),
    ('content/studio/ai.py',
     """    if kind == 'practice':
        lines.append(f"Number of questions: {brief.get('question_count') or 6}")
""",
     """    if kind == 'practice':
        lines.append(f"Number of questions: {brief.get('question_count') or 6}")
    if kind == 'playbook':
        lines.append(f"Number of steps: {STEP_COUNTS.get(brief.get('length'), STEP_COUNTS['medium'])}")
""", 'Number of steps'),
    ('content/studio/ai.py', "def picker_data(kind, result, editor):", EXTRAS, 'def playbook_extras'),
    ('content/studio/ai.py',
     "        data.update(summary=_text(result.get('summary'), 2000), scenario=_text(result.get('scenario'), 4000))\n",
     "        data.update(summary=_text(result.get('summary'), 2000), scenario=_text(result.get('scenario'), 4000))\n        data.update(playbook_extras(result))\n",
     'playbook_extras(result))'),
    ('content/studio/ai.py',
     """        return LENGTHS.get(brief.get('length'), LENGTHS['medium'])[1]
    return 5000
""",
     """        return LENGTHS.get(brief.get('length'), LENGTHS['medium'])[1]
    if kind == 'playbook':
        return {'short': 6000, 'medium': 8000, 'long': 10000}.get(brief.get('length'), 8000)
    return 5000
""", "'short': 6000"),
    ('content/studio/ai.py',
     """        raise ValidationError(problems or ['The draft was not valid.'])
    return editor
""",
     """        raise ValidationError(problems or ['The draft was not valid.'])
    if kind == 'playbook' and len(getattr(editor.form, 'parsed_steps', ())) < 3:
        raise ValidationError(['A playbook needs at least 4 real hands-on steps in the steps list, each with a verb title and two to four short paragraphs.'])
    return editor
""", "len(getattr(editor.form, 'parsed_steps'"),
    # ---- the existing playbook AI test must now return a full playbook
    ('content/test_ai_assistant.py',
     """        good = {'title': 'First salary', 'summary': 'What to do with your first pay.', 'scenario': 'You just got paid.',
                'to_verify': [], 'items': [{'key': f'module-{module.pk}', 'rationale': 'Start with saving.'}]}
""",
     """        good = {'title': 'First salary', 'summary': 'What to do with your first pay.', 'scenario': 'You just got paid.',
                'needs': ['Your pay slip'], 'outcome': 'You now have a plan.',
                'steps': [{'title': 'Open your pay slip', 'text': 'Find the net pay.'}, {'title': 'List fixed costs', 'text': 'Rent and fare.'},
                          {'title': 'Move savings first', 'text': 'Do it on pay day.'}, {'title': 'Review next month', 'text': 'Adjust.'}],
                'to_verify': [], 'items': [{'key': f'module-{module.pk}', 'rationale': 'Start with saving.'}]}
""", "'needs': ['Your pay slip']"),
]
APPENDS = []


def main():
    files = {}
    for path, old, new, done in EDITS:
        f = ROOT / path
        if not f.exists():
            sys.exit(f'STOP: {path} not found under {ROOT}')
        text = files.setdefault(f, f.read_text())
        if done in text:
            continue
        if text.count(old) != 1:
            sys.exit(f'STOP: expected text not found exactly once in {path}: {old[:70]!r}. Nothing was changed.')
        files[f] = text.replace(old, new, 1)
    # replace the old playbook tool (between two markers that each occur once)
    f = ROOT / 'content/studio/ai.py'
    text = files.setdefault(f, f.read_text())
    if "'required': ['title', 'summary', 'scenario', 'needs'" not in text:
        a, b = text.find('def playbook_tool():'), text.find("TOOLS = {'lesson'")
        if a < 0 or b < a or text.count('def playbook_tool():') != 1:
            sys.exit('STOP: could not find the playbook tool in content/studio/ai.py. Nothing was changed.')
        files[f] = text[:a] + PLAYBOOK_TOOL + text[b:]
    for f, text in files.items():
        f.write_text(text)
    print('Patch 13 edits applied.')


main()
