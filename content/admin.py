"""Staff authoring and publication screens (OTP admin site).

Authors create DRAFT revisions only. Review and publication use the existing governance
services (author != reviewer != approver, staff MFA). Published revisions are read-only;
a correction is a new revision. Nothing here edits history or deletes anything.
"""
import re
import uuid

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F

from config.admin_site import admin_site
from practice.schema import validate_schema
from . import authoring, services
from .models import (Lesson, LessonRevision, Module, ModuleLearningRequirement, ModuleRevision,
                     Playbook, PlaybookModuleRecommendation, PlaybookRevision,
                     PracticeActivity, PracticeActivityRevision)

ALL_ROLES = tuple(services.ROLE_GROUPS)


def in_role(user, *roles):
    if not (getattr(user, 'is_active', False) and getattr(user, 'is_staff', False)):
        return False
    return user.groups.filter(name__in=[services.ROLE_GROUPS[r] for r in roles]).exists()


def revision_label(rev):
    identity = next((getattr(rev, n) for n in ('lesson', 'module', 'playbook', 'activity') if hasattr(rev, n + '_id')), None)
    return f'{getattr(identity, "slug", "?")} · rev {rev.revision_number} · {rev.title}'


class IdentityAdmin(admin.ModelAdmin):
    """Create the stable slug. Slugs and publication pointers are never edited here."""
    fields = ('slug',)
    list_display = ('slug', 'status')
    search_fields = ('slug',)
    def has_module_permission(self, request): return in_role(request.user, *ALL_ROLES)
    def has_view_permission(self, request, obj=None): return in_role(request.user, *ALL_ROLES)
    def has_add_permission(self, request): return in_role(request.user, 'author_editor')
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


class RevisionAdmin(admin.ModelAdmin):
    identity_field = None
    list_display = ('label', 'status', 'author', 'created_at')
    list_filter = ('status',)
    actions = ['start_new_draft_action', 'submit_for_review_action', 'review_action', 'publish_action']

    @admin.display(description='Revision')
    def label(self, obj): return revision_label(obj)

    def has_module_permission(self, request): return in_role(request.user, *ALL_ROLES)
    def has_view_permission(self, request, obj=None): return in_role(request.user, *ALL_ROLES)
    def has_add_permission(self, request): return in_role(request.user, 'author_editor')
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None):
        return in_role(request.user, 'author_editor') and (obj is None or (obj.status == 'draft' and obj.author_id == request.user.pk))
    def has_start_permission(self, request): return in_role(request.user, 'author_editor')
    def has_submit_permission(self, request): return in_role(request.user, 'author_editor')
    def has_review_permission(self, request): return in_role(request.user, 'reviewer')
    def has_publish_permission(self, request): return in_role(request.user, 'approver_publisher')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == self.identity_field and field is not None:
            field.label_from_instance = lambda o: o.slug
        return field

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
            last = (type(obj).objects.filter(**{self.identity_field: getattr(obj, self.identity_field)})
                    .order_by('-revision_number').first())
            obj.revision_number = (last.revision_number + 1) if last else 1
        super().save_model(request, obj, form, change)

    def _run(self, request, queryset, fn, verb):
        done = 0
        for rev in queryset:
            try:
                fn(revision=rev, actor=request.user)
                done += 1
            except ValidationError as exc:
                self.message_user(request, f'{revision_label(rev)}: {"; ".join(exc.messages)}', messages.ERROR)
            except PermissionDenied as exc:
                self.message_user(request, f'{revision_label(rev)}: {exc}', messages.ERROR)
        if done:
            self.message_user(request, f'{done} revision(s) {verb}.', messages.SUCCESS)

    @admin.action(description='Start a NEW DRAFT revision from selected (copies content)', permissions=['start'])
    def start_new_draft_action(self, request, queryset):
        self._run(request, queryset, authoring.start_revision_from, 'copied into a new draft')

    @admin.action(description='Submit selected drafts for review', permissions=['submit'])
    def submit_for_review_action(self, request, queryset):
        self._run(request, queryset, services.submit_for_review, 'submitted for review')

    @admin.action(description='Record review of selected revisions (Reviewer)', permissions=['review'])
    def review_action(self, request, queryset):
        self._run(request, queryset, services.review_revision, 'reviewed')

    @admin.action(description='Approve and PUBLISH selected revisions (Approver/Publisher)', permissions=['publish'])
    def publish_action(self, request, queryset):
        self._run(request, queryset, services.approve_and_publish, 'published')


