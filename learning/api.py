"""JSON for reading lessons and marking them complete in the app. Uses the website's own completion records."""
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.api import token_user
from billing.catalog import paywall_on
from billing.service import lesson_gate, prices_note
from content.models import Lesson
from content.public import public_module_lessons, public_modules, resolve_public_revision
from content.public_practice import public_module_practice
from .lesson_completion import mark_lesson_complete
from .models import LessonCompletion, RequirementEvidence


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


def _unauthorized():
    return _json({'error': 'unauthorized', 'message': 'Please sign in.'}, status=401)


def payment_required(modules):
    """The lesson belongs to modules this learner has not unlocked."""
    return _json({'error': 'payment_required', 'message': 'Unlock this module to read its lessons.', 'modules': modules,
                  'prices': prices_note()}, status=402)


@require_GET
def lesson_detail(request, slug):
    identity, revision = resolve_public_revision(Lesson, slug)
    if paywall_on():
        user = token_user(request)
        if user is None:
            return _unauthorized()
        gate = lesson_gate(user, revision)
        if gate:
            return payment_required(gate)
    blocks = revision.blocks if isinstance(revision.blocks, list) else []
    blocks = sorted((b for b in blocks if isinstance(b, dict) and isinstance(b.get('payload'), dict)),
                    key=lambda b: b.get('position', 0))
    response = _json({'slug': identity.slug, 'title': revision.title, 'summary': revision.summary,
                      'blocks': [{'key': b.get('key', ''), 'type': b.get('type', ''), 'payload': b['payload']} for b in blocks]})
    response['Cache-Control'] = 'private, no-store' if paywall_on() else 'public, max-age=60'
    return response


def progress_for(user):
    """What this learner has finished: lesson slugs, practice slugs, and per module the lessons and practice done."""
    from practice.models import PracticeAttempt
    finished = set(LessonCompletion.objects.filter(owner=user).values_list('lesson_revision_id', flat=True))
    met = set(RequirementEvidence.objects.filter(owner=user, state='accepted', attempt__state='submitted').values_list('requirement_id', flat=True))
    practice_slugs = set(PracticeAttempt.objects.filter(owner=user, state='submitted').values_list('practice_revision__activity__slug', flat=True))
    lesson_slugs, modules = set(), []
    for identity in public_modules():
        revision = identity.current_published_revision
        lessons = public_module_lessons(revision)
        done = [lesson for lesson in lessons if lesson.pk in finished]
        lesson_slugs.update(lesson.lesson.slug for lesson in done)
        practice = public_module_practice(revision)
        practice_done = [r for r in practice if r.pk in met]
        required_open = [r for r in practice if r.classification == 'required' and r.pk not in met]
        modules.append({'slug': identity.slug, 'done': len(done), 'total': len(lessons),
                        'practice_done': len(practice_done), 'practice_total': len(practice),
                        'complete': bool(lessons or practice) and len(done) == len(lessons) and not required_open})
    return {'lessons': sorted(lesson_slugs), 'practice': sorted(practice_slugs), 'modules': modules}


@require_GET
@never_cache
def progress(request):
    user = token_user(request)
    if user is None:
        return _unauthorized()
    return _json(progress_for(user))


@csrf_exempt
@require_POST
@never_cache
def complete_lesson(request, slug):
    user = token_user(request)
    if user is None:
        return _unauthorized()
    _, revision = resolve_public_revision(Lesson, slug)    # 404 unless published
    gate = lesson_gate(user, revision)
    if gate:
        return payment_required(gate)
    try:
        mark_lesson_complete(user=user, lesson_revision=revision)
    except PermissionDenied:
        return _unauthorized()
    return _json({'completed': slug, **progress_for(user)})
