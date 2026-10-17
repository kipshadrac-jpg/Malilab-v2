"""Rich, skimmable lesson blocks: parse, validate, serialise and safely render.

Stored shapes (all blocks keep {key, type, position, payload}):
  paragraph {text}            heading {text, level 2|3}
  list      {items, ordered}  callout {tone, text}
  table     {header, rows}
Inline markup inside text fields: **bold**, ==highlight==, ==blue:coloured highlight==.
Everything is HTML-escaped before markup is applied, so no raw HTML can ever be stored or shown.
"""
import re
import uuid

from django.utils.html import escape
from django.utils.safestring import mark_safe

TONES = ('tip', 'warning', 'key', 'example', 'note')
TONE_LABELS = {'tip': 'Tip', 'warning': 'Watch out', 'key': 'Key idea', 'example': 'Example', 'note': 'Note'}
HIGHLIGHTS = ('yellow', 'green', 'blue', 'pink', 'orange')
HEADING_COLOURS = 5
MAX_TEXT, MAX_HEADING, MAX_ITEMS, MAX_ITEM, MAX_COLS, MAX_ROWS, MAX_CELL = 5000, 200, 60, 500, 8, 40, 300


class RichTextError(ValueError):
    pass


# ------------------------------------------------------------------ inline
_HL = re.compile(r'==(?:(' + '|'.join(HIGHLIGHTS) + r'):)?(.+?)==')
_BOLD = re.compile(r'\*\*(.+?)\*\*')


def render_inline(text):
    html = escape(str(text))
    html = _HL.sub(lambda m: f'<mark class="hl hl-{m.group(1) or "yellow"}">{m.group(2)}</mark>', html)
    html = _BOLD.sub(r'<strong>\1</strong>', html)
    return mark_safe(html)


def strip_inline(text):
    text = _HL.sub(lambda m: m.group(2), str(text))
    return _BOLD.sub(r'\1', text)


def plain_text(block):
    """Readable plain text of any block (markup removed) for search and note anchoring."""
    if not isinstance(block, dict) or not isinstance(block.get('payload'), dict):
        return ''
    p = block['payload']
    parts = []
    if isinstance(p.get('text'), str):
        parts.append(p['text'])
    if isinstance(p.get('items'), list):
        parts += [i for i in p['items'] if isinstance(i, str)]
    if isinstance(p.get('header'), list):
        parts.append(' '.join(c for c in p['header'] if isinstance(c, str)))
    if isinstance(p.get('rows'), list):
        parts += [' '.join(c for c in r if isinstance(c, str)) for r in p['rows'] if isinstance(r, list)]
    return '\n'.join(strip_inline(x) for x in parts)


# ------------------------------------------------------------------ validation
def _text(value, limit, what):
    if not isinstance(value, str) or not value.strip():
        raise RichTextError(f'{what} cannot be empty.')
    if len(value) > limit:
        raise RichTextError(f'{what} is too long (limit {limit} characters).')


def validate_payload(btype, p):
    """Raise RichTextError when the payload is not exactly the approved shape for this block type."""
    if not isinstance(p, dict):
        raise RichTextError('payload must be an object')
    if btype == 'paragraph':
        if set(p) != {'text'}:
            raise RichTextError('paragraph payload must be exactly {text}')
        _text(p['text'], MAX_TEXT, 'Paragraph text')
    elif btype == 'heading':
        if set(p) != {'text', 'level'}:
            raise RichTextError('heading payload must be exactly {text, level}')
        _text(p['text'], MAX_HEADING, 'Heading')
        if isinstance(p['level'], bool) or p['level'] not in (2, 3):
            raise RichTextError('heading level must be 2 or 3')
    elif btype == 'list':
        if set(p) != {'items', 'ordered'}:
            raise RichTextError('list payload must be exactly {items, ordered}')
        if not isinstance(p['ordered'], bool):
            raise RichTextError('list ordered must be true or false')
        if not isinstance(p['items'], list) or not 1 <= len(p['items']) <= MAX_ITEMS:
            raise RichTextError(f'a list needs 1 to {MAX_ITEMS} items')
        for item in p['items']:
            _text(item, MAX_ITEM, 'List item')
    elif btype == 'callout':
        if set(p) != {'tone', 'text'}:
            raise RichTextError('callout payload must be exactly {tone, text}')
        if p['tone'] not in TONES:
            raise RichTextError('callout tone must be one of ' + ', '.join(TONES))
        _text(p['text'], MAX_TEXT, 'Callout text')
    elif btype == 'table':
        if set(p) != {'header', 'rows'}:
            raise RichTextError('table payload must be exactly {header, rows}')
        header, rows = p['header'], p['rows']
        if not isinstance(header, list) or not 2 <= len(header) <= MAX_COLS:
            raise RichTextError(f'a table needs 2 to {MAX_COLS} columns')
        for cell in header:
            _text(cell, MAX_CELL, 'Table heading')
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_ROWS:
            raise RichTextError(f'a table needs 1 to {MAX_ROWS} rows')
        for row in rows:
            if not isinstance(row, list) or len(row) != len(header):
                raise RichTextError('every table row must have the same number of cells as the heading row')
            for cell in row:
                if not isinstance(cell, str) or len(cell) > MAX_CELL:
                    raise RichTextError('table cells must be text of at most %d characters' % MAX_CELL)
    else:
        raise RichTextError('unsupported block type')


BLOCK_TYPES = ('paragraph', 'heading', 'list', 'callout', 'table')