class DraftOnlyInline(admin.TabularInline):
    extra = 0
    def _ok(self, request, obj):
        return in_role(request.user, 'author_editor') and (obj is None or (obj.status == 'draft' and obj.author_id in (None, request.user.pk)))
    def has_view_permission(self, request, obj=None): return in_role(request.user, *ALL_ROLES)
    def has_add_permission(self, request, obj=None): return self._ok(request, obj)
    def has_change_permission(self, request, obj=None): return self._ok(request, obj)
    def has_delete_permission(self, request, obj=None): return self._ok(request, obj)


# ---------------------------------------------------------------- Lessons
class LessonRevisionForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 24}),
        help_text='Plain text. One paragraph per block; separate paragraphs with a blank line.')

    class Meta:
        model = LessonRevision
        fields = ('lesson', 'title', 'summary')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        blocks = self.instance.blocks if self.instance.pk and isinstance(self.instance.blocks, list) else []
        self.fields['body'].initial = '\n\n'.join(
            b['payload']['text'] for b in sorted(blocks, key=lambda b: b['position']))
        self.order_fields(['lesson', 'title', 'summary', 'body'])

    def clean_body(self):
        body = self.cleaned_data['body']
        if not split_paragraphs(body):
            raise forms.ValidationError('Write at least one paragraph.')
        return body


def split_paragraphs(body):
    return [p.strip() for p in re.split(r'\n\s*\n', body.replace('\r\n', '\n')) if p.strip()]


def blocks_from_body(body, existing=()):
    keys = [b['key'] for b in sorted(existing, key=lambda b: b['position'])]
    return [{'key': keys[i] if i < len(keys) else str(uuid.uuid4()), 'type': 'paragraph',
             'position': i, 'payload': {'text': text}} for i, text in enumerate(split_paragraphs(body))]


class LessonRevisionAdmin(RevisionAdmin):
    form = LessonRevisionForm
    identity_field = 'lesson'
    fields = ('lesson', 'title', 'summary', 'body')
    def save_model(self, request, obj, form, change):
        obj.blocks = blocks_from_body(form.cleaned_data['body'], obj.blocks if change else [])
        super().save_model(request, obj, form, change)


# ---------------------------------------------------------------- Practice
SCHEMA_EXAMPLE = ('{"schema_version": 1, "questions": [{"id": "monthly_income", "type": "decimal_amount", '
                  '"label": "Your monthly income", "required": true, "constraints": {"currency": "KES"}}]}')


class PracticeRevisionForm(forms.ModelForm):
    class Meta:
        model = PracticeActivityRevision
        fields = ('activity', 'title', 'instructions', 'prompt', 'response_schema', 'safety_text')
        help_texts = {'response_schema': 'Strict JSON. Example: ' + SCHEMA_EXAMPLE}

    def clean_response_schema(self):
        return validate_schema(self.cleaned_data['response_schema'])


class PracticeRevisionAdmin(RevisionAdmin):
    form = PracticeRevisionForm
    identity_field = 'activity'
    fields = ('activity', 'title', 'instructions', 'prompt', 'response_schema', 'safety_text')


# ---------------------------------------------------------------- Modules
class RequirementInline(DraftOnlyInline):
    model = ModuleLearningRequirement
    fields = ('position', 'target_kind', 'lesson_revision', 'practice_revision', 'classification', 'active')
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'lesson_revision':
            kwargs['queryset'] = LessonRevision.objects.filter(status='published', lesson__current_published_revision_id=F('pk'))
        elif db_field.name == 'practice_revision':
            kwargs['queryset'] = PracticeActivityRevision.objects.filter(status='published', activity__current_published_revision_id=F('pk'))
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is not None and db_field.name in ('lesson_revision', 'practice_revision'):
            field.label_from_instance = revision_label
        return field


class ModuleRevisionAdmin(RevisionAdmin):
    identity_field = 'module'
    fields = ('module', 'title', 'description')
    inlines = [RequirementInline]


# ---------------------------------------------------------------- Playbooks
class RecommendationInline(DraftOnlyInline):
    model = PlaybookModuleRecommendation
    fields = ('position', 'module_revision', 'rationale', 'active')
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'module_revision':
            kwargs['queryset'] = ModuleRevision.objects.filter(status='published', module__current_published_revision_id=F('pk'))
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field is not None and db_field.name == 'module_revision':
            field.label_from_instance = revision_label
        return field


class PlaybookRevisionAdmin(RevisionAdmin):
    identity_field = 'playbook'
    fields = ('playbook', 'title', 'summary', 'scenario')
    inlines = [RecommendationInline]


for model in (Playbook, Module, Lesson, PracticeActivity):
    admin_site.register(model, IdentityAdmin)
admin_site.register(LessonRevision, LessonRevisionAdmin)
admin_site.register(PracticeActivityRevision, PracticeRevisionAdmin)
admin_site.register(ModuleRevision, ModuleRevisionAdmin)
admin_site.register(PlaybookRevision, PlaybookRevisionAdmin)
