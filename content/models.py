import uuid
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

class ProtectedHistoryQuerySet(models.QuerySet):
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Bulk creation is not allowed for editorial history.')
    def update(self, **kwargs):
        raise ValidationError('Use instance validation and the approved lifecycle service for editorial history.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Bulk updates are not allowed for editorial history.')
    def delete(self):
        raise ValidationError('Bulk deletion is not allowed for editorial history.')

class ImmutableRecordQuerySet(ProtectedHistoryQuerySet):
    """ORM bulk operations cannot rewrite immutable versions or events."""

class ImmutableVersionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Immutable versions cannot be bulk-updated.')
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError('Immutable versions cannot be bulk-updated.')
    def bulk_create(self, objs, **kwargs):
        raise ValidationError('Create versions through validated instance paths.')

class RevisionRecord(models.Model):
    """Draft-owned editorial data remains editable; reviewed history is frozen."""
    objects = ProtectedHistoryQuerySet.as_manager()
    class Meta: abstract = True
    revision_field = None
    def _parent_revision(self):
        return getattr(self, self.revision_field) if self.revision_field else None
    def save(self, *args, **kwargs):
        parent = self._parent_revision()
        if self._state.adding:
            if parent is not None and parent.status != 'draft':
                raise ValidationError('Editorial records cannot be added after review begins.')
        else:
            old = type(self).objects.get(pk=self.pk)
            old_parent = old._parent_revision()
            if any(p is not None and p.status != 'draft' for p in (old_parent, parent)):
                if old_parent is not None and parent is not None and old_parent.pk != parent.pk:
                    raise ValidationError('Editorial records cannot be moved between revisions.')
                if parent is not None and old_parent is not None and old_parent.pk != parent.pk:
                    raise ValidationError('Editorial records for reviewed revisions are immutable.')
            changed = [f.attname for f in self._meta.concrete_fields if f.attname not in ('id', 'created_at') and getattr(old, f.attname) != getattr(self, f.attname)]
            if changed and any(p is not None and p.status != 'draft' for p in (old_parent, parent)):
                raise ValidationError('Editorial records for reviewed revisions are immutable.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        parents = [self._parent_revision()]
        if self.pk:
            try:
                parents.append(type(self).objects.get(pk=self.pk)._parent_revision())
            except type(self).DoesNotExist:
                pass
        if any(parent is not None and parent.status != 'draft' for parent in parents):
            raise ValidationError('Editorial records for reviewed revisions cannot be deleted.')
        return super().delete(*args, **kwargs)

class EditorialRevision(models.Model):
    class Meta: abstract = True
    objects = ProtectedHistoryQuerySet.as_manager()
    protected_fields = ()
    def save(self, *args, **kwargs):
        if not self._state.adding:
            old = type(self).objects.get(pk=self.pk)
            if old.status != self.status and not getattr(self, '_allow_lifecycle_transition', False):
                raise ValidationError('Editorial lifecycle changes must use the approved governance service.')
            if old.status != 'draft':
                allowed = {'status'}
                changed = [f.attname for f in self._meta.concrete_fields if f.attname not in ('id', 'created_at') and getattr(old, f.attname) != getattr(self, f.attname)]
                if any(field not in allowed for field in changed):
                    raise ValidationError('Reviewed editorial revisions are immutable; create a new revision.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        if self.status != 'draft':
            raise ValidationError('Reviewed editorial revisions cannot be deleted.')
        return super().delete(*args, **kwargs)

class AppendOnlyEvent(models.Model):
    class Meta: abstract = True
    objects = ImmutableRecordQuerySet.as_manager()
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Editorial history events are append-only.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Editorial history events cannot be deleted.')

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: abstract = True

class MutableStamped(TimeStamped):
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class EditorialIdentity(MutableStamped):
    current_revision_field = 'current_published_revision'
    class Meta: abstract = True
    def save(self, *args, **kwargs):
        if not self._state.adding and not getattr(self, '_allow_pointer_update', False):
            old=type(self).objects.get(pk=self.pk)
            field=self.current_revision_field + '_id'
            if getattr(old, field) != getattr(self, field):
                raise ValidationError('Published revision pointers must be changed through the publication service.')
        return super().save(*args, **kwargs)

class MediaAsset(TimeStamped):
    objects = ImmutableVersionQuerySet.as_manager()
    asset_key = models.CharField(max_length=240, unique=True)
    media_kind = models.CharField(max_length=32)
    mime_type = models.CharField(max_length=127)
    byte_size = models.PositiveBigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128)
    rights_metadata = models.JSONField(default=dict)
    status = models.CharField(max_length=16, default='available')
    class Meta: indexes=[models.Index(fields=['media_kind','status'], name='media_kind_status_idx')]
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Media assets are immutable versions; create a new asset for changed metadata or bytes.')
        self.full_clean()
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)  # Protected by revision foreign keys while referenced.

