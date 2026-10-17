from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError

class AppendOnlyQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Append-only records must be created through validated instance/service paths.')
    def update(self, **kwargs):
        raise ValidationError('Append-only records cannot be bulk-updated.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Append-only records cannot be bulk-updated.')
    def delete(self):
        raise ValidationError('Append-only records cannot be bulk-deleted.')

class AppendOnlyModel(models.Model):
    class Meta: abstract = True
    objects = AppendOnlyQuerySet.as_manager()
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(f'{self.__class__.__name__} records are append-only.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError(f'{self.__class__.__name__} records cannot be deleted.')

class LearningJourney(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='learning_journeys')
    starting_context = models.JSONField(default=dict,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: indexes=[models.Index(fields=['owner','created_at'],name='journey_owner_time_idx')]
    def save(self, *args, **kwargs):
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exclude(owner_id=self.owner_id).exists():
            raise ValidationError({'owner': 'Journey ownership cannot be changed.'})
        return super().save(*args, **kwargs)

class JourneyTargetRef(models.Model):
    TARGETS=[('playbook','PlaybookRevision'),('module','ModuleRevision'),('lesson','LessonRevision'),('practice','PracticeRevision'),('attempt','PracticeAttempt'),('calculation','CalculationResult'),('plan','PlanRevision')]
    target_kind=models.CharField(max_length=16,choices=TARGETS)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name='journey_targets')
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self._state.adding and type(self).objects.filter(pk=self.pk, steps__isnull=False).exists():
            old=type(self).objects.get(pk=self.pk)
            if old.target_kind != self.target_kind or old.owner_id != self.owner_id:
                raise ValidationError('A target registry referenced by journey history is immutable.')
        return super().save(*args, **kwargs)

class JourneyTargetLink(models.Model):
    objects = AppendOnlyQuerySet.as_manager()
    expected_kind = None
    private_target = False
    class Meta: abstract = True
    def clean(self):
        if self.target_ref.target_kind != self.expected_kind:
            raise ValidationError({'target_ref': 'Target association kind does not match its registry.'})
        if self.private_target:
            if not getattr(self.target, 'owner_id', None) or self.target_ref.owner_id != self.target.owner_id:
                raise ValidationError({'target_ref': 'Private target owner must match the target registry.'})
        elif self.target_ref.owner_id is not None:
            raise ValidationError({'target_ref': 'Editorial target registry cannot have a private owner.'})
        association_models = (JourneyPlaybookTarget, JourneyModuleTarget, JourneyLessonTarget,
            JourneyPracticeTarget, JourneyAttemptTarget, JourneyCalculationTarget, JourneyPlanTarget)
        for model in association_models:
            if model is not type(self) and model.objects.filter(target_ref_id=self.target_ref_id).exists():
                raise ValidationError({'target_ref': 'A target registry may have exactly one subtype association.'})
    def save(self, *args, **kwargs):
        if self.target_ref.steps.exists():
            raise ValidationError('Journey target associations cannot change after a step references them.')
        self.full_clean()
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.target_ref.steps.exists():
            raise ValidationError('Journey target associations referenced by history cannot be deleted.')
        return super().delete(*args, **kwargs)

class JourneyStep(AppendOnlyModel):
    journey=models.ForeignKey(LearningJourney,on_delete=models.PROTECT,related_name='steps')
    target_ref=models.ForeignKey(JourneyTargetRef,on_delete=models.PROTECT,related_name='steps')
    sequence=models.PositiveIntegerField()
    step_type=models.CharField(max_length=32)
    state=models.CharField(max_length=24,default='planned')
    occurred_at=models.DateTimeField(null=True,blank=True)
    recorded_at=models.DateTimeField(auto_now_add=True)
    context_metadata=models.JSONField(default=dict,blank=True)
    class Meta:
        ordering=['sequence','pk']
        constraints=[models.UniqueConstraint(fields=['journey','sequence'],name='journey_step_seq_uniq'),models.CheckConstraint(condition=models.Q(sequence__gt=0),name='journey_step_seq_positive')]
    def clean(self):
        from .services import validate_journey_target
        validate_journey_target(self.journey, self.target_ref)
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class JourneyPlaybookTarget(JourneyTargetLink):
    expected_kind='playbook'
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='playbook_target')
    target=models.ForeignKey('content.PlaybookRevision',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyModuleTarget(JourneyTargetLink):
    expected_kind='module'
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='module_target')
    target=models.ForeignKey('content.ModuleRevision',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyLessonTarget(JourneyTargetLink):
    expected_kind='lesson'
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='lesson_target')
    target=models.ForeignKey('content.LessonRevision',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyPracticeTarget(JourneyTargetLink):
    expected_kind='practice'
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='practice_target')
    target=models.ForeignKey('content.PracticeActivityRevision',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyAttemptTarget(JourneyTargetLink):
    expected_kind='attempt'
    private_target=True
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='attempt_target')
    target=models.ForeignKey('practice.PracticeAttempt',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyCalculationTarget(JourneyTargetLink):
    expected_kind='calculation'
    private_target=True
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='calculation_target')
    target=models.ForeignKey('calculations.CalculationResult',on_delete=models.PROTECT,related_name='journey_target_links')
