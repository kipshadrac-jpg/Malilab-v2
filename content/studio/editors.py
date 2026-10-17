"""Guided editors: one small class per kind of content. Drafts only; history is never touched."""
import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils.text import slugify

from content.richtext import RichTextError, body_from_blocks, parse_body
from content.guide import clean_outcome, initial_steps_text, parse_needs, parse_steps, with_guide
from content.models import (LessonRevision, ModuleLearningRequirement, ModuleRevision,
                            PlaybookModuleRecommendation, PlaybookRevision, PracticeActivityRevision)
from practice.schema import IDENTIFIER, MAX_TEXT, TEXT_TYPES, validate_schema
from .kinds import KINDS, identity_of

CLASSIFICATIONS = (('required', 'Required'), ('recommended', 'Recommended'), ('optional', 'Optional'))
QUESTION_TYPES = (
    ('short_text', 'Short answer (a line)'), ('long_text', 'Long answer (a paragraph)'),
    ('single_choice', 'Pick one option'), ('multiple_choice', 'Pick several options'),
    ('integer', 'Whole number'), ('decimal_amount', 'Amount in KES'),
)
TYPE_LABELS = dict(QUESTION_TYPES)
DEFAULT_MAX = {'short_text': 280, 'long_text': 2000}
MIN_ROWS, MAX_ROWS = 5, 40


def unique_slug(identity_model, title):
    base = (slugify(title) or 'untitled')[:150].strip('-') or 'untitled'
    slug, n = base, 2
    while identity_model.objects.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


class Editor:
    kind = None
    template = None

    def __init__(self, revision=None, data=None):
        self.revision, self.data, self.errors = revision, data, []
        self.build()

    def build(self):
        raise NotImplementedError

    def valid(self):
        raise NotImplementedError

    def save(self, user):
        raise NotImplementedError

    def context(self):
        return {}

    def _create_identity_and_revision(self, user, **fields):
        cfg = KINDS[self.kind]
        identity = cfg['identity_model'].objects.create(slug=unique_slug(cfg['identity_model'], fields['title']))
        return cfg['model'].objects.create(**{cfg['identity']: identity}, revision_number=1, author=user,
                                           status='draft', **fields)

    def _update_revision(self, **fields):
        for name, value in fields.items():
            setattr(self.revision, name, value)
        self.revision.save()
        return self.revision


# ------------------------------------------------------------------ Lesson
class LessonForm(forms.Form):
    title = forms.CharField(label='Title', max_length=240)
    summary = forms.CharField(label='Summary (one or two sentences shown above the lesson)', max_length=2000,
                              required=False, widget=forms.Textarea(attrs={'rows': 3}))
    body = forms.CharField(label='Lesson text', widget=forms.Textarea(attrs={'rows': 18}),
                           help_text='Short paragraphs, a blank line between them. Use ## for subheadings, - for bullets, > tip: for coloured boxes, | for tables.')

    def clean_body(self):
        body = self.cleaned_data['body']
        try:
            parse_body(body)
        except RichTextError as exc:
            raise forms.ValidationError(str(exc))
        return body


class LessonEditor(Editor):
    kind, template = 'lesson', 'studio/edit_lesson.html'

    def build(self):
        initial = {}
        if self.revision:
            blocks = sorted(self.revision.blocks or [], key=lambda b: b['position'])
            initial = {'title': self.revision.title, 'summary': self.revision.summary,
                       'body': body_from_blocks(blocks)}
        self.form = LessonForm(self.data, initial=initial)

    def valid(self):
        return self.form.is_valid()

    def context(self):
        return {'form': self.form}

    @transaction.atomic
    def save(self, user):
        d = self.form.cleaned_data
        if self.revision is None:
            return self._create_identity_and_revision(user, title=d['title'], summary=d['summary'],
                                                      blocks=parse_body(d['body']))
        return self._update_revision(title=d['title'], summary=d['summary'],
                                     blocks=parse_body(d['body'], self.revision.blocks))


# ------------------------------------------------------------------ Practice
class PracticeForm(forms.Form):
    title = forms.CharField(label='Title', max_length=240)
    instructions = forms.CharField(label='Instructions (what the learner should do)', required=False,
                                   widget=forms.Textarea(attrs={'rows': 4}))
    prompt = forms.CharField(label='Scenario or prompt', required=False, widget=forms.Textarea(attrs={'rows': 4}))
    safety_text = forms.CharField(label='Safety note (for example: this is not personal financial advice)',
                                  required=False, widget=forms.Textarea(attrs={'rows': 2}))