class Source(MutableStamped):
    source_key = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=300)
    url_or_reference = models.TextField(blank=True)
    publication_date = models.DateField(null=True, blank=True)
    version_reference = models.CharField(max_length=160, blank=True)
    current_metadata = models.JSONField(default=dict, blank=True)

class Topic(MutableStamped):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, default='active')

class Playbook(EditorialIdentity):
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(max_length=16, default='draft')
    current_published_revision = models.ForeignKey('PlaybookRevision', null=True, blank=True, on_delete=models.PROTECT, related_name='current_for_playbooks')

class PlaybookRevision(EditorialRevision, TimeStamped):
    playbook = models.ForeignKey(Playbook, on_delete=models.PROTECT, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default='draft')
    title = models.CharField(max_length=240)
    summary = models.TextField(blank=True)
    scenario = models.TextField(blank=True)
    audience_context = models.JSONField(default=dict, blank=True)
    assumptions = models.JSONField(default=list, blank=True)
    discovery_metadata = models.JSONField(default=dict, blank=True)
    cover_asset = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.PROTECT, related_name='playbook_covers')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='authored_playbook_revisions')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['playbook','revision_number'], name='playbook_revision_uniq'), models.CheckConstraint(condition=models.Q(revision_number__gt=0), name='playbook_revision_positive')]

class Module(EditorialIdentity):
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(max_length=16, default='draft')
    current_published_revision = models.ForeignKey('ModuleRevision', null=True, blank=True, on_delete=models.PROTECT, related_name='current_for_modules')

class ModuleRevision(EditorialRevision, TimeStamped):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='authored_module_revisions')
    module = models.ForeignKey(Module, on_delete=models.PROTECT, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default='draft')
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['module','revision_number'], name='module_revision_uniq'), models.CheckConstraint(condition=models.Q(revision_number__gt=0), name='module_revision_positive')]

class Lesson(EditorialIdentity):
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(max_length=16, default='draft')
    current_published_revision = models.ForeignKey('LessonRevision', null=True, blank=True, on_delete=models.PROTECT, related_name='current_for_lessons')

class LessonRevision(EditorialRevision, TimeStamped):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='authored_lesson_revisions')
    lesson = models.ForeignKey(Lesson, on_delete=models.PROTECT, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default='draft')
    title = models.CharField(max_length=240)
    summary = models.TextField(blank=True)
    content_schema_version = models.PositiveIntegerField(default=1)
    blocks = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['lesson','revision_number'], name='lesson_revision_uniq'), models.CheckConstraint(condition=models.Q(revision_number__gt=0), name='lesson_revision_positive')]
    def clean(self):
        super().clean()
        validate_lesson_blocks(self.blocks)
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


def validate_lesson_blocks(blocks):
    """Validate the structured lesson block shapes (paragraph, heading, list, callout, table); no arbitrary markup is accepted."""
    from .richtext import RichTextError, validate_payload  # content.richtext
    if not isinstance(blocks, list):
        raise ValidationError({'blocks': 'Lesson blocks must be a list.'})
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValidationError({'blocks': f'Block {index} must be an object.'})
        if set(block) != {'key', 'type', 'position', 'payload'}:
            raise ValidationError({'blocks': f'Block {index} has unsupported or missing fields.'})
        if block.get('type') not in ('paragraph', 'heading', 'list', 'callout', 'table'):
            raise ValidationError({'blocks': f'Block {index} has an unsupported type.'})
        try:
            uuid.UUID(block.get('key'))
        except (ValueError, TypeError, AttributeError):
            raise ValidationError({'blocks': f'Block {index} requires a UUID key.'})
        position = block.get('position')
        if isinstance(position, bool) or not isinstance(position, int) or position < 0:
            raise ValidationError({'blocks': f'Block {index} requires a nonnegative integer position.'})
        try:
            validate_payload(block['type'], block.get('payload'))
        except RichTextError as exc:
            raise ValidationError({'blocks': f'Block {index}: {exc}.'})
    keys = [block['key'] for block in blocks]
    if len(keys) != len(set(keys)):
        raise ValidationError({'blocks': 'Block keys must be unique within a revision.'})
    positions = [block['position'] for block in blocks]
    if len(positions) != len(set(positions)):
        raise ValidationError({'blocks': 'Block positions must be unique within a revision.'})


