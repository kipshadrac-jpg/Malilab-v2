from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

class SearchProjection(models.Model):
    content_kind=models.CharField(max_length=16)
    playbook_revision=models.ForeignKey('content.PlaybookRevision',null=True,blank=True,on_delete=models.CASCADE,related_name='search_projection')
    module_revision=models.ForeignKey('content.ModuleRevision',null=True,blank=True,on_delete=models.CASCADE,related_name='search_projection')
    lesson_revision=models.ForeignKey('content.LessonRevision',null=True,blank=True,on_delete=models.CASCADE,related_name='search_projection')
    practice_revision=models.ForeignKey('content.PracticeActivityRevision',null=True,blank=True,on_delete=models.CASCADE,related_name='search_projection')
    title=models.TextField()
    searchable_text=models.TextField()
    search_vector=SearchVectorField(null=True)
    filter_metadata=models.JSONField(default=dict)
    schema_version=models.PositiveIntegerField(default=1)
    indexed_at=models.DateTimeField(auto_now=True)
    class Meta:
        indexes=[GinIndex(fields=['search_vector'],name='search_vector_gin_idx')]
        constraints=[
            models.CheckConstraint(condition=(models.Q(content_kind='playbook',playbook_revision__isnull=False,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='module',playbook_revision__isnull=True,module_revision__isnull=False,lesson_revision__isnull=True,practice_revision__isnull=True)|models.Q(content_kind='lesson',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=False,practice_revision__isnull=True)|models.Q(content_kind='practice',playbook_revision__isnull=True,module_revision__isnull=True,lesson_revision__isnull=True,practice_revision__isnull=False)),name='search_projection_target_kind_match'),
            models.UniqueConstraint(fields=['playbook_revision'],condition=models.Q(playbook_revision__isnull=False),name='search_playbook_revision_uniq'),
            models.UniqueConstraint(fields=['module_revision'],condition=models.Q(module_revision__isnull=False),name='search_module_revision_uniq'),
            models.UniqueConstraint(fields=['lesson_revision'],condition=models.Q(lesson_revision__isnull=False),name='search_lesson_revision_uniq'),
            models.UniqueConstraint(fields=['practice_revision'],condition=models.Q(practice_revision__isnull=False),name='search_practice_revision_uniq'),
        ]
