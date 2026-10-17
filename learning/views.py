from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from content.models import Lesson
from content.richtext import plain_text
from content.public import resolve_public_revision
from .models import LessonCompletion, ModuleCompletion, Note, RequirementEvidence, UserAchievement
from .services import create_note, owned_notes, require_verified_account


def _page(request, template, context, status=200):
    context.update({'user': request.user, 'csrf_token': get_token(request)})
    from django.http import HttpResponse
    return HttpResponse(render_to_string(template, context), status=status)


def _paragraphs(revision):
    """Readable picker for the exact revision's paragraph blocks (learners never see block keys)."""
    if revision is None or not isinstance(revision.blocks, list):
        return []
    blocks = [b for b in revision.blocks if isinstance(b, dict) and isinstance(b.get('payload'), dict) and b.get('key')]
    blocks.sort(key=lambda b: b.get('position', 0))
    return [{'key': b['key'], 'number': i + 1, 'snippet': plain_text(b)[:90]} for i, b in enumerate(blocks)]


@login_required(login_url='sign-in')
def notes(request, slug=None):
    try:
        require_verified_account(request.user)
    except PermissionDenied:
        return redirect('sign-in')
    revision = None
    if slug:
        _, revision = resolve_public_revision(Lesson, slug)
    error = ''
    if request.method == 'POST':
        if revision is None:
            return redirect('notes')
        kind = request.POST.get('kind', 'note')
        body = request.POST.get('body', '')
        block_key = request.POST.get('block_key', '')
        quote = request.POST.get('selected_quote', '')
        try:
            create_note(user=request.user, kind=kind, body=body, lesson_revision=revision,
                        block_key=block_key, anchor_data={'selected_quote': quote} if kind == 'highlight' else None)
            return redirect('notes')
        except ValidationError:
            error = 'We could not save this note. Check that a highlight matches a block in this lesson revision.'
    return _page(request, 'learning/notes.html', {'notes': owned_notes(request.user).select_related('lesson_revision__lesson'), 'revision': revision, 'paragraphs': _paragraphs(revision), 'error': error}, 400 if error else 200)


@login_required(login_url='sign-in')
def progress(request):
    try:
        require_verified_account(request.user)
    except PermissionDenied:
        return redirect('sign-in')
    return _page(request, 'learning/progress.html', {
        'accepted_evidence': RequirementEvidence.objects.filter(owner=request.user, state='accepted').select_related('module_revision','requirement','practice_revision','attempt').order_by('-evaluated_at'),
        'lesson_completions': LessonCompletion.objects.filter(owner=request.user).select_related('lesson_revision').order_by('-completed_at'),
        'module_completions': ModuleCompletion.objects.filter(owner=request.user).select_related('module_revision').order_by('-evaluated_at'),
        'achievements': UserAchievement.objects.filter(owner=request.user).select_related('definition_revision','module_completion','plan_revision').order_by('-awarded_at'),
    })


@login_required(login_url='sign-in')
def note_source(request, note_id):
    from django.shortcuts import get_object_or_404
    note = get_object_or_404(Note.objects.select_related('lesson_revision__lesson'), pk=note_id, owner=request.user, deleted_at__isnull=True)
    blocks = note.lesson_revision.blocks if isinstance(note.lesson_revision.blocks, list) else []
    block = next((item for item in blocks if isinstance(item, dict) and item.get('key') == note.block_key), None) if note.block_key else None
    return _page(request, 'learning/note_source.html', {'note':note,'revision':note.lesson_revision,'source_block':block,'source_text':plain_text(block) if block else ''})


@login_required(login_url='sign-in')
def record_module_completion(request, slug):
    from django.views.decorators.http import require_POST
    from content.models import Module
    from content.public import resolve_public_revision
    from .services import evaluate_module_completion
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    try:
        require_verified_account(request.user)
    except PermissionDenied:
        return redirect('sign-in')
    _, revision = resolve_public_revision(Module, slug)
    evaluate_module_completion(user=request.user, module_revision=revision)
    return redirect('module-detail', slug=slug)
