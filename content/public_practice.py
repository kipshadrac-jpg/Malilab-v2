"""Practice activities as they appear inside a published module (exact, current, published only)."""
from django.db.models import F

from .models import ModuleLearningRequirement


def public_module_practice(module_revision):
    """Active practice requirements of this module revision whose activity is live and unchanged."""
    return list(ModuleLearningRequirement.objects.filter(
        module_revision=module_revision, target_kind='practice', active=True,
        practice_revision__status='published', practice_revision__activity__status='published',
        practice_revision__activity__current_published_revision_id=F('practice_revision_id'),
    ).select_related('practice_revision', 'practice_revision__activity').order_by('position'))
