from django.core.exceptions import ValidationError
from django.contrib.postgres.search import SearchVector
from django.db import transaction, connection
from .models import SearchProjection

TARGET_FIELDS={'playbook':'playbook_revision','module':'module_revision','lesson':'lesson_revision','practice':'practice_revision'}

@transaction.atomic
def rebuild_revision_projection(*, content_kind, revision, title=None, searchable_text=None, filter_metadata=None):
    field=TARGET_FIELDS.get(content_kind)
    if field is None:
        raise ValidationError('Unsupported public content kind.')
    expected_model = {'playbook':'PlaybookRevision','module':'ModuleRevision','lesson':'LessonRevision','practice':'PracticeActivityRevision'}[content_kind]
    if revision.__class__.__name__ != expected_model:
        raise ValidationError('Revision type does not match content kind.')
    if revision.status != 'published':
        SearchProjection.objects.filter(**{field:revision}).delete()
        return None
    identity=getattr(revision, {'playbook':'playbook','module':'module','lesson':'lesson','practice':'activity'}[content_kind])
    if identity.current_published_revision_id != revision.pk:
        SearchProjection.objects.filter(**{field:revision}).delete()
        return None
    # A single identity may expose only its current published revision.
    identity_field = {'playbook':'playbook_revision__playbook','module':'module_revision__module',
        'lesson':'lesson_revision__lesson','practice':'practice_revision__activity'}[content_kind]
    SearchProjection.objects.filter(**{identity_field: identity}).exclude(**{field: revision}).delete()
    title = title if title is not None else revision.title
    searchable_text = searchable_text if searchable_text is not None else title
    projection, _ = SearchProjection.objects.update_or_create(**{field:revision},defaults={'content_kind':content_kind,'title':title,'searchable_text':searchable_text,'filter_metadata':filter_metadata or {}})
    if connection.vendor == 'postgresql':
        SearchProjection.objects.filter(pk=projection.pk).update(search_vector=SearchVector('title', weight='A') + SearchVector('searchable_text', weight='B'))
    projection.refresh_from_db()
    return projection

@transaction.atomic
def rebuild_published_projection(*, content_kind, revision):
    """Build the allow-listed public text from one exact current revision."""
    title = revision.title
    if content_kind == 'lesson':
        from content.richtext import plain_text
        values = [t for t in (plain_text(b) for b in revision.blocks if isinstance(b,dict)) if t]
        body = ' '.join(values)
    elif content_kind == 'playbook':
        body = ' '.join([revision.summary, revision.scenario])
    elif content_kind == 'module':
        body = revision.description
    elif content_kind == 'practice':
        body = ' '.join([revision.instructions, revision.prompt])
    else:
        raise ValidationError('Unsupported public content kind.')
    return rebuild_revision_projection(content_kind=content_kind, revision=revision,
        title=title, searchable_text=' '.join([title, body]).strip())