def make_id(text, used, fallback='item'):
    base = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')[:40] or fallback
    if not re.match(r'[a-z]', base):
        base = f'{fallback}_{base}'[:40]
    candidate, n = base, 2
    while candidate in used:
        candidate = f'{base}_{n}'
        n += 1
    used.add(candidate)
    return candidate


def rows_from_schema(schema):
    rows = []
    for q in (schema or {}).get('questions', []):
        constraints = q.get('constraints') or {}
        row = {'id': q['id'], 'label': q['label'], 'type': q['type'], 'required': q['required'],
               'options': '\n'.join(o['label'] for o in q.get('options', [])), 'min': '', 'max': ''}
        if q['type'] in TEXT_TYPES:
            row['max'] = str(constraints.get('max_length', ''))
        else:
            row['min'] = '' if 'minimum' not in constraints else str(constraints['minimum'])
            row['max'] = '' if 'maximum' not in constraints else str(constraints['maximum'])
        rows.append(row)
    return rows


def rows_from_post(post, count):
    rows = []
    for i in range(count):
        rows.append({'id': post.get(f'q{i}_id', '').strip(), 'label': post.get(f'q{i}_label', '').strip(),
                     'type': post.get(f'q{i}_type', 'short_text'), 'required': post.get(f'q{i}_required') == 'on',
                     'options': post.get(f'q{i}_options', ''), 'min': post.get(f'q{i}_min', '').strip(),
                     'max': post.get(f'q{i}_max', '').strip()})
    return rows


def _whole(text, name, number, errors):
    if text == '':
        return None
    try:
        return int(text)
    except ValueError:
        errors.append(f'Question {number}: {name} must be a whole number.')
        return None


def _amount(text, name, number, errors):
    if text == '':
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        errors.append(f'Question {number}: {name} must be an amount such as 5000 or 250.50.')
        return None
    return format(value, 'f')


def build_schema(rows):
    questions, errors, used = [], [], set()
    for number, row in enumerate(rows, 1):
        if not row['label']:
            continue
        if row['type'] not in TYPE_LABELS:
            errors.append(f'Question {number}: choose a type.')
            continue
        qid = row['id'] if (IDENTIFIER.fullmatch(row['id'] or '') and row['id'] not in used) else ''
        if qid:
            used.add(qid)
        else:
            qid = make_id(row['label'], used, 'question')
        q = {'id': qid, 'type': row['type'], 'label': row['label'], 'required': bool(row['required'])}
        kind = row['type']
        if kind in TEXT_TYPES:
            limit = _whole(row['max'], 'the answer length limit', number, errors)
            q['constraints'] = {'max_length': limit if limit else DEFAULT_MAX[kind]}
            if q['constraints']['max_length'] > MAX_TEXT[kind] or q['constraints']['max_length'] < 1:
                errors.append(f'Question {number}: the length limit must be between 1 and {MAX_TEXT[kind]}.')
        elif kind in ('single_choice', 'multiple_choice'):
            labels = [line.strip() for line in row['options'].splitlines() if line.strip()]
            if len(labels) < 2:
                errors.append(f'Question {number}: give at least two options, one per line.')
            option_ids = set()
            q['options'] = [{'id': make_id(label, option_ids, 'option'), 'label': label} for label in labels]
        elif kind == 'integer':
            low, high = _whole(row['min'], 'the smallest value', number, errors), _whole(row['max'], 'the largest value', number, errors)
            constraints = {k: v for k, v in (('minimum', low), ('maximum', high)) if v is not None}
            if constraints:
                q['constraints'] = constraints
        else:
            low, high = _amount(row['min'], 'the smallest amount', number, errors), _amount(row['max'], 'the largest amount', number, errors)
            q['constraints'] = {'currency': 'KES', **{k: v for k, v in (('minimum', low), ('maximum', high)) if v is not None}}
        questions.append(q)
    if not questions and not errors:
        errors.append('Add at least one question.')
    if errors:
        return None, errors
    try:
        return validate_schema({'schema_version': 1, 'questions': questions}), []
    except ValidationError as exc:
        return None, [m for m in exc.messages]


