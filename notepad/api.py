"""The Plan Notepad API for the app. Every call needs the learner's sign-in token; notes are private to their owner."""
import re
import uuid
from datetime import timedelta
from functools import wraps

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.api import _body, _error, _json, token_user
from . import engine
from .blocks import NoteError, clean_note, search_text
from .export import to_markdown
from .models import PlanNote, PlanNoteVersion

VERSION_GAP = timedelta(minutes=10)
KEEP_VERSIONS = 60
LIST_LIMIT = 300
NOTES_PER_LEARNER = 2000


def learner(view):
    """Require a signed-in learner (Bearer token), switch off CSRF (no cookies are used) and caching."""
    @csrf_exempt
    @never_cache
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = token_user(request)
        if user is None:
            return _error('unauthorized', 'Please sign in.', 401)
        request.learner = user
        return view(request, *args, **kwargs)
    return wrapper


def _stamp(value):
    return value.isoformat() if value else None


def _summary(note):
    text = note.search_text or ''
    body = text[len(note.title):].strip() if note.title and text.startswith(note.title) else text
    return {
        'uid': str(note.uid), 'title': note.title, 'snippet': re.sub(r'\s+', ' ', body)[:140],
        'collection': note.collection, 'tags': note.tags, 'favourite': note.favourite, 'context': note.context,
        'template': note.template, 'version': note.version, 'block_count': len(note.blocks),
        'updated_at': _stamp(note.updated_at),
    }


def _full(note):
    data = _summary(note)
    data['blocks'] = note.blocks
    data['created_at'] = _stamp(note.created_at)
    return data


def _mine(request):
    return PlanNote.objects.filter(owner=request.learner, deleted_at__isnull=True)


def _note_or_404(request, uid, lock=False):
    qs = _mine(request)
    if lock:
        qs = qs.select_for_update()
    return qs.filter(uid=uid).first()


def _not_found():
    return _error('not_found', 'That note was not found.', 404)


def _invalid(exc):
    return _json({'error': 'invalid_note', 'message': 'This note could not be saved.', 'fields': exc.errors}, status=400)


def _snapshot(note, label=''):
    """Keep the note's current content as a restorable version; at most one every 10 minutes unless labelled."""
    last = note.versions.order_by('-number').first()
    if label or last is None or timezone.now() - last.created_at >= VERSION_GAP:
        PlanNoteVersion.objects.create(note=note, number=(last.number + 1) if last else 1, title=note.title, blocks=note.blocks, label=label)
        old = list(note.versions.order_by('-number').values_list('pk', flat=True)[KEEP_VERSIONS:])
        if old:
            PlanNoteVersion.objects.filter(pk__in=old).delete()


# ---------------------------------------------------------------- list and create
@learner
@require_http_methods(['GET', 'POST'])
def notes(request):
    if request.method == 'POST':
        return _create(request)
    qs = _mine(request)
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(search_text__icontains=q[:100])
    if request.GET.get('collection'):
        qs = qs.filter(collection=request.GET['collection'][:60])
    if request.GET.get('tag'):
        qs = qs.filter(tags__contains=[request.GET['tag'][:30]])
    if request.GET.get('favourite') == '1':
        qs = qs.filter(favourite=True)
    ctx = request.GET.get('context', '')
    if ':' in ctx:
        kind, slug = ctx.split(':', 1)
        qs = qs.filter(context__kind=kind, context__slug=slug)
    rows = qs.order_by('-updated_at')[:LIST_LIMIT]
    return _json({'notes': [_summary(n) for n in rows]})


def _parse_uid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return None