class JourneyPlanTarget(JourneyTargetLink):
    expected_kind='plan'
    private_target=True
    target_ref=models.OneToOneField(JourneyTargetRef,on_delete=models.PROTECT,related_name='plan_target')
    target=models.ForeignKey('planning.PlanRevision',on_delete=models.PROTECT,related_name='journey_target_links')

class Note(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='notes')
    kind=models.CharField(max_length=16,choices=[('note','Note'),('highlight','Highlight')])
    body=models.TextField(blank=True)
    lesson_revision=models.ForeignKey('content.LessonRevision',null=True,blank=True,on_delete=models.PROTECT,related_name='notes')
    block_key=models.CharField(max_length=80,blank=True)
    anchor_schema_version=models.PositiveIntegerField(null=True,blank=True)
    anchor_data=models.JSONField(null=True,blank=True)
    journey=models.ForeignKey(LearningJourney,null=True,blank=True,on_delete=models.PROTECT,related_name='notes')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    class Meta: indexes=[models.Index(fields=['owner','updated_at'],name='note_owner_updated_idx'),models.Index(fields=['lesson_revision','block_key'],name='note_lesson_block_idx')]
    def clean(self):
        if self.journey_id and self.journey.owner_id != self.owner_id:
            raise ValidationError({'journey': 'Journey must belong to the note owner.'})
        if self.kind == 'highlight':
            from .services import validate_note_anchor
            validate_note_anchor(self.lesson_revision, self.block_key, self.anchor_data)
    def save(self, *args, **kwargs):
        if not self._state.adding and type(self).objects.filter(pk=self.pk).exclude(owner_id=self.owner_id).exists():
            raise ValidationError({'owner': 'Note ownership cannot be changed.'})
        self.full_clean()
        return super().save(*args, **kwargs)

