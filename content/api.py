"""Read-only JSON for the MaliLab Android app: the same published playbooks the website shows, nothing more.

Only current, published revisions are ever returned (the same rules as the public pages). GET only; no sign-in
is needed because everything here is already public on the website.
"""
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import Playbook
from .public import public_playbooks, public_recommended_modules, resolve_public_revision


def _guide(revision):
    """Needs, steps and closing text exactly as stored (plain strings only)."""
    meta = revision.discovery_metadata if isinstance(revision.discovery_metadata, dict) else {}
    raw = meta.get('guide') if isinstance(meta.get('guide'), dict) else {}
    steps = []
    for s in raw.get('steps') or []:
        if isinstance(s, dict) and isinstance(s.get('title'), str) and s['title'].strip():
            steps.append({'n': len(steps) + 1, 'title': s['title'].strip(),
                          'text': s['text'] if isinstance(s.get('text'), str) else '',
                          'optional': bool(s.get('optional'))})
    needs = [n.strip() for n in (revision.assumptions or []) if isinstance(n, str) and n.strip()]
    outcome = raw.get('outcome') if isinstance(raw.get('outcome'), str) else ''
    return needs, steps, outcome


def _summary(request, identity, revision, step_count):
    asset = revision.cover_asset
    cover = request.build_absolute_uri(reverse('cover-image', args=[asset.asset_key])) if asset else None
    meta = getattr(asset, 'rights_metadata', None)
    return {'slug': identity.slug, 'title': revision.title, 'summary': revision.summary, 'goal': revision.scenario,
            'step_count': step_count, 'cover_url': cover,
            'cover_alt': meta.get('alt_text', '') if isinstance(meta, dict) else ''}


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


@require_GET
@cache_control(public=True, max_age=60)
def playbook_list(request):
    rows = []
    for identity in public_playbooks().select_related('current_published_revision__cover_asset'):
        revision = identity.current_published_revision
        rows.append(_summary(request, identity, revision, len(_guide(revision)[1])))
    return _json({'playbooks': rows})


@require_GET
@cache_control(public=True, max_age=60)
def playbook_detail(request, slug):
    try:
        identity, revision = resolve_public_revision(Playbook, slug)
    except Http404:
        return _json({'error': 'not_found'}, status=404)
    needs, steps, outcome = _guide(revision)
    data = _summary(request, identity, revision, len(steps))
    data.update(needs=needs, steps=steps, outcome=outcome, modules=[
        {'slug': row.module_revision.module.slug, 'title': row.module_revision.title, 'rationale': row.rationale}
        for row in public_recommended_modules(revision)])
    return _json(data)
