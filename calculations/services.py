from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .models import CalculationResult

def save_result(*, user, formula_version, inputs, outputs, assumptions=None, practice_attempt=None, **snapshots):
    if not getattr(user,'can_use_personal_features',False):
        raise PermissionDenied('A verified active account is required.')
    if formula_version.state != 'active':
        raise ValidationError('Only an active approved formula can produce a saved result.')
    if practice_attempt is not None and practice_attempt.owner_id != user.pk:
        raise PermissionDenied('Practice attempt belongs to another account.')
    return CalculationResult.objects.create(owner=user,formula_version=formula_version,practice_attempt=practice_attempt,inputs=inputs,outputs=outputs,assumptions=assumptions or {},**snapshots)