class PracticeActivity(EditorialIdentity):
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(max_length=16, default='draft')
    current_published_revision = models.ForeignKey('PracticeActivityRevision', null=True, blank=True, on_delete=models.PROTECT, related_name='current_for_activities')

class PracticeActivityRevision(EditorialRevision, TimeStamped):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='authored_practice_revisions')
    activity = models.ForeignKey(PracticeActivity, on_delete=models.PROTECT, related_name='revisions')
    revision_number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, default='draft')
    title = models.CharField(max_length=240)
    instructions = models.TextField(blank=True)
    prompt = models.TextField(blank=True)
    response_schema = models.JSONField(default=dict)
    tool_refs = models.JSONField(default=list, blank=True)
    safety_text = models.TextField(blank=True)
    content_schema_version = models.PositiveIntegerField(default=1)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['activity','revision_number'], name='practice_revision_uniq'), models.CheckConstraint(condition=models.Q(revision_number__gt=0), name='practice_revision_positive')]

class ModuleLearningRequirement(RevisionRecord, TimeStamped):
    revision_field = 'module_revision'
    module_revision = models.ForeignKey(ModuleRevision, on_delete=models.PROTECT, related_name='learning_requirements')
    target_kind = models.CharField(max_length=12, choices=[('lesson','Lesson'),('practice','Practice')])
    lesson_revision = models.ForeignKey(LessonRevision, null=True, blank=True, on_delete=models.PROTECT, related_name='module_requirements')
    practice_revision = models.ForeignKey(PracticeActivityRevision, null=True, blank=True, on_delete=models.PROTECT, related_name='module_requirements')
    CLASSIFICATIONS = [('required', 'Required'), ('optional', 'Optional'), ('recommended', 'Recommended')]
    classification = models.CharField(max_length=16, choices=CLASSIFICATIONS, default='required')
    position = models.PositiveIntegerField()
    completion_condition_key = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(classification__in=['required','optional','recommended']), name='requirement_classification_valid'),models.CheckConstraint(condition=(models.Q(target_kind='lesson',lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(target_kind='practice',lesson_revision__isnull=True,practice_revision__isnull=False)),name='requirement_target_kind_match'),models.UniqueConstraint(fields=['module_revision','position'],name='requirement_position_uniq'),models.UniqueConstraint(fields=['module_revision','lesson_revision'],condition=models.Q(lesson_revision__isnull=False),name='requirement_lesson_target_uniq'),models.UniqueConstraint(fields=['module_revision','practice_revision'],condition=models.Q(practice_revision__isnull=False),name='requirement_practice_target_uniq')]
    def clean(self):
        super().clean()
        if self.classification not in dict(self.CLASSIFICATIONS):
            raise ValidationError({'classification': 'Classification must be required, optional, or recommended.'})
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class PlaybookModuleRecommendation(RevisionRecord, TimeStamped):
    revision_field = 'playbook_revision'
    playbook_revision = models.ForeignKey(PlaybookRevision,on_delete=models.PROTECT,related_name='module_recommendations')
    module_revision = models.ForeignKey(ModuleRevision,on_delete=models.PROTECT,related_name='playbook_recommendations')
    position = models.PositiveIntegerField()
    rationale = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['playbook_revision','position'],name='recommendation_position_uniq'),models.UniqueConstraint(fields=['playbook_revision','module_revision'],name='recommendation_module_uniq')]

