from django.http import Http404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import F, Q
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token

from .models import Lesson, Module, Playbook, validate_lesson_blocks
from .richtext import render_blocks
from .public import (
    public_lesson_modules, public_module_lessons, public_modules, public_playbooks,
    public_recommended_modules, resolve_public_revision,
)


def _page(template, context):
    # Public pages do not need request/auth/message globals. Avoid loading the
    # existing broken messages context-processor path from Phase 6A settings.
    request = context.pop('_request', None)
    if request is not None:
        context.update({'user': request.user, 'csrf_token': get_token(request)})
    return HttpResponse(render_to_string(template, context))


def home(request):
    return _page('content/home.html', {'playbooks': public_playbooks()[:6], '_request': request})


def playbook_list(request):
    return _page('content/playbook_list.html', {'playbooks': public_playbooks(), '_request': request})


def playbook_detail(request, slug):
    identity, revision = resolve_public_revision(Playbook, slug)
    return _page('content/playbook_detail.html', {
        'identity': identity, 'revision': revision,
        'recommendations': public_recommended_modules(revision),
        '_request': request,
    })


def module_list(request):
    return _page('content/module_list.html', {'modules': public_modules(), '_request': request})


def module_detail(request, slug):
    identity, revision = resolve_public_revision(Module, slug)
    playbook = None
    playbook_slug = request.GET.get('playbook')
    if playbook_slug:
        playbook, playbook_revision = resolve_public_revision(Playbook, playbook_slug)
        if not playbook_revision.module_recommendations.filter(active=True, module_revision=revision).exists():
            raise Http404
    lessons = public_module_lessons(revision)
    requirements = list(revision.learning_requirements.filter(active=True).filter(
        Q(target_kind='lesson', lesson_revision__status='published', lesson_revision__lesson__status='published', lesson_revision__lesson__current_published_revision_id=F('lesson_revision_id'), lesson_revision__lesson_id=F('lesson_revision__lesson_id')) |
        Q(target_kind='practice', practice_revision__status='published', practice_revision__activity__status='published', practice_revision__activity__current_published_revision_id=F('practice_revision_id'), practice_revision__activity_id=F('practice_revision__activity_id'))
    ).select_related('lesson_revision','practice_revision').order_by('position','pk'))
    completion = None
    if request.user.is_authenticated and request.user.can_use_personal_features:
        from learning.models import ModuleCompletion
        completion = ModuleCompletion.objects.filter(owner=request.user,module_revision=revision).order_by('-evaluated_at').first()
    snapshot_rows = {row.get('requirement_id'): row for row in (completion.evidence_snapshot.get('requirements', []) if completion else []) if isinstance(row, dict)}
    requirement_rows = [{'requirement': req, 'satisfied': bool(snapshot_rows.get(req.pk, {}).get('satisfied', False))} for req in requirements]
    return _page('content/module_detail.html', {
        'identity': identity, 'revision': revision, 'lessons': lessons, 'playbook': playbook,
        'requirements': requirement_rows, 'completion': completion, '_request': request,
    })


def _lesson_completed(request, revision):
    """True when a signed-in learner has nothing left to record for this lesson revision."""
    if request.user.is_authenticated and request.user.can_use_personal_features:
        from learning.lesson_completion import has_outstanding
        return not has_outstanding(request.user, revision)
    return False


def lesson_detail(request, slug):
    identity, revision = resolve_public_revision(Lesson, slug)
    published_modules = list(public_lesson_modules(revision))

    module_slug = request.GET.get('module')
    context_module = None
    playbook = None
    playbook_slug = request.GET.get('playbook')
    if module_slug:
        context_module, module_revision = resolve_public_revision(Module, module_slug)
        if not module_revision.learning_requirements.filter(
            target_kind='lesson', active=True, lesson_revision=revision,
        ).exists():
            raise Http404
    elif len(published_modules) == 1:
        context_module = published_modules[0]
    elif len(published_modules) > 1:
        # The route has no module segment; omit navigation rather than guessing context.
        context_module = None

    if playbook_slug:
        if context_module is None:
            raise Http404
        playbook, playbook_revision = resolve_public_revision(Playbook, playbook_slug)
        if not playbook_revision.module_recommendations.filter(
            active=True, module_revision=context_module.current_published_revision,
        ).exists():
            raise Http404
    else:
        playbook = None

    previous_lesson = next_lesson = None
    if context_module:
        ordered = public_module_lessons(context_module.current_published_revision)
        index = next((i for i, item in enumerate(ordered) if item.pk == revision.pk), None)
        if index is not None:
            previous_lesson = ordered[index - 1] if index > 0 else None
            next_lesson = ordered[index + 1] if index + 1 < len(ordered) else None

    try:
        # Reuse the approved Phase 6A schema validator for rows changed outside
        # model.save(), and do not reinterpret malformed stored JSON as content.
        validate_lesson_blocks(revision.blocks)
    except ValidationError:
        unsupported_blocks = True
        rendered_blocks = []
    else:
        unsupported_blocks = False
        rendered_blocks = sorted(revision.blocks, key=lambda block: block['position'])

    return _page('content/lesson_detail.html', {
        'identity': identity, 'revision': revision, 'blocks': rendered_blocks,
        'unsupported_blocks': unsupported_blocks,
        'body_html': render_blocks(rendered_blocks) if rendered_blocks else '',
        'lesson_completed': _lesson_completed(request, revision),
        'module': context_module, 'previous_lesson': previous_lesson,
        'next_lesson': next_lesson, 'playbook': playbook,
        '_request': request,
    })