class LessonCompletion(AppendOnlyModel):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='lesson_completions')
    lesson_revision=models.ForeignKey('content.LessonRevision',on_delete=models.PROTECT,related_name='completions')
    requirement=models.ForeignKey('content.ModuleLearningRequirement',null=True,blank=True,on_delete=models.PROTECT,related_name='lesson_completions')
    journey_step=models.ForeignKey(JourneyStep,null=True,blank=True,on_delete=models.PROTECT,related_name='lesson_completions')
    evidence_kind=models.CharField(max_length=32)
    completed_at=models.DateTimeField()
    recorded_at=models.DateTimeField(auto_now_add=True)
    evidence_context=models.JSONField(default=dict,blank=True)
    class Meta: indexes=[models.Index(fields=['owner','completed_at'],name='lessoncomp_owner_time_idx')]
    def clean(self):
        if self.requirement_id and (self.requirement.target_kind != 'lesson' or self.requirement.lesson_revision_id != self.lesson_revision_id):
            raise ValidationError({'requirement': 'Requirement must target this exact LessonRevision.'})
        if self.journey_step_id:
            if self.journey_step.journey.owner_id != self.owner_id:
                raise ValidationError({'journey_step': 'Journey step must belong to the completion owner.'})
            if self.journey_step.target_ref.target_kind != 'lesson' or self.journey_step.target_ref.lesson_target.target_id != self.lesson_revision_id:
                raise ValidationError({'journey_step': 'Journey step must reference this exact LessonRevision.'})
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class RequirementEvidence(AppendOnlyModel):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='requirement_evidence')
    module_revision=models.ForeignKey('content.ModuleRevision',on_delete=models.PROTECT,related_name='evidence_records')
    requirement=models.ForeignKey('content.ModuleLearningRequirement',on_delete=models.PROTECT,related_name='evidence_records')
    practice_revision=models.ForeignKey('content.PracticeActivityRevision',on_delete=models.PROTECT,related_name='requirement_evidence')
    attempt=models.ForeignKey('practice.PracticeAttempt',on_delete=models.PROTECT,related_name='requirement_evidence')
    state=models.CharField(max_length=16,choices=[('pending','Pending'),('accepted','Accepted'),('rejected','Rejected'),('superseded','Superseded')])
    recorded_at=models.DateTimeField(auto_now_add=True)
    evaluated_at=models.DateTimeField(null=True,blank=True)
    supersedes=models.ForeignKey('self',null=True,blank=True,on_delete=models.PROTECT,related_name='superseding_records')
    evaluation_context=models.JSONField(default=dict,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['attempt','requirement'],name='evidence_attempt_requirement_uniq'),models.UniqueConstraint(fields=['attempt'],condition=models.Q(state='accepted'),name='evidence_attempt_accepted_uniq')]
        indexes=[models.Index(fields=['owner','module_revision','requirement','state'],name='evidence_owner_req_idx')]
    def clean(self):
        from .services import validate_requirement_evidence
        validate_requirement_evidence(self)
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class ModuleCompletion(AppendOnlyModel):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='module_completions')
    module_revision=models.ForeignKey('content.ModuleRevision',on_delete=models.PROTECT,related_name='completions')
    evaluated_at=models.DateTimeField(auto_now_add=True)
    outcome=models.CharField(max_length=16)
    evidence_snapshot=models.JSONField(default=dict)
    journey=models.ForeignKey(LearningJourney,null=True,blank=True,on_delete=models.PROTECT,related_name='module_completions')
    class Meta: indexes=[models.Index(fields=['owner','module_revision','evaluated_at'],name='modulecomp_owner_rev_idx')]
    def clean(self):
        if self.journey_id and self.journey.owner_id != self.owner_id:
            raise ValidationError({'journey': 'Journey must belong to the completion owner.'})
        rows = self.evidence_snapshot.get('requirements') if isinstance(self.evidence_snapshot, dict) else None
        if not isinstance(rows, list) or self.evidence_snapshot.get('module_revision_id') != self.module_revision_id:
            raise ValidationError({'evidence_snapshot': 'Completion must preserve a requirement snapshot for this exact revision.'})
        requirements = list(self.module_revision.learning_requirements.filter(active=True).order_by('position','pk'))
        by_id = {row.get('requirement_id'): row for row in rows if isinstance(row, dict)}
        if set(by_id) != {req.pk for req in requirements}:
            raise ValidationError({'evidence_snapshot': 'Snapshot must contain the exact active requirement set.'})
        complete = True
        for req in requirements:
            row = by_id[req.pk]
            if row.get('classification') != req.classification:
                raise ValidationError({'evidence_snapshot': 'Requirement classification does not match the pinned revision.'})
            if req.classification == 'required':
                evidence_id = row.get('evidence_id')
                if evidence_id and req.target_kind == 'practice':
                    valid = RequirementEvidence.objects.filter(pk=evidence_id, owner_id=self.owner_id,
                        module_revision_id=self.module_revision_id, requirement_id=req.pk, state='accepted',
                        attempt__state='submitted', attempt__submitted_at__isnull=False).exists()
                    if not valid:
                        raise ValidationError({'evidence_snapshot': 'Required evidence must be accepted, submitted, owned, and revision-exact.'})
                elif evidence_id and req.target_kind == 'lesson':
                    valid = LessonCompletion.objects.filter(pk=evidence_id, owner_id=self.owner_id,
                        lesson_revision_id=req.lesson_revision_id, requirement_id=req.pk).exists()
                    if not valid:
                        raise ValidationError({'evidence_snapshot': 'Lesson evidence must be owned and revision-exact.'})
                elif row.get('satisfied'):
                    raise ValidationError({'evidence_snapshot': 'A required item cannot be satisfied without exact evidence.'})
                if not row.get('satisfied'):
                    complete = False
        if self.outcome != ('complete' if complete else 'incomplete') or self.evidence_snapshot.get('complete') != complete:
            raise ValidationError({'outcome': 'Completion outcome must match its required evidence snapshot.'})
    def save(self, *args, **kwargs):
        self.full_clean(exclude=['evidence_snapshot'])
        return super().save(*args, **kwargs)

class UserAchievement(models.Model):
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='achievements')
    definition_revision=models.ForeignKey('content.AchievementDefinitionRevision',on_delete=models.PROTECT,related_name='awards')
    awarded_at=models.DateTimeField(auto_now_add=True)
    module_completion=models.ForeignKey(ModuleCompletion,null=True,blank=True,on_delete=models.PROTECT,related_name='achievement_awards')
    plan_revision=models.ForeignKey('planning.PlanRevision',null=True,blank=True,on_delete=models.PROTECT,related_name='achievement_awards')
    evidence=models.JSONField(default=dict)
    class Meta: indexes=[models.Index(fields=['owner','awarded_at'],name='award_owner_time_idx')]
    def clean(self):
        if self.module_completion_id and self.module_completion.owner_id != self.owner_id:
            raise ValidationError({'module_completion': 'Completion must belong to the award owner.'})
        if self.plan_revision_id and self.plan_revision.plan.owner_id != self.owner_id:
            raise ValidationError({'plan_revision': 'Plan revision must belong to the award owner.'})
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Achievement awards are immutable.')
        self.full_clean()
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Achievement awards cannot be deleted.')
