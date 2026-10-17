from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import EditorialReview, PublicationEvent

ROLE_GROUPS={'author_editor':'Author/Editor','reviewer':'Reviewer','approver_publisher':'Approver/Publisher','administrator':'Administrator'}

def require_staff_mfa(actor, role):
    group=ROLE_GROUPS.get(role)
    verified=getattr(actor,'is_verified',None)
    if not getattr(actor,'is_authenticated',False) or not getattr(actor,'is_active',False) or not getattr(actor,'is_staff',False):
        raise PermissionDenied('An authenticated staff account is required.')
    if not callable(verified) or not verified():
        raise PermissionDenied('Staff MFA verification is required.')
    if not actor.groups.filter(name=group).exists():
        raise PermissionDenied('The required editorial role is missing.')

def _target_fields(revision):
    table={
      'PlaybookRevision':('playbook','playbook_revision'),
      'ModuleRevision':('module','module_revision'),
      'LessonRevision':('lesson','lesson_revision'),
      'PracticeActivityRevision':('activity','practice_revision'),
    }
    identity_field,revision_field=table[revision.__class__.__name__]
    kind=revision_field.removesuffix('_revision')
    return identity_field,kind,revision_field

@transaction.atomic
def submit_for_review(*, revision, actor):
    require_staff_mfa(actor,'author_editor')
    if revision.status!='draft' or revision.author_id != actor.pk:
        raise ValidationError('Only the revision author may submit a draft for review.')
    revision.full_clean()
    revision.status='in_review'
    revision._allow_lifecycle_transition=True
    revision.save(update_fields=['status'])
    revision._allow_lifecycle_transition=False
    return revision

@transaction.atomic
def review_revision(*, revision, actor, comment=''):
    require_staff_mfa(actor,'reviewer')
    if revision.status != 'in_review':
        raise ValidationError('Only a revision in review can be reviewed.')
    if revision.author_id is not None and revision.author_id == actor.pk:
        raise PermissionDenied('The reviewer must be different from the revision author.')
    identity_field,kind,revision_field=_target_fields(revision)
    return EditorialReview.objects.create(content_kind=kind,**{revision_field:revision},reviewer=actor,
        role_snapshot=ROLE_GROUPS['reviewer'],action='reviewed',comment=comment)

@transaction.atomic
def approve_and_publish(*, revision, actor, comment=''):
    require_staff_mfa(actor,'approver_publisher')
    if revision.status!='in_review':
        raise ValidationError('Only a submitted revision can be approved.')
    if revision.author_id is None or revision.author_id==actor.pk:
        raise PermissionDenied('The approver must be different from the revision author.')
    identity_field,kind,revision_field=_target_fields(revision)
    prior_review=EditorialReview.objects.filter(**{revision_field:revision}, action='reviewed', role_snapshot=ROLE_GROUPS['reviewer']).order_by('-created_at').first()
    if prior_review is None:
        raise ValidationError('A Reviewer must review this exact revision before publication.')
    if prior_review.reviewer_id == actor.pk:
        raise PermissionDenied('The Reviewer and Approver/Publisher must be different people.')
    from .models import validate_lesson_blocks
    if revision.__class__.__name__ == 'LessonRevision':
        validate_lesson_blocks(revision.blocks)
    identity=getattr(revision,identity_field)
    EditorialReview.objects.create(content_kind=kind,**{revision_field:revision},reviewer=actor,role_snapshot=ROLE_GROUPS['approver_publisher'],action='approved',comment=comment)
    PublicationEvent.objects.create(content_kind=kind,**{revision_field:revision},actor=actor,role_snapshot=ROLE_GROUPS['approver_publisher'],action='published')
    revision.status='published'
    revision._allow_lifecycle_transition=True
    revision.save(update_fields=['status'])
    revision._allow_lifecycle_transition=False
    setattr(identity,'current_published_revision',revision)
    identity.status='published'
    identity._allow_pointer_update=True
    identity.save(update_fields=['current_published_revision','status','updated_at'])
    identity._allow_pointer_update=False
    from discovery.services import rebuild_published_projection
    rebuild_published_projection(content_kind=kind, revision=revision)
    return revision
