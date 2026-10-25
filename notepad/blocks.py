"""What a note may contain. Pure Python (no Django) so it is easy to test.

A note is an ordered list of typed blocks, never one blob of HTML. Text blocks hold the person's writing;
evidence blocks (metric, chart, table, scenarios, assumptions, methodology, interpretation, source) are
inserted from the calculator and carry everything needed to understand them later.
"""
import json
import re
import uuid

TEXT_TYPES = ('paragraph', 'heading', 'list', 'callout', 'quote', 'divider')
EVIDENCE_TYPES = ('metric', 'chart', 'table', 'scenarios', 'assumptions', 'methodology', 'interpretation', 'source')
BLOCK_TYPES = TEXT_TYPES + EVIDENCE_TYPES
TONES = ('tip', 'warning', 'key', 'example', 'note')
MAX_BLOCKS = 400
MAX_TEXT = 20000
MAX_BLOCK_BYTES = 300_000
MAX_NOTE_BYTES = 3_000_000
MAX_TAGS = 20


class NoteError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('; '.join(f"{e['field']}: {e['message']}" for e in errors))


_INLINE = re.compile(r'==(?:(?:yellow|green|blue|pink|orange):)?(.+?)==|\*\*(.+?)\*\*')


def plain(text):
    return _INLINE.sub(lambda m: m.group(1) or m.group(2), str(text))


def _text(value, field, errors, limit, allow_empty=True):
    if value is None:
        value = ''
    if not isinstance(value, str):
        errors.append({'field': field, 'message': 'Must be text.'})
        return ''
    if len(value) > limit:
        errors.append({'field': field, 'message': 'Too long (limit %d characters).' % limit})
        return ''
    if not allow_empty and not value.strip():
        errors.append({'field': field, 'message': 'Cannot be empty.'})
    return value


def clean_block(block, index, errors):
    field = f'blocks[{index}]'
    if not isinstance(block, dict):
        errors.append({'field': field, 'message': 'Each block must be an object.'})
        return None
    out = dict(block)
    btype = out.get('type')
    if btype not in BLOCK_TYPES:
        errors.append({'field': field + '.type', 'message': 'Unknown block type.'})
        return None
    bid = out.get('id')
    if not isinstance(bid, str) or not 1 <= len(bid) <= 64:
        out['id'] = str(uuid.uuid4())
    if btype in ('paragraph', 'quote'):
        out['text'] = _text(out.get('text'), field + '.text', errors, MAX_TEXT)
    elif btype == 'heading':
        out['text'] = _text(out.get('text'), field + '.text', errors, 300)
        level = out.get('level', 2)
        out['level'] = level if level in (1, 2, 3) and not isinstance(level, bool) else 2
    elif btype == 'callout':
        out['text'] = _text(out.get('text'), field + '.text', errors, MAX_TEXT)
        out['tone'] = out.get('tone') if out.get('tone') in TONES else 'note'
    elif btype == 'list':
        items = out.get('items')
        if not isinstance(items, list) or len(items) > 200:
            errors.append({'field': field + '.items', 'message': 'A list needs up to 200 items.'})
            items = []
        out['items'] = [_text(i, field + '.items', errors, 2000) for i in items]
        out['ordered'] = bool(out.get('ordered'))
    elif btype == 'divider':
        pass
    else:
        out['mode'] = out.get('mode') if out.get('mode') in ('live', 'snapshot') else 'snapshot'
    try:
        size = len(json.dumps(out, ensure_ascii=False))
    except (TypeError, ValueError):
        errors.append({'field': field, 'message': 'Block must be plain JSON.'})
        return None
    if size > MAX_BLOCK_BYTES:
        errors.append({'field': field, 'message': 'Block is too large.'})
        return None
    return out


def clean_blocks(blocks, errors):
    if not isinstance(blocks, list):
        errors.append({'field': 'blocks', 'message': 'Blocks must be a list.'})
        return []
    if len(blocks) > MAX_BLOCKS:
        errors.append({'field': 'blocks', 'message': 'A note can have at most %d blocks.' % MAX_BLOCKS})
        return []
    out = []
    for i, block in enumerate(blocks):
        cleaned = clean_block(block, i, errors)
        if cleaned is not None:
            out.append(cleaned)
    if not errors and len(json.dumps(out, ensure_ascii=False)) > MAX_NOTE_BYTES:
        errors.append({'field': 'blocks', 'message': 'This note is too large.'})
    return out


def clean_tags(tags, errors):
    if not isinstance(tags, list):
        errors.append({'field': 'tags', 'message': 'Tags must be a list.'})
        return []
    out = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        tag = tag.strip()[:30]
        if tag and tag.lower() not in [t.lower() for t in out]:
            out.append(tag)
    if len(out) > MAX_TAGS:
        errors.append({'field': 'tags', 'message': 'At most %d tags.' % MAX_TAGS})
    return out[:MAX_TAGS]


def clean_context(context, errors):
    if context in (None, {}):
        return {}
    if not isinstance(context, dict):
        errors.append({'field': 'context', 'message': 'Context must be an object.'})
        return {}
    kind = context.get('kind')
    slug = context.get('slug')
    if kind not in ('playbook', 'module', 'lesson') or not isinstance(slug, str) or not re.fullmatch(r'[-\w]{1,160}', slug):
        errors.append({'field': 'context', 'message': 'Context needs a kind (playbook, module or lesson) and a slug.'})
        return {}
    title = context.get('title')
    return {'kind': kind, 'slug': slug, 'title': title[:200] if isinstance(title, str) else ''}


def clean_note(data, partial):
    """Validate the editable fields of a note. With partial=True, absent fields are left out of the result."""
    if not isinstance(data, dict):
        raise NoteError([{'field': 'note', 'message': 'Send a JSON object.'}])
    errors, out = [], {}
    if 'title' in data or not partial:
        out['title'] = _text(data.get('title'), 'title', errors, 200).strip()
    if 'blocks' in data or not partial:
        out['blocks'] = clean_blocks(data.get('blocks', []), errors)
    if 'collection' in data or not partial:
        out['collection'] = _text(data.get('collection'), 'collection', errors, 60).strip()
    if 'tags' in data or not partial:
        out['tags'] = clean_tags(data.get('tags', []), errors)
    if 'favourite' in data:
        out['favourite'] = bool(data.get('favourite'))
    if 'context' in data:
        out['context'] = clean_context(data.get('context'), errors)
    if 'template' in data:
        out['template'] = _text(data.get('template'), 'template', errors, 40).strip()
    if errors:
        raise NoteError(errors)
    return out


def search_text(title, blocks):
    """Everything readable in a note, for search. Markup is removed."""
    parts = [title or '']
    for b in blocks:
        t = b.get('type')
        if t in ('paragraph', 'heading', 'callout', 'quote'):
            parts.append(plain(b.get('text', '')))
        elif t == 'list':
            parts.extend(plain(i) for i in b.get('items', []))
        elif t in EVIDENCE_TYPES:
            if b.get('title'):
                parts.append(str(b['title']))
            if t == 'metric':
                parts.append('%s %s' % (b.get('label', ''), b.get('value', '')))
            elif t == 'interpretation':
                parts.extend(str(s) for s in b.get('sentences', []))
            elif t == 'source':
                parts.append(str(b.get('text', '')))
    return '\n'.join(p for p in parts if p).strip()[:50000]
