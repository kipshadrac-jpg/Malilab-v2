"""Markdown export of a note. Evidence keeps its title, units, assumptions, model version and capture time."""
from .blocks import plain


def _cell(value):
    return str(value if value is not None else '').replace('|', '\\|').replace('\n', ' ')


def _table(header, rows):
    lines = ['| ' + ' | '.join(_cell(h) for h in header) + ' |', '| ' + ' | '.join('---' for _ in header) + ' |']
    lines += ['| ' + ' | '.join(_cell(c) for c in row) + ' |' for row in rows]
    return '\n'.join(lines)


def _footer(block):
    calc = block.get('calc') or {}
    model = ('model %s %s' % (calc.get('model', ''), calc.get('version', ''))).strip()
    if block.get('mode') == 'live':
        stamp = '*Live block, last calculated %s; %s. It can change when refreshed.*' % (calc.get('calculated_at', 'unknown time'), model)
    else:
        stamp = '*Snapshot captured %s; %s. It does not change when other scenarios change.*' % (block.get('captured_at') or calc.get('calculated_at', 'unknown time'), model)
    return stamp


def block_to_markdown(b):
    t = b.get('type')
    if t == 'heading':
        return '#' * (int(b.get('level', 2)) + 1) + ' ' + plain(b.get('text', ''))
    if t == 'paragraph':
        return plain(b.get('text', ''))
    if t == 'quote':
        return '> ' + plain(b.get('text', '')).replace('\n', '\n> ')
    if t == 'divider':
        return '---'
    if t == 'callout':
        label = {'tip': 'Tip', 'warning': 'Watch out', 'key': 'Key idea', 'example': 'Example', 'note': 'Note'}.get(b.get('tone'), 'Note')
        return '> **%s:** %s' % (label, plain(b.get('text', '')).replace('\n', '\n> '))
    if t == 'list':
        items = b.get('items', [])
        return '\n'.join(('%d. ' % (i + 1) if b.get('ordered') else '- ') + plain(item) for i, item in enumerate(items))
    if t == 'metric':
        text = '**%s:** %s' % (b.get('label', ''), b.get('value', ''))
        if b.get('caption'):
            text += '  \n' + str(b['caption'])
        return text + '\n\n' + _footer(b)
    if t == 'chart':
        x = b.get('x', [])
        series = b.get('series', [])
        head = '### %s\n\n*Chart: %s against %s (%s).*\n\n' % (b.get('title', 'Chart'), b.get('y_label', 'value'), b.get('x_label', 'time'), b.get('unit', ''))
        rows = [[x[i]] + [s.get('values', [])[i] if i < len(s.get('values', [])) else '' for s in series] for i in range(len(x))]
        return head + _table([b.get('x_label', 'Year')] + [s.get('name', '') for s in series], rows) + '\n\n' + _footer(b)
    if t == 'table':
        cols = b.get('columns', [])
        return '### %s\n\n%s\n\n%s' % (b.get('title', 'Table'), _table([c.get('label', '') for c in cols], b.get('rows', [])), _footer(b))
    if t == 'scenarios':
        rows = []
        for s in b.get('scenarios', []):
            changed = '; '.join('%s: %s to %s' % (c.get('label'), c.get('from'), c.get('to')) for c in s.get('changes', [])) or 'Starting point'
            rows.append([s.get('name', ''), changed, 'KES ' + str(s.get('final_balance', '')), s.get('delta', '')])
        return '### %s\n\n%s\n\n%s' % (b.get('title', 'Scenario comparison'), _table(['Scenario', 'What changed', 'Final balance', 'Difference from base'], rows), _footer(b))
    if t == 'assumptions':
        lines = ['- **%s:** %s *(%s)*' % (i.get('label'), i.get('value'), i.get('kind', 'assumption')) for i in b.get('items', [])]
        return '### %s\n\n%s\n\n%s' % (b.get('title', 'Assumptions'), '\n'.join(lines), _footer(b))
    if t == 'methodology':
        return '### %s\n\n%s\n\n%s' % (b.get('title', 'How this was calculated'), '\n'.join('- ' + str(l) for l in b.get('lines', [])), _footer(b))
    if t == 'interpretation':
        text = '\n\n'.join(str(s) for s in b.get('sentences', []))
        note = '\n\n*Written from the calculation results. Edit it to say what you conclude.*' if b.get('generated') else ''
        return '### %s\n\n%s%s' % (b.get('title', 'What this shows'), text, note)
    if t == 'source':
        text = '> Source: ' + str(b.get('text', ''))
        return text + (' (%s)' % b['url'] if b.get('url') else '')
    return ''


def to_markdown(title, blocks, updated_at=''):
    parts = ['# ' + (title or 'Untitled note')]
    for b in blocks:
        chunk = block_to_markdown(b)
        if chunk:
            parts.append(chunk)
    parts.append('---\n*Exported from MaliLab%s. Figures are illustrations based on the stated assumptions, not forecasts or advice.*' % (' on ' + updated_at if updated_at else ''))
    return '\n\n'.join(parts) + '\n'
