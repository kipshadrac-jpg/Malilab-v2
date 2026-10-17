from django.urls import reverse

from content.models import (Lesson, LessonRevision, Module, ModuleRevision, Playbook, PlaybookRevision,
                            PracticeActivity, PracticeActivityRevision)

KINDS = {
    'lesson': {'model': LessonRevision, 'identity_model': Lesson, 'identity': 'lesson',
               'label': 'Lesson', 'plural': 'Lessons', 'public': 'lesson-detail'},
    'practice': {'model': PracticeActivityRevision, 'identity_model': PracticeActivity, 'identity': 'activity',
                 'label': 'Practice activity', 'plural': 'Practice activities', 'public': 'practice-activity'},
    'module': {'model': ModuleRevision, 'identity_model': Module, 'identity': 'module',
               'label': 'Module', 'plural': 'Modules', 'public': 'module-detail'},
    'playbook': {'model': PlaybookRevision, 'identity_model': Playbook, 'identity': 'playbook',
                 'label': 'Playbook', 'plural': 'Playbooks', 'public': 'playbook-detail'},
}
ORDER = ('lesson', 'practice', 'module', 'playbook')


def revision_field(kind):
    """Name of the revision foreign key on EditorialReview / PublicationEvent (e.g. lesson_revision)."""
    return f'{kind}_revision'


def identity_of(kind, revision):
    return getattr(revision, KINDS[kind]['identity'])


def public_path(kind, revision):
    return reverse(KINDS[kind]['public'], args=[identity_of(kind, revision).slug])


def item(kind, revision, extra=''):
    cfg = KINDS[kind]
    identity = identity_of(kind, revision)
    return {
        'kind': kind, 'kind_label': cfg['label'], 'rev': revision, 'title': revision.title,
        'slug': identity.slug, 'number': revision.revision_number, 'extra': extra,
        'url': reverse('studio-revision', args=[kind, revision.pk]),
        'created': revision.created_at, 'status': revision.status,
    }
