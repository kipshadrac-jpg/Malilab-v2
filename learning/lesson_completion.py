"""Learner-confirmed Lesson completion (the "Mark this lesson as complete" button).

Records that the learner chose to mark the EXACT published lesson revision complete, linked to
every active Module requirement for that revision in a current published Module. Append-only and
idempotent per (learner, requirement). Stricter rules (time, quiz, etc.) are TO-BE-DEFINED and
can be added later without changing this record: evidence_kind states how it was recorded.
"""
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from content.models import ModuleLearningRequirement
from .models import LessonCompletion
from .services import require_verified_account

EVIDENCE_KIND = 'learner_marked_complete'


def applicable_requirements(lesson_revision):
    return list(ModuleLearningRequirement.objects.filter(
        target_kind='lesson', active=True, lesson_revision=lesson_revision,
        module_revision__status='published',
        module_revision__module__current_published_revision_id=F('module_revision_id')))


def has_outstanding(user, lesson_revision):
    """True if the learner still has something to record for this lesson revision."""
    reqs = applicable_requirements(lesson_revision)
    if not reqs:
        return not LessonCompletion.objects.filter(owner=user, lesson_revision=lesson_revision).exists()
    return any(not LessonCompletion.objects.filter(owner=user, lesson_revision=lesson_revision, requirement=r).exists() for r in reqs)


@transaction.atomic
def mark_lesson_complete(*, user, lesson_revision):
    require_verified_account(user)
    created = []
    for req in applicable_requirements(lesson_revision) or [None]:
        if LessonCompletion.objects.filter(owner=user, lesson_revision=lesson_revision, requirement=req).exists():
            continue
        created.append(LessonCompletion.objects.create(
            owner=user, lesson_revision=lesson_revision, requirement=req, evidence_kind=EVIDENCE_KIND,
            completed_at=timezone.now(), evidence_context={'method': 'learner_button'}))
    return created
