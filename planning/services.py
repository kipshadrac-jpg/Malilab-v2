from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import MyPlan, PlanRevision

def _verified(user):
    if not getattr(user,'can_use_personal_features',False):
        raise PermissionDenied('A verified active account is required.')

@transaction.atomic
def create_plan(*, user):
    _verified(user)
    return MyPlan.objects.create(owner=user)

@transaction.atomic
def append_revision(*, user, plan, target, assumptions, strategy_path, predecessor=None, journey=None, practice_attempt=None, calculation_result=None):
    _verified(user)
    plan=MyPlan.objects.select_for_update().get(pk=plan.pk,owner=user)
    refs=[journey,practice_attempt,calculation_result]
    if any(ref is not None and ref.owner_id != user.pk for ref in refs):
        raise PermissionDenied('Plan references must belong to the same account.')
    latest=plan.revisions.order_by('-revision_number').first()
    if predecessor is not None and (predecessor.plan_id != plan.pk or predecessor != latest):
        raise ValidationError('A new revision must follow the latest revision of this plan.')
    revision=PlanRevision.objects.create(plan=plan,revision_number=(latest.revision_number+1 if latest else 1),predecessor=latest,target=target,assumptions=assumptions,strategy_path=strategy_path,journey=journey,practice_attempt=practice_attempt,calculation_result=calculation_result)
    plan.current_revision=revision
    plan.save(update_fields=['current_revision','updated_at'])
    return revision
