"""Plain read-only renderings of a revision for the Studio (staff only)."""
from content.richtext import render_blocks
from .editors import TYPE_LABELS


def _constraint_text(q):
    c = q.get('constraints') or {}
    if q['type'] in ('short_text', 'long_text'):
        return f"up to {c.get('max_length')} characters"
    if q['type'] == 'integer':
        parts = [f'{name} {c[key]}' for key, name in (('minimum', 'at least'), ('maximum', 'at most')) if key in c]
        return ', '.join(parts)
    if q['type'] == 'decimal_amount':
        parts = [f'{name} KES {c[key]}' for key, name in (('minimum', 'at least'), ('maximum', 'at most')) if key in c]
        return ', '.join(['KES'] + parts) if parts else 'KES'
    return ''


def preview_context(kind, revision):
    if kind == 'lesson':
        blocks = sorted(revision.blocks or [], key=lambda b: b['position'])
        return {'body_html': render_blocks(blocks), 'summary': revision.summary}
    if kind == 'practice':
        questions = []
        for q in (revision.response_schema or {}).get('questions', []):
            questions.append({'label': q['label'], 'type': TYPE_LABELS.get(q['type'], q['type']), 'required': q['required'],
                              'options': [o['label'] for o in q.get('options', [])], 'limits': _constraint_text(q)})
        return {'questions': questions, 'instructions': revision.instructions, 'prompt': revision.prompt,
                'safety_text': revision.safety_text}
    if kind == 'module':
        rows = []
        for r in revision.learning_requirements.filter(active=True).order_by('position', 'pk').select_related(
                'lesson_revision', 'practice_revision'):
            target = r.lesson_revision or r.practice_revision
            rows.append({'kind': 'Lesson' if r.target_kind == 'lesson' else 'Practice', 'title': target.title,
                         'classification': r.get_classification_display()})
        return {'description': revision.description, 'items': rows}
    rows = [{'title': r.module_revision.title, 'rationale': r.rationale}
            for r in revision.module_recommendations.filter(active=True).order_by('position', 'pk').select_related('module_revision')]
    return {'summary': revision.summary, 'scenario': revision.scenario, 'items': rows}
