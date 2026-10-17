from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class ImmutablePlanRevisionQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Plan revisions must be appended through the validated service path.')
    def update(self, **kwargs):
        raise ValidationError('Plan revisions are immutable; append a new revision.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Plan revisions are immutable; append a new revision.')
    def delete(self):
        raise ValidationError('Plan revisions cannot be bulk-deleted.')

class MyPlan(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='plans')
    status = models.CharField(max_length=16,default='active')
    current_revision = models.ForeignKey('PlanRevision',null=True,blank=True,on_delete=models.PROTECT,related_name='current_for_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: indexes=[models.Index(fields=['owner','updated_at'],name='plan_owner_updated_idx')]
    def clean(self):
        if self.current_revision_id and self.current_revision.plan_id != self.pk:
            raise ValidationError({'current_revision': 'Current revision must belong to this plan.'})
    def save(self, *args, **kwargs):
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exclude(owner_id=self.owner_id).exists():
            raise ValidationError({'owner': 'Plan ownership cannot be changed.'})
        self.full_clean()
        return super().save(*args, **kwargs)

class PlanRevision(models.Model):
    objects = ImmutablePlanRevisionQuerySet.as_manager()
    plan = models.ForeignKey(MyPlan,on_delete=models.PROTECT,related_name='revisions')
    revision_number = models.PositiveIntegerField()
    predecessor = models.ForeignKey('self',null=True,blank=True,on_delete=models.PROTECT,related_name='successors')
    target = models.JSONField(default=dict)
    assumptions = models.JSONField(default=dict)
    strategy_path = models.JSONField(default=dict)
    journey = models.ForeignKey('learning.LearningJourney',null=True,blank=True,on_delete=models.PROTECT,related_name='plan_revisions')
    practice_attempt = models.ForeignKey('practice.PracticeAttempt',null=True,blank=True,on_delete=models.PROTECT,related_name='plan_revisions')
    calculation_result = models.ForeignKey('calculations.CalculationResult',null=True,blank=True,on_delete=models.PROTECT,related_name='plan_revisions')
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def owner_id(self):
        return self.plan.owner_id
    class Meta:
        constraints=[models.UniqueConstraint(fields=['plan','revision_number'],name='plan_revision_uniq'),models.CheckConstraint(condition=models.Q(revision_number__gt=0),name='plan_revision_positive'),models.CheckConstraint(condition=models.Q(predecessor__isnull=True)|~models.Q(predecessor=models.F('id')),name='plan_revision_not_self')]
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Plan revisions are immutable; append a new revision.')
        self.full_clean(exclude=['target','assumptions','strategy_path'])
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Plan revisions are immutable and cannot be deleted.')
    def clean(self):
        if self.predecessor_id and (self.predecessor.plan_id != self.plan_id or self.predecessor.revision_number >= self.revision_number):
            raise ValidationError({'predecessor': 'Predecessor must belong to this plan and have a lower revision number.'})
        for field in ('journey','practice_attempt','calculation_result'):
            ref = getattr(self, field, None)
            if ref is not None and ref.owner_id != self.plan.owner_id:
                raise ValidationError({field: 'Private references must belong to the plan owner.'})
