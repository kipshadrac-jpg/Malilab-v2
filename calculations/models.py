from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class ImmutableSnapshotQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Immutable calculation snapshots must be created through validated instance paths.')
    def update(self, **kwargs):
        raise ValidationError('Immutable calculation snapshots cannot be bulk-updated.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Immutable calculation snapshots cannot be bulk-updated.')
    def delete(self):
        raise ValidationError('Immutable calculation snapshots cannot be bulk-deleted.')

class LabTool(models.Model):
    slug = models.SlugField(max_length=160,unique=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16,default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CalculatorDefinition(models.Model):
    lab_tool = models.ForeignKey(LabTool,on_delete=models.PROTECT,related_name='definitions')
    key = models.SlugField(max_length=120)
    contract_schema_version = models.PositiveIntegerField(default=1)
    input_contract = models.JSONField(default=dict)
    output_contract = models.JSONField(default=dict)
    current_formula_version = models.ForeignKey('FormulaVersion',null=True,blank=True,on_delete=models.PROTECT,related_name='current_for_definitions')
    status = models.CharField(max_length=16,default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['lab_tool','key'],name='calculator_key_uniq')]

class FormulaVersion(models.Model):
    definition = models.ForeignKey(CalculatorDefinition,on_delete=models.PROTECT,related_name='versions')
    version_key = models.CharField(max_length=100)
    state = models.CharField(max_length=16,default='draft',choices=[('draft','Draft'),('tested','Tested'),('reviewed','Reviewed'),('approved','Approved'),('active','Active'),('retired','Retired')])
    artifact_ref = models.CharField(max_length=240,blank=True)
    artifact_checksum = models.CharField(max_length=128,blank=True)
    assumptions = models.JSONField(default=dict)
    test_evidence = models.JSONField(default=dict)
    source_evidence = models.JSONField(default=dict)
    methodology = models.JSONField(default=dict)
    rounding_method = models.CharField(max_length=80,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['definition','version_key'],name='formula_version_key_uniq'),models.UniqueConstraint(fields=['definition'],condition=models.Q(state='active'),name='formula_one_active_uniq')]

class FormulaApproval(models.Model):
    formula_version = models.ForeignKey(FormulaVersion,on_delete=models.PROTECT,related_name='approvals')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='formula_approvals')
    role_snapshot = models.CharField(max_length=32)
    action = models.CharField(max_length=24)
    evidence_refs = models.JSONField(default=dict)
    note = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)
    class Meta: indexes=[models.Index(fields=['formula_version','occurred_at'],name='formula_approval_time_idx'),models.Index(fields=['actor','occurred_at'],name='formula_actor_time_idx')]

class CalculationResult(models.Model):
    objects = ImmutableSnapshotQuerySet.as_manager()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='calculation_results')
    formula_version = models.ForeignKey(FormulaVersion,on_delete=models.PROTECT,related_name='results')
    practice_attempt = models.ForeignKey('practice.PracticeAttempt',null=True,blank=True,on_delete=models.PROTECT,related_name='calculation_results')
    inputs = models.JSONField(default=dict)
    assumptions = models.JSONField(default=dict)
    outputs = models.JSONField(default=dict)
    unit = models.CharField(max_length=48,blank=True)
    currency = models.CharField(max_length=3,blank=True)
    precision_policy = models.CharField(max_length=100,blank=True)
    rounding_method = models.CharField(max_length=80,blank=True)
    methodology_version = models.CharField(max_length=100,blank=True)
    source_snapshot = models.JSONField(default=dict)
    warnings = models.JSONField(default=list)
    saved_label = models.CharField(max_length=160,blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    class Meta: indexes=[models.Index(fields=['owner','calculated_at'],name='result_owner_time_idx'),models.Index(fields=['practice_attempt','calculated_at'],name='result_attempt_time_idx')]
    def clean(self):
        if self.practice_attempt_id and self.practice_attempt.owner_id != self.owner_id:
            raise ValidationError({'practice_attempt': 'Attempt must belong to the result owner.'})
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Saved calculation results are immutable.')
        self.full_clean(exclude=['inputs','assumptions','outputs','source_snapshot','warnings'])
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Saved calculation results cannot be deleted.')