class ContentTopicAssignment(RevisionRecord, TimeStamped):
    content_kind = models.CharField(max_length=16, choices=[('playbook','Playbook'),('module','Module'),('lesson','Lesson'),('practice','Practice')])
    playbook_revision = models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='topic_assignments')
    module_revision = models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='topic_assignments')
    lesson_revision = models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='topic_assignments')
    practice_revision = models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='topic_assignments')
    topic = models.ForeignKey(Topic,on_delete=models.PROTECT,related_name='assignments')
    role = models.CharField(max_length=32,default='topic')
    position = models.PositiveIntegerField(null=True,blank=True)
    class Meta:
        constraints=[models.CheckConstraint(condition=(models.Q(content_kind='playbook',playbook_revision__isnull=False,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='module',playbook_revision__isnull=True,module_revision__isnull=False,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='lesson',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(content_kind='practice',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=False)),name='topic_target_kind_match')]
    def _parent_revision(self):
        return getattr(self, {'playbook':'playbook_revision','module':'module_revision','lesson':'lesson_revision','practice':'practice_revision'}.get(self.content_kind,''), None)

class AchievementDefinition(MutableStamped):
    slug = models.SlugField(max_length=160,unique=True)
    status = models.CharField(max_length=16,default='draft')
    current_revision = models.ForeignKey('AchievementDefinitionRevision',null=True,blank=True,on_delete=models.PROTECT,related_name='current_for_definitions')

class AchievementDefinitionRevision(EditorialRevision, TimeStamped):
    definition = models.ForeignKey(AchievementDefinition,on_delete=models.PROTECT,related_name='revisions')
    revision_number = models.PositiveIntegerField()
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    criteria_key = models.CharField(max_length=100)
    criteria_config = models.JSONField(default=dict)
    status = models.CharField(max_length=16,default='draft')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['definition','revision_number'],name='achievement_revision_uniq'),models.CheckConstraint(condition=models.Q(revision_number__gt=0),name='achievement_revision_positive')]