def _create(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    uid = _parse_uid(data.get('uid')) if data.get('uid') else uuid.uuid4()
    if uid is None:
        return _error('bad_request', 'The note id is not valid.')
    existing = PlanNote.objects.filter(uid=uid).first()
    if existing is not None:
        # Creating twice (a retry after a poor connection) is harmless; another person's note is not revealed.
        if existing.owner_id == request.learner.pk and existing.deleted_at is None:
            return _json(_full(existing))
        return _error('conflict', 'That note id is already taken.', 409)
    try:
        clean = clean_note(data, partial=False)
    except NoteError as exc:
        return _invalid(exc)
    if _mine(request).count() >= NOTES_PER_LEARNER:
        return _error('limit', 'You have reached the limit of %d notes.' % NOTES_PER_LEARNER, 400)
    try:
        with transaction.atomic():
            note = PlanNote.objects.create(
                uid=uid, owner=request.learner, search_text=search_text(clean['title'], clean['blocks']),
                **{k: v for k, v in clean.items() if k in ('title', 'blocks', 'collection', 'tags', 'favourite', 'context', 'template')})
            _snapshot(note)
    except IntegrityError:
        return _error('conflict', 'That note id is already taken.', 409)
    return _json(_full(note), status=201)


# ---------------------------------------------------------------- one note
@learner
@require_http_methods(['GET', 'PUT', 'DELETE'])
def note_detail(request, uid):
    if request.method == 'GET':
        note = _note_or_404(request, uid)
        return _json(_full(note)) if note else _not_found()
    if request.method == 'DELETE':
        note = _note_or_404(request, uid)
        if note is None:
            return _not_found()
        note.deleted_at = timezone.now()
        note.save(update_fields=['deleted_at'])
        return _json({'ok': True})
    return _update(request, uid)


def _update(request, uid):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    base = data.get('base_version')
    if isinstance(base, bool) or not isinstance(base, int):
        return _error('bad_request', 'base_version is required so edits from two phones are never mixed up silently.')
    try:
        clean = clean_note(data, partial=True)
    except NoteError as exc:
        return _invalid(exc)
    with transaction.atomic():
        note = _note_or_404(request, uid, lock=True)
        if note is None:
            return _not_found()
        if note.version != base:
            return _json({'error': 'conflict', 'message': 'This note changed on another device.', 'note': _full(note)}, status=409)
        for key, value in clean.items():
            setattr(note, key, value)
        note.search_text = search_text(note.title, note.blocks)
        note.version += 1
        note.save()
        _snapshot(note)
    return _json({'uid': str(note.uid), 'version': note.version, 'updated_at': _stamp(note.updated_at)})


# ---------------------------------------------------------------- duplicate, history, restore, export
@learner
@require_http_methods(['POST'])
def duplicate(request, uid):
    note = _note_or_404(request, uid)
    if note is None:
        return _not_found()
    if _mine(request).count() >= NOTES_PER_LEARNER:
        return _error('limit', 'You have reached the limit of %d notes.' % NOTES_PER_LEARNER, 400)
    title = ('Copy of ' + note.title)[:200] if note.title else 'Copy of untitled note'
    with transaction.atomic():
        copy = PlanNote.objects.create(
            uid=uuid.uuid4(), owner=request.learner, title=title, blocks=note.blocks, collection=note.collection,
            tags=note.tags, favourite=False, context=note.context, template=note.template, search_text=note.search_text)
        _snapshot(copy)
    return _json(_full(copy), status=201)


@learner
@require_http_methods(['GET'])
def versions(request, uid):
    note = _note_or_404(request, uid)
    if note is None:
        return _not_found()
    rows = note.versions.order_by('-number')[:KEEP_VERSIONS]
    return _json({'versions': [{'number': v.number, 'title': v.title, 'label': v.label, 'block_count': len(v.blocks),
                                'created_at': _stamp(v.created_at)} for v in rows]})


@learner
@require_http_methods(['POST'])
def restore(request, uid, number):
    with transaction.atomic():
        note = _note_or_404(request, uid, lock=True)
        if note is None:
            return _not_found()
        target = note.versions.filter(number=number).first()
        if target is None:
            return _not_found()
        _snapshot(note, label='Before restore')
        note.title = target.title
        note.blocks = target.blocks
        note.search_text = search_text(note.title, note.blocks)
        note.version += 1
        note.save()
        _snapshot(note, label='Restored from #%d' % target.number)
    return _json(_full(note))


@learner
@require_http_methods(['GET'])
def export(request, uid):
    note = _note_or_404(request, uid)
    if note is None:
        return _not_found()
    body = to_markdown(note.title, note.blocks, note.updated_at.date().isoformat() if note.updated_at else '')
    name = re.sub(r'[^A-Za-z0-9]+', '-', note.title).strip('-')[:50] or 'note'
    response = HttpResponse(body, content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="%s.md"' % name
    return response


# ---------------------------------------------------------------- the note that belongs to a lesson, module or playbook
@learner
@require_http_methods(['POST'])
def for_context(request):
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    from .blocks import clean_context
    errors = []
    context = clean_context({'kind': data.get('kind'), 'slug': data.get('slug'), 'title': data.get('title')}, errors)
    if errors or not context:
        return _error('bad_request', 'Say which playbook, module or lesson this note belongs to.')
    found = _mine(request).filter(context__kind=context['kind'], context__slug=context['slug']).order_by('-updated_at').first()
    if found is not None:
        return _json(_full(found))
    title = ('Notes: ' + context['title'])[:200] if context['title'] else 'My notes'
    with transaction.atomic():
        note = PlanNote.objects.create(
            uid=uuid.uuid4(), owner=request.learner, title=title, context=context, collection='Learning notes',
            blocks=[{'id': str(uuid.uuid4()), 'type': 'paragraph', 'text': ''}], search_text=title)
        _snapshot(note)
    return _json(_full(note), status=201)


# ---------------------------------------------------------------- calculator
CALC_PER_MINUTE = 60


def _calc_guard(request):
    key = 'calc-rl:%s:%s' % (request.learner.pk, int(timezone.now().timestamp() // 60))
    if cache.add(key, 1, 90):
        return None
    try:
        count = cache.incr(key)
    except ValueError:
        count = 1
    if count > CALC_PER_MINUTE:
        return _error('too_many', 'Slow down a little and try again in a minute.', 429)
    return None


def _calc_invalid(exc):
    return _json({'error': 'invalid_inputs', 'message': 'Check the highlighted values.', 'fields': exc.errors}, status=400)


def _stamped(result):
    result['calculated_at'] = timezone.now().replace(microsecond=0).isoformat()
    return result


@learner
@require_http_methods(['POST'])
def calc_compound(request):
    """Project a savings/withdrawal model, or solve backwards for an unknown ({'solve': {'kind': ...}})."""
    blocked = _calc_guard(request)
    if blocked:
        return blocked
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    try:
        inputs = engine.normalize(data.get('inputs'))
        detail = bool(data.get('detail'))
        solve = data.get('solve')
        if solve:
            kind = solve.get('kind') if isinstance(solve, dict) else None
            out = engine.solve(inputs, kind, detail)
            out['result'] = _stamped(out['result'])
            return _json(out)
        return _json({'result': _stamped(engine.project(inputs, detail))})
    except engine.EngineError as exc:
        return _calc_invalid(exc)


@learner
@require_http_methods(['POST'])
def calc_compare(request):
    """The base case plus up to five named scenarios, with what changed and how the results differ."""
    blocked = _calc_guard(request)
    if blocked:
        return blocked
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    try:
        out = engine.compare(data.get('inputs') or {}, data.get('scenarios'), bool(data.get('detail')))
    except engine.EngineError as exc:
        return _calc_invalid(exc)
    stamp = timezone.now().replace(microsecond=0).isoformat()
    for row in out['scenarios']:
        row['result']['calculated_at'] = stamp
    return _json(out)


# ---- Patch 20: Kenyan instruments ------------------------------------------------------------------
from . import instruments as _instruments
from . import rules as _kenya_rules


@learner
@require_http_methods(['POST'])
def calc_instrument(request):
    """Run one Kenyan instrument model: {'model': 'tbill'|'tbond'|'mmf'|'sacco'|'loan', 'inputs': {...}}."""
    blocked = _calc_guard(request)
    if blocked:
        return blocked
    data = _body(request)
    if data is None:
        return _error('bad_request', 'Send JSON.')
    try:
        return _json({'result': _stamped(_instruments.run(data.get('model'), data.get('inputs') or {}))})
    except engine.EngineError as exc:
        return _calc_invalid(exc)


@learner
@require_http_methods(['GET'])
def calc_rules(request):
    """The sourced rules in force today, with where each came from."""
    return _json({'rules': _kenya_rules.all_rules(), 'models': list(_instruments.MODELS)})
