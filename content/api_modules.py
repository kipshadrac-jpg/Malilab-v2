"""Read-only JSON for modules (the app's "books"): the same published modules and lessons the website shows."""
from django.http import Http404, JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from .models import Module
from .public import public_module_lessons, public_modules, resolve_public_revision
from .public_practice import public_module_practice


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def _module(identity, revision, lessons):
    return {'slug': identity.slug, 'title': revision.title, 'description': revision.description, 'lesson_count': len(lessons)}


@require_GET
@cache_control(public=True, max_age=60)
def module_list(request):
    rows = []
    for identity in public_modules():
        revision = identity.current_published_revision
        rows.append(_module(identity, revision, public_module_lessons(revision)))
    return _json({'modules': rows})


@require_GET
@cache_control(public=True, max_age=60)
def module_detail(request, slug):
    try:
        identity, revision = resolve_public_revision(Module, slug)
    except Http404:
        return _json({'error': 'not_found'}, status=404)
    lessons = public_module_lessons(revision)
    data = _module(identity, revision, lessons)
    data['lessons'] = [{'n': n, 'slug': lesson.lesson.slug, 'title': lesson.title, 'summary': lesson.summary}
                       for n, lesson in enumerate(lessons, 1)]
    data['practice'] = [{'n': n, 'slug': r.practice_revision.activity.slug, 'title': r.practice_revision.title,
                         'classification': r.classification}
                        for n, r in enumerate(public_module_practice(revision), 1)]
    return _json(data)