class SourceSnapshot(RevisionRecord, TimeStamped):
    def _parent_revision(self):
        return getattr(self, {'playbook':'playbook_revision','module':'module_revision','lesson':'lesson_revision','practice':'practice_revision'}.get(self.content_kind,''), None)
    source = models.ForeignKey(Source,on_delete=models.PROTECT,related_name='snapshots')
    source_identity_snapshot = models.CharField(max_length=160, null=True, blank=True)
    content_kind = models.CharField(max_length=16,choices=[('playbook','Playbook'),('module','Module'),('lesson','Lesson'),('practice','Practice')])
    playbook_revision = models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='source_snapshots')
    module_revision = models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='source_snapshots')
    lesson_revision = models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='source_snapshots')
    practice_revision = models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='source_snapshots')
    title_snapshot = models.CharField(max_length=300)
    url_snapshot = models.TextField(blank=True)
    publication_date_snapshot = models.DateField(null=True,blank=True)
    version_snapshot = models.CharField(max_length=160,blank=True)
    retrieved_at = models.DateTimeField(null=True,blank=True)
    reviewed_at = models.DateTimeField(null=True,blank=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name='source_reviews')
    class Meta:
        constraints=[models.CheckConstraint(condition=(models.Q(content_kind='playbook',playbook_revision__isnull=False,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='module',playbook_revision__isnull=True,module_revision__isnull=False,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='lesson',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(content_kind='practice',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=False)),name='source_snapshot_target_kind_match')]
    def save(self, *args, **kwargs):
        if self._state.adding and self.source_id:
            self.source_identity_snapshot = self.source_identity_snapshot or self.source.source_key
            self.title_snapshot = self.title_snapshot or self.source.title
            self.url_snapshot = self.url_snapshot or self.source.url_or_reference
            self.publication_date_snapshot = self.publication_date_snapshot or self.source.publication_date
            self.version_snapshot = self.version_snapshot or self.source.version_reference
        if self.reviewed_at and not self.reviewer_id:
            raise ValidationError({'reviewer': 'A reviewed source snapshot must retain its reviewer.'})
        if self.reviewer_id and not self.reviewed_at:
            raise ValidationError({'reviewed_at': 'A reviewed source snapshot must retain its review time.'})
        return super().save(*args, **kwargs)

class EditorialReview(AppendOnlyEvent, TimeStamped):
    content_kind = models.CharField(max_length=16, choices=[('playbook','Playbook'),('module','Module'),('lesson','Lesson'),('practice','Practice')])
    playbook_revision = models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='reviews')
    module_revision = models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='reviews')
    lesson_revision = models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='reviews')
    practice_revision = models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='editorial_reviews')
    role_snapshot = models.CharField(max_length=32)
    action = models.CharField(max_length=24)
    comment = models.TextField(blank=True)
    class Meta:
        indexes=[models.Index(fields=['reviewer','created_at'],name='editorial_actor_time_idx')]
        constraints=[models.CheckConstraint(condition=(models.Q(content_kind='playbook',playbook_revision__isnull=False,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='module',playbook_revision__isnull=True,module_revision__isnull=False,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='lesson',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(content_kind='practice',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=False)),name='editorial_review_target_match')]

class PublicationEvent(AppendOnlyEvent, TimeStamped):
    content_kind = models.CharField(max_length=16, choices=[('playbook','Playbook'),('module','Module'),('lesson','Lesson'),('practice','Practice')])
    playbook_revision = models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='publication_events')
    module_revision = models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='publication_events')
    lesson_revision = models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='publication_events')
    practice_revision = models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='publication_events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.PROTECT,related_name='publication_events')
    role_snapshot = models.CharField(max_length=32)
    action = models.CharField(max_length=24)
    class Meta:
        indexes=[models.Index(fields=['actor','created_at'],name='publication_actor_time_idx')]
        constraints=[models.CheckConstraint(condition=(models.Q(content_kind='playbook',playbook_revision__isnull=False,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='module',playbook_revision__isnull=True,module_revision__isnull=False,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='lesson',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(content_kind='practice',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=False)),name='publication_event_target_match')]

class RelatedContentRelationship(RevisionRecord, TimeStamped):
    CONTENT_KINDS=[('playbook','Playbook'),('module','Module'),('lesson','Lesson'),('practice','Practice')]
    source_kind=models.CharField(max_length=16,choices=CONTENT_KINDS)
    source_playbook=models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='outgoing_related_links')
    source_module=models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='outgoing_related_links')
    source_lesson=models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='outgoing_related_links')
    source_practice=models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='outgoing_related_links')
    target_kind=models.CharField(max_length=16,choices=CONTENT_KINDS)
    target_playbook=models.ForeignKey(PlaybookRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='incoming_related_links')
    target_module=models.ForeignKey(ModuleRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='incoming_related_links')
    target_lesson=models.ForeignKey(LessonRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='incoming_related_links')
    target_practice=models.ForeignKey(PracticeActivityRevision,null=True,blank=True,on_delete=models.PROTECT,related_name='incoming_related_links')
    relationship_kind=models.CharField(max_length=32)
    position=models.PositiveIntegerField(null=True,blank=True)
    rationale=models.TextField(blank=True)
    class Meta:
        constraints=[
          models.CheckConstraint(condition=(models.Q(source_kind='playbook',source_playbook__isnull=False,source_module__isnull=True,source_lesson__isnull=True,source_practice__isnull=True)|models.Q(source_kind='module',source_playbook__isnull=True,source_module__isnull=False,source_lesson__isnull=True,source_practice__isnull=True)|models.Q(source_kind='lesson',source_playbook__isnull=True,source_module__isnull=True,source_lesson__isnull=False,source_practice__isnull=True)|models.Q(source_kind='practice',source_playbook__isnull=True,source_module__isnull=True,source_lesson__isnull=True,source_practice__isnull=False)),name='related_source_kind_match'),
          models.CheckConstraint(condition=(models.Q(target_kind='playbook',target_playbook__isnull=False,target_module__isnull=True,target_lesson__isnull=True,target_practice__isnull=True)|models.Q(target_kind='module',target_playbook__isnull=True,target_module__isnull=False,target_lesson__isnull=True,target_practice__isnull=True)|models.Q(target_kind='lesson',target_playbook__isnull=True,target_module__isnull=True,target_lesson__isnull=False,target_practice__isnull=True)|models.Q(target_kind='practice',target_playbook__isnull=True,target_module__isnull=True,target_lesson__isnull=True,target_practice__isnull=False)),name='related_target_kind_match')]
        indexes=[models.Index(fields=['source_kind','relationship_kind','position'],name='related_source_order_idx')]
    def _parent_revision(self):
        return getattr(self, {'playbook':'source_playbook','module':'source_module','lesson':'source_lesson','practice':'source_practice'}.get(self.source_kind,''), None)
