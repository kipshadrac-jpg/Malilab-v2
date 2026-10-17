"""Human (staff) evaluation of submitted Practice attempts.

No automatic acceptance: an attempt only becomes accepted requirement evidence
when an MFA-verified staff member with the existing Reviewer role records it.
Rejected is recorded as history; retry/feedback rules remain TO-BE-DEFINED.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from content.models import ModuleLearningRequirement
from content.services import require_staff_mfa
from practice.models import PracticeAttempt

from .models import RequirementEvidence

EVALUATOR_ROLE = 'reviewer'


def require_evaluator(user):
    require_staff_mfa(user, EVALUATOR_ROLE)


def pending_attempts():
    """Submitted attempts with no evaluation recorded yet and at least one matching requirement."""
    matching = ModuleLearningRequirement.objects.filter(
        target_kind='practice', active=True).values('practice_revision_id')
    return (PracticeAttempt.objects
            .filter(state='submitted', practice_revision_id__in=matching)
            .exclude(requirement_evidence__isnull=False)
            .select_related('owner', 'practice_revision__activity')
            .order_by('submitted_at', 'pk'))


def candidate_requirements(attempt):
    return (ModuleLearningRequirement.objects
            .filter(target_kind='practice', active=True, practice_revision_id=attempt.practice_revision_id)
            .select_related('module_revision__module').order_by('module_revision_id', 'position'))


@transaction.atomic
def evaluate_attempt(*, evaluator, attempt_id, requirement_id, decision, note=''):
    require_evaluator(evaluator)
    if decision not in ('accepted', 'rejected'):
        raise ValidationError('Decision must be accepted or rejected.')
    attempt = (PracticeAttempt.objects.select_for_update()
               .select_related('owner', 'practice_revision').get(pk=attempt_id))
    requirement = (ModuleLearningRequirement.objects.select_related('module_revision')
                   .get(pk=requirement_id))
    evidence = RequirementEvidence(
        owner=attempt.owner, module_revision=requirement.module_revision, requirement=requirement,
        practice_revision=attempt.practice_revision, attempt=attempt, state=decision,
        evaluated_at=timezone.now(),
        evaluation_context={'method': 'staff_review', 'evaluator_id': evaluator.pk, 'note': (note or '')[:1000]})
    evidence.full_clean()   # enforces submitted-only, exact revision, one accepted attempt per requirement
    evidence.save()
    return evidence