# ------------------------------------------------------------------ parsing the Studio text
_BULLET = re.compile(r'^\s*[-*•]\s+(.*)$')
_NUMBER = re.compile(r'^\s*\d{1,2}[.)]\s+(.*)$')
_TONE = re.compile(r'^>\s?(?:(' + '|'.join(TONES) + r')\s*:\s*)?(.*)$', re.I)
_SPLIT = re.compile(r'(?<!\\)\|')
_SEP = re.compile(r'^\|?[\s:|-]*-[\s:|-]*\|?$')


_HEADING = re.compile(r'^(#{2,3})(?:\s+(.*))?$')


def _special(line):
    s = line.strip()
    return bool(_HEADING.match(s) or s.startswith(('>', '|')) or _BULLET.match(line) or _NUMBER.match(line))


def _cells(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|') and not line.endswith('\\|'):
        line = line[:-1]
    return [c.strip().replace('\\|', '|') for c in _SPLIT.split(line)]


def parse_body(body, existing=()):
    """Turn Studio text into validated lesson blocks, reusing existing block keys by position."""
    keys = [b['key'] for b in sorted(existing, key=lambda b: b['position'])]
    lines = body.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    raw, i = [], 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
        elif _HEADING.match(s):
            m = _HEADING.match(s)
            raw.append(('heading', {'text': (m.group(2) or '').strip(), 'level': len(m.group(1))})); i += 1
        elif s.startswith('>'):
            boxes = []          # a line that starts with a tone word begins a new box; other lines continue the last one
            while i < len(lines) and lines[i].strip().startswith('>'):
                m = _TONE.match(lines[i].strip())
                if m.group(1) or not boxes:
                    boxes.append([(m.group(1) or 'note').lower(), [m.group(2).strip()]])
                else:
                    boxes[-1][1].append(m.group(2).strip())
                i += 1
            for tone, parts in boxes:
                raw.append(('callout', {'tone': tone, 'text': ' '.join(p for p in parts if p)}))
        elif s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                if not _SEP.match(lines[i].strip()):
                    rows.append(_cells(lines[i]))
                i += 1
            if len(rows) < 2:
                raise RichTextError('A table needs a heading row and at least one data row.')
            raw.append(('table', {'header': rows[0], 'rows': rows[1:]}))
        elif _BULLET.match(line) or _NUMBER.match(line):
            ordered = bool(_NUMBER.match(line))
            pattern = _NUMBER if ordered else _BULLET
            items = []
            while i < len(lines) and pattern.match(lines[i]):
                items.append(pattern.match(lines[i]).group(1).strip()); i += 1
            raw.append(('list', {'items': items, 'ordered': ordered}))
        else:
            para = [s]
            i += 1          # always consume the first line, so the parser can never stall
            while i < len(lines) and lines[i].strip() and not _special(lines[i]):
                para.append(lines[i].strip()); i += 1
            raw.append(('paragraph', {'text': '\n'.join(para)}))
    if not raw:
        raise RichTextError('Write at least one paragraph.')
    blocks = []
    for n, (btype, payload) in enumerate(raw):
        try:
            validate_payload(btype, payload)
        except RichTextError as exc:
            raise RichTextError(f'Part {n + 1} ({btype}): {exc}')
        blocks.append({'key': keys[n] if n < len(keys) else str(uuid.uuid4()), 'type': btype,
                       'position': n, 'payload': payload})
    return blocks


def body_from_blocks(blocks):
    """Inverse of parse_body, so a saved lesson reopens as the same text."""
    out = []
    for b in sorted(blocks or [], key=lambda b: b['position']):
        p, t = b['payload'], b['type']
        if t == 'heading':
            out.append('#' * p['level'] + ' ' + p['text'])
        elif t == 'list':
            out.append('\n'.join((f'{n}. ' if p['ordered'] else '- ') + item for n, item in enumerate(p['items'], 1)))
        elif t == 'callout':
            out.append(f"> {p['tone']}: {p['text']}")
        elif t == 'table':
            def row(cells):
                return '| ' + ' | '.join(c.replace('|', '\\|') for c in cells) + ' |'
            out.append('\n'.join([row(p['header']), '|' + ' --- |' * len(p['header'])] + [row(r) for r in p['rows']]))
        else:
            out.append(p['text'])
    return '\n\n'.join(out)


# ------------------------------------------------------------------ rendering
def render_blocks(blocks):
    """Safe HTML for validated blocks. Headings rotate through five colours; a level 3 never skips a level."""
    html, colour, seen_h2 = [], -1, False
    for b in sorted(blocks, key=lambda b: b['position']):
        p, t = b['payload'], b['type']
        if t == 'heading':
            level = p['level']
            if level == 2 or not seen_h2:
                level, colour, seen_h2 = 2, (colour + 1) % HEADING_COLOURS, True
            html.append(f'<h{level} class="lh lh-{colour}">{render_inline(p["text"])}</h{level}>')
        elif t == 'list':
            tag = 'ol' if p['ordered'] else 'ul'
            items = ''.join(f'<li>{render_inline(i)}</li>' for i in p['items'])
            html.append(f'<{tag} class="ll ll-{max(colour, 0)}">{items}</{tag}>')
        elif t == 'callout':
            html.append(f'<aside class="callout callout-{p["tone"]}"><strong class="callout-label">'
                        f'{TONE_LABELS[p["tone"]]}</strong><p>{render_inline(p["text"])}</p></aside>')
        elif t == 'table':
            head = ''.join(f'<th scope="col">{render_inline(c)}</th>' for c in p['header'])
            body = ''.join('<tr>' + ''.join(f'<td>{render_inline(c)}</td>' for c in r) + '</tr>' for r in p['rows'])
            html.append('<div class="table-wrap" tabindex="0" role="region" aria-label="Table">'
                        f'<table class="lt"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        else:
            html.append(f'<p>{render_inline(p["text"])}</p>')
    return mark_safe('<div class="lesson-rich">' + ''.join(html) + '</div>')
