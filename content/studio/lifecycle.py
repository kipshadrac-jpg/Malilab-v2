"""What each role has to do, plus the one new governance step: returning a revision to its author.

Returning is recorded as an append-only EditorialReview event ('changes_requested') and moves the
revision from in_review to 'returned'. Nothing is edited or deleted; the author starts a NEW draft
from it (authoring.start_revision_from), exactly like any other correction.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count

from content.models import EditorialReview, PublicationEvent
from content.services import ROLE_GROUPS, _target_fields, require_staff_mfa
from .kinds import KINDS, ORDER, identity_of, item, revision_field

RETURN_ROLES = ('reviewer', 'approver_publisher')


def reviews_of(kind, revision):
    return (EditorialReview.objects.filter(**{revision_field(kind): revision})
            .select_related('reviewer').order_by('created_at', 'pk'))


def passed_review_event(kind, revision):
    return (reviews_of(kind, revision).filter(action='reviewed', role_snapshot=ROLE_GROUPS['reviewer'])
            .order_by('-created_at', '-pk').first())


def has_reviewed(kind, revision):
    return passed_review_event(kind, revision) is not None


def is_latest(kind, revision):
    cfg = KINDS[kind]
    return not cfg['model'].objects.filter(
        **{cfg['identity']: identity_of(kind, revision)}, revision_number__gt=revision.revision_number).exists()


def has_unpublished(kind, revision):
    cfg = KINDS[kind]
    return cfg['model'].objects.filter(
        **{cfg['identity']: identity_of(kind, revision)}, status__in=('draft', 'in_review')).exists()


def last_return_comment(kind, revision):
    event = reviews_of(kind, revision).filter(action='changes_requested').order_by('-created_at', '-pk').first()
    return event


def _all(status, **filters):
    for kind in ORDER:
        cfg = KINDS[kind]
        for rev in (cfg['model'].objects.filter(status=status, **filters)
                    .select_related(cfg['identity'], 'author').order_by('-created_at', '-pk')):
            yield kind, rev


def author_work(user):
    drafts = [item(k, r) for k, r in _all('draft', author=user)]
    returned = [item(k, r) for k, r in _all('returned', author=user) if is_latest(k, r)]
    waiting = [item(k, r, 'waiting for a reviewer' if not has_reviewed(k, r) else 'waiting for the approver')
               for k, r in _all('in_review', author=user)]
    live = [item(k, r) for k, r in _all('published') if r.pk == identity_of(k, r).current_published_revision_id]
    return {'drafts': drafts, 'returned': returned, 'waiting': waiting, 'live': live}


def reviewer_queue(user):
    return [item(k, r) for k, r in _all('in_review') if r.author_id != user.pk and not has_reviewed(k, r)]


def approver_queue(user):
    ready = []
    for kind, rev in _all('in_review'):
        event = passed_review_event(kind, rev)
        if event and rev.author_id not in (None, user.pk) and event.reviewer_id != user.pk:
            ready.append(item(kind, rev, f'reviewed by {event.reviewer.email}'))
    return ready


def overview():
    counts = []
    for kind in ORDER:
        by_status = {row['status']: row['n'] for row in
                     KINDS[kind]['model'].objects.values('status').annotate(n=Count('id'))}
        counts.append({'label': KINDS[kind]['plural'], 'draft': by_status.get('draft', 0),
                       'in_review': by_status.get('in_review', 0), 'returned': by_status.get('returned', 0),
                       'published': by_status.get('published', 0)})
    return counts


def recent_publications(limit=10):
    events = []
    for event in PublicationEvent.objects.select_related('actor').order_by('-created_at', '-pk')[:limit]:
        revision = getattr(event, revision_field(event.content_kind))
        events.append({'when': event.created_at, 'who': event.actor.email if event.actor else 'unknown',
                       'what': f'{KINDS[event.content_kind]["label"]}: {revision.title}'})
    return events


def history(kind, revision):
    rows = []
    for event in reviews_of(kind, revision):
        label = {'reviewed': 'Review passed', 'approved': 'Approved', 'changes_requested': 'Returned to the author',
                 'ai_drafted': 'Drafted with the AI assistant'}.get(event.action, event.action)
        rows.append({'when': event.created_at, 'label': label, 'who': event.reviewer.email,
                     'role': event.role_snapshot, 'comment': event.comment})
    for event in PublicationEvent.objects.filter(**{revision_field(kind): revision}).select_related('actor').order_by('created_at', 'pk'):
        rows.append({'when': event.created_at, 'label': 'Published', 'who': event.actor.email if event.actor else '',
                     'role': event.role_snapshot, 'comment': ''})
    return sorted(rows, key=lambda row: row['when'])


@transaction.atomic
def return_to_author(*, revision, actor, comment, role):
    """A Reviewer (before review) or an Approver (after review) sends a revision back with a reason."""
    if role not in RETURN_ROLES:
        raise PermissionDenied('Only a Reviewer or an Approver can return a revision.')
    require_staff_mfa(actor, role)
    comment = (comment or '').strip()
    if not comment:
        raise ValidationError('Say what needs to change, so the author can act on it.')
    if revision.status != 'in_review':
        raise ValidationError('Only a revision that is in review can be returned.')
    if revision.author_id is None or revision.author_id == actor.pk:
        raise PermissionDenied('You cannot return your own work.')
    _, kind, field = _target_fields(revision)
    reviewed = has_reviewed(kind, revision)
    if role == 'reviewer' and reviewed:
        raise ValidationError('This revision has already passed review; the Approver decides next.')
    if role == 'approver_publisher':
        event = passed_review_event(kind, revision)
        if event is None:
            raise ValidationError('A Reviewer must review this revision first.')
        if event.reviewer_id == actor.pk:
            raise PermissionDenied('The Reviewer and the Approver must be different people.')
    EditorialReview.objects.create(content_kind=kind, **{field: revision}, reviewer=actor,
                                   role_snapshot=ROLE_GROUPS[role], action='changes_requested', comment=comment)
    revision.status = 'returned'
    revision._allow_lifecycle_transition = True
    revision.save(update_fields=['status'])
    revision._allow_lifecycle_transition = False
    return revision


def readiness_problems(kind, revision):
    """Plain-language gaps to fix before sending for review."""
    problems = []
    if not (revision.title or '').strip():
        problems.append('Add a title.')
    if kind == 'lesson' and not revision.blocks:
        problems.append('Write at least one paragraph.')
    if kind == 'practice' and not (revision.response_schema or {}).get('questions'):
        problems.append('Add at least one question.')
    if kind == 'module' and not revision.learning_requirements.filter(active=True).exists():
        problems.append('Choose at least one lesson or practice activity for this module.')
    if kind == 'playbook':
        if not (revision.summary or '').strip():
            problems.append('Add a short summary.')
        if not revision.module_recommendations.filter(active=True).exists():
            problems.append('Choose at least one module for this playbook.')
    return problems
