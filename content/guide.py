"""The step-by-step part of a playbook: what you need, numbered step cards, and where this leaves you.

No database change: the "what you need" list lives in PlaybookRevision.assumptions, and the steps and the
closing paragraph live under the 'guide' key of PlaybookRevision.discovery_metadata. Everything is plain text
in the Studio and is HTML-escaped before it is shown, so nothing a person or the AI writes can inject markup.

Studio text syntax for steps:
    ### Open your M-Pesa statement          (add "(optional)" after the title for a bonus step)

    A short paragraph. Another short paragraph.

    - a bullet
    - another bullet
"""
import re

from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .richtext import render_inline

MAX_STEPS, MAX_NEEDS = 12, 10
TITLE_MAX, NEED_MAX, CHUNK_MAX, STEP_MAX, OUTCOME_MAX = 120, 200, 700, 2600, 2000
TONES = 6                                   # step cards cycle through six colours

_HEAD = re.compile(r'^###\s*(.*?)\s*$')
_OPTIONAL = re.compile(r'\s*\((?:optional)\)\s*$', re.I)
_BULLET = re.compile(r'^\s*[-*•]\s+(.*)$')


def _plain(text):
    return re.sub(r'\n{3,}', '\n\n', str(text or '').replace('\r\n', '\n').replace('\r', '\n')).strip()


def parse_needs(text):
    items, errors = [], []
    for raw in _plain(text).split('\n'):
        line = (_BULLET.match(raw).group(1) if _BULLET.match(raw) else raw).strip()
        if not line:
            continue
        if len(line) > NEED_MAX:
            errors.append(f'Keep each "what you need" line under {NEED_MAX} characters ("{line[:30]}…").')
        items.append(line)
    if len(items) > MAX_NEEDS:
        errors.append(f'List at most {MAX_NEEDS} things under "what you need".')
    if errors:
        raise ValidationError(errors)
    return items


def _check_text(number, text, errors):
    if not text:
        errors.append(f'Step {number} has a title but no text. Say what to do and how.')
        return
    if len(text) > STEP_MAX:
        errors.append(f'Step {number} is too long ({len(text)} characters). Keep it under {STEP_MAX}, or split it into two steps.')
    for chunk in text.split('\n\n'):
        if len(chunk) > CHUNK_MAX:
            errors.append(f'Step {number} has a paragraph that is too long. Break it into shorter paragraphs or a list.')
            break


def parse_steps(text):
    """Studio text -> [{'title', 'text', 'optional'}]. Raises ValidationError with plain messages."""
    steps, errors, current = [], [], None
    for raw in _plain(text).split('\n'):
        m = _HEAD.match(raw.strip())
        if m:
            title = m.group(1)
            optional = bool(_OPTIONAL.search(title))
            title = _OPTIONAL.sub('', title).strip()
            if not title:
                errors.append('A step heading (###) has no title.')
            current = {'title': title[:TITLE_MAX], 'lines': [], 'optional': optional}
            if len(title) > TITLE_MAX:
                errors.append(f'Step {len(steps) + 1}: keep the title under {TITLE_MAX} characters.')
            steps.append(current)
        elif current is None:
            if raw.strip():
                errors.append('Start every step with a heading line like: ### Open your M-Pesa statement')
                break
        else:
            current['lines'].append(raw.rstrip())
    out = []
    for number, s in enumerate(steps, 1):
        body = _plain('\n'.join(s['lines']))
        _check_text(number, body, errors)
        out.append({'title': s['title'], 'text': body, 'optional': s['optional']})
    if len(out) > MAX_STEPS:
        errors.append(f'Use at most {MAX_STEPS} steps. Split a big playbook into two.')
    if errors:
        raise ValidationError(errors)
    return out


def steps_to_text(steps):
    parts = []
    for s in steps or []:
        if isinstance(s, dict) and s.get('title'):
            head = '### ' + s['title'] + (' (optional)' if s.get('optional') else '')
            parts.append(head + '\n\n' + (s.get('text') or ''))
    return '\n\n'.join(parts)


def clean_outcome(text):
    text = _plain(text)
    if len(text) > OUTCOME_MAX:
        raise ValidationError(f'Keep "where this leaves you" under {OUTCOME_MAX} characters.')
    return text


def render_text(text):
    """Paragraphs and bullet lists -> safe HTML. Inline **bold** and ==colour:text== work as in lessons."""
    html, para, bullets = [], [], []

    def flush():
        if para:
            html.append('<p>' + render_inline(' '.join(para)) + '</p>')
            para.clear()
        if bullets:
            html.append('<ul>' + ''.join('<li>' + render_inline(b) + '</li>' for b in bullets) + '</ul>')
            bullets.clear()

    for raw in _plain(text).split('\n'):
        line = raw.strip()
        if not line:
            flush()
            continue
        m = _BULLET.match(line)
        if m:
            if para:
                flush()
            bullets.append(m.group(1).strip())
        else:
            if bullets:
                flush()
            para.append(line)
    flush()
    return mark_safe(''.join(html))


def guide_of(revision):
    """Everything the page needs to show a playbook's step cards. Safe on old playbooks that have none."""
    meta = revision.discovery_metadata if isinstance(revision.discovery_metadata, dict) else {}
    raw = meta.get('guide') if isinstance(meta.get('guide'), dict) else {}
    needs = [{'tone': i % TONES, 'html': render_inline(n)} for i, n in
             enumerate(n.strip() for n in (revision.assumptions or []) if isinstance(n, str) and n.strip())]
    steps = []
    for s in raw.get('steps') or []:
        if isinstance(s, dict) and isinstance(s.get('title'), str) and s['title'].strip():
            n = len(steps)
            steps.append({'n': n + 1, 'tone': n % TONES, 'title': s['title'].strip(), 'optional': bool(s.get('optional')),
                          'html': render_text(s.get('text') if isinstance(s.get('text'), str) else '')})
    outcome = raw.get('outcome') if isinstance(raw.get('outcome'), str) else ''
    return {'needs': needs, 'steps': steps, 'outcome': render_text(outcome) if outcome.strip() else '',
            'has_steps': bool(steps)}


def with_guide(existing_meta, steps, outcome):
    """discovery_metadata with the guide replaced and every other key left alone."""
    meta = dict(existing_meta) if isinstance(existing_meta, dict) else {}
    if steps or outcome:
        meta['guide'] = {'version': 1, 'steps': steps, 'outcome': outcome}
    else:
        meta.pop('guide', None)
    return meta


def initial_steps_text(revision):
    meta = revision.discovery_metadata if isinstance(revision.discovery_metadata, dict) else {}
    raw = meta.get('guide') if isinstance(meta.get('guide'), dict) else {}
    return steps_to_text(raw.get('steps')), raw.get('outcome') if isinstance(raw.get('outcome'), str) else ''
