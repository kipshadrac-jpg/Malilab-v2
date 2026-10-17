from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse

from content import authoring, services
from content.models import LessonRevision, ModuleRevision, PracticeActivityRevision
from content.services import ROLE_GROUPS
from . import lifecycle
from .access import ROLE_LABELS, ROLE_ORDER, page, studio_view
from .editors import EDITORS
from .kinds import KINDS, ORDER, identity_of, public_path
from .preview import preview_context

User = get_user_model()


def _kind(kind):
    if kind not in KINDS:
        raise Http404
    return KINDS[kind]


def _revision(kind, rev_id):
    try:
        return _kind(kind)['model'].objects.select_related(KINDS[kind]['identity'], 'author').get(pk=rev_id)
    except _kind(kind)['model'].DoesNotExist:
        raise Http404


def _can_view(request, kind, rev):
    roles, me = request.studio_roles, request.user
    if 'administrator' in roles:
        return True
    if rev.author_id == me.pk and 'author_editor' in roles:
        return True
    if 'author_editor' in roles and rev.status == 'published':
        return True
    if roles & {'reviewer', 'approver_publisher'} and rev.status in ('in_review', 'published', 'returned'):
        return True
    return False


def _prerequisite(kind):
    """Why a new item of this kind cannot be started yet, or ''."""
    if kind == 'module':
        has_lesson = LessonRevision.objects.filter(status='published', lesson__current_published_revision_id=F('pk')).exists()
        has_practice = PracticeActivityRevision.objects.filter(status='published', activity__current_published_revision_id=F('pk')).exists()
        if not (has_lesson or has_practice):
            return 'A module is built from published lessons and practice activities. Publish at least one first.'
    if kind == 'playbook':
        if not ModuleRevision.objects.filter(status='published', module__current_published_revision_id=F('pk')).exists():
            return 'A playbook recommends published modules. Publish at least one module first.'
    return ''


# ---------------------------------------------------------------- Home
@studio_view()
def home(request):
    roles, me = request.studio_roles, request.user
    sections = []
    create_options = []
    if 'author_editor' in roles:
        work = lifecycle.author_work(me)
        for kind in ORDER:
            problem = _prerequisite(kind)
            create_options.append({'label': f'New {KINDS[kind]["label"].lower()}', 'url': reverse('studio-new', args=[kind]),
                                   'enabled': not problem, 'hint': problem})
        sections += [
            {'title': 'Returned to you', 'role': 'Author', 'items': work['returned'],
             'intro': 'A reviewer or approver asked for changes. Open one to read why, then start a new draft from it.',
             'empty': 'Nothing has been returned.', 'hide_if_empty': True},
            {'title': 'Your drafts', 'role': 'Author', 'items': work['drafts'],
             'intro': 'Finish these, then send them for review.', 'empty': 'You have no drafts. Start something new above.'},
            {'title': 'Waiting on others', 'role': 'Author', 'items': work['waiting'],
             'intro': 'Sent for review. Nothing to do until someone decides.', 'empty': '', 'hide_if_empty': True},
            {'title': 'Published: correct or update', 'role': 'Author', 'items': work['live'],
             'intro': 'Open one to start a corrected draft. The published version stays live until the new one is approved.',
             'empty': 'Nothing is published yet.'},
        ]
    if 'reviewer' in roles:
        sections.append({'title': 'Waiting for your review', 'role': 'Reviewer', 'items': lifecycle.reviewer_queue(me),
                         'intro': 'Read each item carefully. Pass it to the Approver, or return it with a reason.',
                         'empty': 'Nothing is waiting for you.'})
    if 'approver_publisher' in roles:
        sections.append({'title': 'Ready to publish', 'role': 'Approver', 'items': lifecycle.approver_queue(me),
                         'intro': 'These passed review. Publishing makes them live for learners.',
                         'empty': 'Nothing is ready to publish.'})
    context = {'sections': sections, 'create_options': create_options, 'ai_link': 'author_editor' in roles}
    if 'administrator' in roles:
        staff = []
        for user in User.objects.filter(is_staff=True, is_active=True).order_by('email'):
            names = set(user.groups.values_list('name', flat=True))
            staff.append({'email': user.email, 'roles': ', '.join(ROLE_LABELS[r] for r in ROLE_ORDER if ROLE_GROUPS[r] in names) or 'none'})
        context.update({'admin_overview': lifecycle.overview(), 'recent': lifecycle.recent_publications(), 'staff': staff})
    return page(request, 'studio/home.html', context)


# ---------------------------------------------------------------- Create / edit
def _editor_page(request, editor, kind, *, creating, revision=None, status=200):
    ctx = {'kind': kind, 'kind_label': KINDS[kind]['label'], 'creating': creating, 'revision': revision,
           'editor_errors': editor.errors}
    ctx.update(editor.context())
    return page(request, editor.template, ctx, status=status)


def _run_editor(request, kind, revision):
    creating = revision is None
    editor = EDITORS[kind](revision, request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        if 'add_rows' in request.POST and hasattr(editor, 'add_rows'):
            editor.add_rows()
            return _editor_page(request, editor, kind, creating=creating, revision=revision)
        if editor.valid():
            try:
                saved = editor.save(request.user)
            except ValidationError as exc:
                editor.errors.extend(exc.messages)
            else:
                messages.success(request, 'Saved. Check the preview below, then send it for review when it is ready.')
                return redirect('studio-revision', kind=kind, rev_id=saved.pk)
        return _editor_page(request, editor, kind, creating=creating, revision=revision)
    return _editor_page(request, editor, kind, creating=creating, revision=revision)


@studio_view('author_editor')
def create(request, kind):
    _kind(kind)
    problem = _prerequisite(kind)
    if problem:
        return page(request, 'studio/blocked.html', {'kind_label': KINDS[kind]['label'], 'problem': problem})
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    return _run_editor(request, kind, None)


@studio_view('author_editor')
def edit(request, kind, rev_id):
    revision = _revision(kind, rev_id)
    if revision.status != 'draft' or revision.author_id != request.user.pk:
        raise Http404
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])
    return _run_editor(request, kind, revision)