class PracticeEditor(Editor):
    kind, template = 'practice', 'studio/edit_practice.html'

    def build(self):
        initial = {}
        if self.revision:
            initial = {'title': self.revision.title, 'instructions': self.revision.instructions,
                       'prompt': self.revision.prompt, 'safety_text': self.revision.safety_text}
        self.form = PracticeForm(self.data, initial=initial)
        self.schema, self.row_errors = None, []
        if self.data is not None:
            try:
                count = max(MIN_ROWS, min(MAX_ROWS, int(self.data.get('row_count', MIN_ROWS))))
            except ValueError:
                count = MIN_ROWS
            self.rows = rows_from_post(self.data, count)
        else:
            existing = rows_from_schema(self.revision.response_schema if self.revision else {})
            self.rows = existing + [self.blank_row() for _ in range(max(2, MIN_ROWS - len(existing)))]

    @staticmethod
    def blank_row():
        return {'id': '', 'label': '', 'type': 'short_text', 'required': True, 'options': '', 'min': '', 'max': ''}

    def add_rows(self, extra=5):
        self.rows += [self.blank_row() for _ in range(extra)]
        del self.rows[MAX_ROWS:]

    def valid(self):
        ok = self.form.is_valid()
        self.schema, self.row_errors = build_schema(self.rows)
        return ok and not self.row_errors

    def context(self):
        numbered = [{**row, 'n': i + 1, 'i': i} for i, row in enumerate(self.rows)]
        return {'form': self.form, 'rows': numbered, 'row_count': len(self.rows), 'question_types': QUESTION_TYPES,
                'row_errors': self.row_errors}

    @transaction.atomic
    def save(self, user):
        d = self.form.cleaned_data
        fields = dict(title=d['title'], instructions=d['instructions'], prompt=d['prompt'],
                      safety_text=d['safety_text'], response_schema=self.schema)
        if self.revision is None:
            return self._create_identity_and_revision(user, **fields)
        return self._update_revision(**fields)


# ------------------------------------------------------------------ Module / Playbook pickers
def _int(text, default):
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


class PickerEditor(Editor):
    """Shared by Module and Playbook: a title, some text, and an ordered choice of published items."""

    def candidate_rows(self):
        raise NotImplementedError

    def after_build(self):
        pass

    def build(self):
        self.form = self.form_class(self.data, initial=self.initial())
        self.candidates = self.candidate_rows()
        if self.data is not None:
            for c in self.candidates:
                c['selected'] = self.data.get(f"inc_{c['key']}") == 'on'
                c['position'] = _int(self.data.get(f"pos_{c['key']}"), 999)
                c['classification'] = self.data.get(f"cls_{c['key']}", c.get('classification', 'required'))
                c['rationale'] = self.data.get(f"rat_{c['key']}", '').strip()
        self.picked = []

    def chosen(self):
        picked = [c for c in self.candidates if c['selected']]
        return sorted(picked, key=lambda c: (c['position'], c['sort']))

    def valid(self):
        ok = self.form.is_valid()
        self.picked = self.chosen()
        if not self.picked:
            self.errors.append(self.nothing_chosen)
        return ok and bool(self.picked)

    def context(self):
        return {'form': self.form, 'candidates': self.candidates, 'classifications': CLASSIFICATIONS}


class ModuleForm(forms.Form):
    title = forms.CharField(label='Title', max_length=240)
    description = forms.CharField(label='What this module helps the learner do', required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))


class ModuleEditor(PickerEditor):
    kind, template, form_class = 'module', 'studio/edit_module.html', ModuleForm
    nothing_chosen = 'Choose at least one lesson or practice activity.'

    def initial(self):
        return {'title': self.revision.title, 'description': self.revision.description} if self.revision else {}

    def candidate_rows(self):
        existing = {}
        if self.revision:
            for r in self.revision.learning_requirements.filter(active=True).select_related(
                    'lesson_revision__lesson', 'practice_revision__activity'):
                target = r.lesson_revision or r.practice_revision
                existing[(r.target_kind, target.pk)] = r
        rows, seen = [], set()
        sources = [
            ('lesson', LessonRevision.objects.filter(status='published', lesson__current_published_revision_id=F('pk')).select_related('lesson')),
            ('practice', PracticeActivityRevision.objects.filter(status='published', activity__current_published_revision_id=F('pk')).select_related('activity')),
        ]
        for kind, qs in sources:
            for rev in qs.order_by('title', 'pk'):
                seen.add((kind, rev.pk))
                rows.append(self._row(kind, rev, existing.get((kind, rev.pk))))
        for (kind, pk), req in existing.items():   # keep links that are no longer the current revision visible
            if (kind, pk) not in seen:
                rows.append(self._row(kind, req.lesson_revision or req.practice_revision, req))
        for number, row in enumerate(rows):
            row['sort'] = number
        return rows

    @staticmethod
    def _row(kind, rev, req):
        identity = identity_of(kind, rev)
        return {'key': f'{kind}-{rev.pk}', 'kind': kind, 'kind_label': KINDS[kind]['label'], 'title': rev.title,
                'slug': identity.slug, 'rev': rev, 'selected': req is not None,
                'position': req.position if req else 999, 'classification': req.classification if req else 'required',
                'rationale': ''}

    @transaction.atomic
    def save(self, user):
        d = self.form.cleaned_data
        if self.revision is None:
            revision = self._create_identity_and_revision(user, title=d['title'], description=d['description'])
        else:
            revision = self._update_revision(title=d['title'], description=d['description'])
        for old in list(revision.learning_requirements.all()):
            old.delete()
        for position, c in enumerate(self.picked, 1):
            cls = c['classification'] if c['classification'] in dict(CLASSIFICATIONS) else 'required'
            ModuleLearningRequirement.objects.create(
                module_revision=revision, target_kind=c['kind'], position=position, classification=cls, active=True,
                **{'lesson_revision' if c['kind'] == 'lesson' else 'practice_revision': c['rev']})
        return revision


