from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class PracticeHistoryQuerySet(models.QuerySet):
    """Supported ORM paths cannot bulk-mutate learner history."""
    def update(self, **kwargs):
        raise ValidationError('Practice history must be changed through validated services.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Practice history cannot be bulk-updated.')
    def delete(self):
        raise ValidationError('Practice history cannot be bulk-deleted.')
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Practice history must be created through validated services.')

class PracticeAttempt(models.Model):
    objects = PracticeHistoryQuerySet.as_manager()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='practice_attempts')
    practice_revision = models.ForeignKey('content.PracticeActivityRevision',on_delete=models.PROTECT,related_name='attempts')
    journey = models.ForeignKey('learning.LearningJourney',null=True,blank=True,on_delete=models.PROTECT,related_name='practice_attempts')
    state = models.CharField(max_length=16,default='started',choices=[('started','Started'),('submitted','Submitted'),('abandoned','Abandoned')])
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True,blank=True)
    response_summary = models.JSONField(default=dict,blank=True)
    class Meta:
        indexes=[models.Index(fields=['owner','submitted_at'],name='attempt_owner_time_idx')]
    def clean(self):
        if self.journey_id and self.journey.owner_id != self.owner_id:
            raise ValidationError({'journey': 'Journey must belong to the attempt owner.'})
    def save(self, *args, **kwargs):
        if not self._state.adding:
            old = type(self).objects.get(pk=self.pk)
            if old.owner_id != self.owner_id:
                raise ValidationError({'owner': 'Attempt ownership cannot be changed.'})
            if old.state == 'submitted' and any(getattr(old, f.attname) != getattr(self, f.attname) for f in self._meta.concrete_fields if f.attname not in ('id',)):
                raise ValidationError('Submitted attempts are immutable.')
        self.full_clean()
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.state == 'submitted':
            raise ValidationError('Submitted PracticeAttempt history cannot be deleted.')
        return super().delete(*args, **kwargs)

class PracticeResponse(models.Model):
    objects = PracticeHistoryQuerySet.as_manager()
    attempt = models.ForeignKey(PracticeAttempt,on_delete=models.PROTECT,related_name='responses')
    prompt_key = models.CharField(max_length=120)
    value = models.JSONField()
    unit = models.CharField(max_length=48,blank=True)
    answered_at = models.DateTimeField(auto_now=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['attempt','prompt_key'],name='response_prompt_uniq')]
    def save(self, *args, **kwargs):
        if self._state.adding and self.attempt.state != 'started':
            raise ValidationError('Responses for submitted attempts are immutable.')
        if not self._state.adding:
            old = type(self).objects.get(pk=self.pk)
            if old.attempt_id != self.attempt_id or old.attempt.state != 'started':
                raise ValidationError('Submitted responses cannot be modified.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.attempt.state != 'started':
            raise ValidationError('Responses for submitted attempts cannot be deleted.')
        return super().delete(*args, **kwargs)