# ---------------------------------------------------------------- One revision
def _actions(request, kind, rev):
    roles, me = request.studio_roles, request.user
    actions = []
    if rev.status == 'draft' and rev.author_id == me.pk and 'author_editor' in roles:
        actions.append({'name': 'submit', 'label': 'Send for review', 'comment': '', 'style': 'primary',
                        'help': 'After this you cannot edit it. A reviewer will read it.'})
    if rev.status == 'in_review':
        reviewed = lifecycle.has_reviewed(kind, rev)
        if 'reviewer' in roles and not reviewed and rev.author_id != me.pk:
            actions.append({'name': 'review', 'label': 'Pass review', 'comment': 'optional', 'style': 'primary',
                            'help': 'It then goes to the Approver.'})
            actions.append({'name': 'return', 'label': 'Return to author', 'comment': 'required', 'style': 'secondary',
                            'help': 'Say what needs to change.'})
        event = lifecycle.passed_review_event(kind, rev)
        if ('approver_publisher' in roles and event is not None and rev.author_id != me.pk
                and event.reviewer_id != me.pk):
            actions.append({'name': 'publish', 'label': 'Approve and publish', 'comment': 'optional', 'style': 'primary',
                            'help': 'It becomes visible to learners straight away.'})
            actions.append({'name': 'return', 'label': 'Return to author', 'comment': 'required', 'style': 'secondary',
                            'help': 'Say what needs to change.'})
    if 'author_editor' in roles and lifecycle.is_latest(kind, rev) and not lifecycle.has_unpublished(kind, rev):
        current = identity_of(kind, rev).current_published_revision_id
        if rev.status == 'returned' or (rev.status == 'published' and rev.pk == current):
            actions.append({'name': 'new-draft', 'label': 'Start a new draft from this', 'comment': '', 'style': 'primary',
                            'help': 'Copies it into a new draft you can edit. The original stays untouched.'})
    return actions


@studio_view()
def revision(request, kind, rev_id):
    rev = _revision(kind, rev_id)
    if not _can_view(request, kind, rev):
        raise Http404
    identity = identity_of(kind, rev)
    problems = lifecycle.readiness_problems(kind, rev) if (rev.status == 'draft' and rev.author_id == request.user.pk) else []
    returned = lifecycle.last_return_comment(kind, rev) if rev.status == 'returned' else None
    return page(request, 'studio/revision.html', {
        'kind': kind, 'kind_label': KINDS[kind]['label'], 'rev': rev, 'identity': identity,
        'can_edit': rev.status == 'draft' and rev.author_id == request.user.pk and 'author_editor' in request.studio_roles,
        'actions': _actions(request, kind, rev), 'problems': problems, 'returned': returned,
        'history': lifecycle.history(kind, rev), 'preview': preview_context(kind, rev),
        'live_path': public_path(kind, rev) if rev.status == 'published' and rev.pk == identity.current_published_revision_id else '',
    })


def _do_submit(request, kind, rev, comment):
    problems = lifecycle.readiness_problems(kind, rev)
    if problems:
        raise ValidationError(problems)
    services.submit_for_review(revision=rev, actor=request.user)
    return 'Sent for review.'


def _do_review(request, kind, rev, comment):
    services.review_revision(revision=rev, actor=request.user, comment=comment)
    return 'Review recorded. It is now with the Approver.'


def _do_publish(request, kind, rev, comment):
    services.approve_and_publish(revision=rev, actor=request.user, comment=comment)
    return f'Published. It is live at {public_path(kind, rev)}'


def _do_return(request, kind, rev, comment):
    role = 'reviewer' if 'reviewer' in request.studio_roles and not lifecycle.has_reviewed(kind, rev) else 'approver_publisher'
    lifecycle.return_to_author(revision=rev, actor=request.user, comment=comment, role=role)
    return 'Returned to the author with your note.'


ACTIONS = {'submit': _do_submit, 'review': _do_review, 'publish': _do_publish, 'return': _do_return}


@studio_view()
def act(request, kind, rev_id, name):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    rev = _revision(kind, rev_id)
    if not _can_view(request, kind, rev):
        raise Http404
    comment = request.POST.get('comment', '')
    target = reverse('studio-revision', args=[kind, rev.pk])
    if name == 'new-draft':
        try:
            new = authoring.start_revision_from(revision=rev, actor=request.user)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, _message(exc))
            return redirect(target)
        messages.success(request, 'A new draft was started. Make your changes, then send it for review.')
        return redirect('studio-revision', kind=kind, rev_id=new.pk)
    handler = ACTIONS.get(name)
    if handler is None:
        raise Http404
    try:
        messages.success(request, handler(request, kind, rev, comment))
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, _message(exc))
    return redirect(target)


def _message(exc):
    if isinstance(exc, ValidationError):
        return ' '.join(exc.messages)
    return str(exc) or 'That action is not allowed for you.'