class PlaybookForm(forms.Form):
    title = forms.CharField(label='Title', max_length=240)
    summary = forms.CharField(label='Summary (what this playbook helps with)', max_length=2000,
                              widget=forms.Textarea(attrs={'rows': 3}))
    scenario = forms.CharField(label='Goal: the real situation, and what the learner will have done by the end', required=False,
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
        return '\n'.join(parse_needs(self.cleaned_data.get('needs', '')))

    def clean_steps(self):
        text = self.cleaned_data.get('steps', '')
        self.parsed_steps = parse_steps(text) if text.strip() else []
        return text

    def clean_outcome(self):
        return clean_outcome(self.cleaned_data.get('outcome', ''))


class PlaybookEditor(PickerEditor):
    kind, template, form_class = 'playbook', 'studio/edit_playbook.html', PlaybookForm
    nothing_chosen = 'Choose at least one module.'

    def initial(self):
        if not self.revision:
            return {}
        steps_text, outcome = initial_steps_text(self.revision)
        return {'title': self.revision.title, 'summary': self.revision.summary, 'scenario': self.revision.scenario,
                'needs': '\n'.join(n for n in (self.revision.assumptions or []) if isinstance(n, str)),
                'steps': steps_text, 'outcome': outcome}

    def candidate_rows(self):
        existing = {}
        if self.revision:
            for r in self.revision.module_recommendations.filter(active=True).select_related('module_revision__module'):
                existing[r.module_revision_id] = r
        qs = (ModuleRevision.objects.filter(status='published', module__current_published_revision_id=F('pk'))
              .select_related('module').order_by('title', 'pk'))
        rows, seen = [], set()
        for rev in qs:
            seen.add(rev.pk)
            rows.append(self._row(rev, existing.get(rev.pk)))
        for pk, rec in existing.items():
            if pk not in seen:
                rows.append(self._row(rec.module_revision, rec))
        for number, row in enumerate(rows):
            row['sort'] = number
        return rows

    @staticmethod
    def _row(rev, rec):
        return {'key': f'module-{rev.pk}', 'kind': 'module', 'kind_label': 'Module', 'title': rev.title,
                'slug': rev.module.slug, 'rev': rev, 'selected': rec is not None,
                'position': rec.position if rec else 999, 'classification': 'required',
                'rationale': rec.rationale if rec else ''}

    @transaction.atomic
    def save(self, user):
        d = self.form.cleaned_data
        steps = parse_steps(d['steps']) if d['steps'].strip() else []
        meta = with_guide(self.revision.discovery_metadata if self.revision else {}, steps, d['outcome'])
        fields = dict(title=d['title'], summary=d['summary'], scenario=d['scenario'],
                      assumptions=parse_needs(d['needs']), discovery_metadata=meta)
        revision = (self._create_identity_and_revision(user, **fields) if self.revision is None
                    else self._update_revision(**fields))
        for old in list(revision.module_recommendations.all()):
            old.delete()
        for position, c in enumerate(self.picked, 1):
            PlaybookModuleRecommendation.objects.create(
                playbook_revision=revision, module_revision=c['rev'], position=position,
                rationale=c['rationale'], active=True)
        return revision


EDITORS = {'lesson': LessonEditor, 'practice': PracticeEditor, 'module': ModuleEditor, 'playbook': PlaybookEditor}
