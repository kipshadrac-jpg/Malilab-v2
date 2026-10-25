from django.conf import settings
from django.db import models


class PlanNote(models.Model):
    """A learner's private financial note: an ordered list of typed blocks (text and calculator evidence)."""
    uid = models.UUIDField(unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plan_notes')
    title = models.CharField(max_length=200, blank=True)
    blocks = models.JSONField(default=list)
    collection = models.CharField(max_length=60, blank=True)
    tags = models.JSONField(default=list)
    favourite = models.BooleanField(default=False)
    context = models.JSONField(default=dict, blank=True)
    template = models.CharField(max_length=40, blank=True)
    version = models.PositiveIntegerField(default=1)
    search_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['owner', 'updated_at'], name='plannote_owner_updated_idx')]


class PlanNoteVersion(models.Model):
    """An earlier state of a note, kept so a learner can look back and restore it."""
    note = models.ForeignKey(PlanNote, on_delete=models.CASCADE, related_name='versions')
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    blocks = models.JSONField(default=list)
    label = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['note', 'number'], name='plannoteversion_number_uniq')]
        ordering = ['-number']


class TaxRule(models.Model):
    """One version of a Kenyan tax rule or day count, with where it came from and when it applies.

    The calculators use the version in force on the date asked for. A rule's history is kept: to change a rate, add a new
    version with its own start date and source. Versions that are not active are drafts and are ignored by the calculators.
    If a rule has no active version at all, the calculators fall back to the values built into the code (rules.py).
    """
    rule_id = models.CharField(max_length=40, db_index=True)
    label = models.CharField(max_length=200)
    rate = models.DecimalField(max_digits=7, decimal_places=3, help_text='A percentage (such as 15), or a number of days for day-count rules.')
    effective_from = models.DateField(null=True, blank=True, help_text='The date this version starts to apply. Leave empty if the source does not say.')
    status = models.CharField(max_length=300, help_text='What the source says, in plain words.')
    source = models.CharField(max_length=300, help_text='The document or publication, with its date.')
    url = models.URLField(max_length=500, help_text='A link to the source.')
    retrieved = models.DateField(help_text='The date someone read the source.')
    caveat = models.TextField(blank=True, help_text='What is uncertain or what the reader should check. Shown to learners next to the rate.')
    active = models.BooleanField(default=True, help_text='Untick to keep this version as a draft. Drafts are not used by the calculators.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('rule_id', 'effective_from', 'id')

    def __str__(self):
        return '%s %s (from %s)' % (self.rule_id, self.rate.normalize(), self.effective_from or 'no start date')

    @property
    def stamp(self):
        return 'db%d-%s' % (self.pk, self.updated_at.strftime('%Y%m%d%H%M%S%f'))

    def as_version(self):
        return {
            'label': self.label, 'rate': format(self.rate.normalize(), 'f'), 'effective_from': self.effective_from, 'status': self.status,
            'source': self.source, 'url': self.url, 'retrieved': self.retrieved.isoformat(), 'caveat': self.caveat, 'stamp': self.stamp,
        }

    def copy_as_draft(self):
        """A copy to edit into the next version. It stays inactive until someone ticks Active."""
        return TaxRule.objects.create(
            rule_id=self.rule_id, label=self.label, rate=self.rate, effective_from=None, status=self.status, source=self.source,
            url=self.url, retrieved=self.retrieved, caveat=self.caveat, active=False,
        )
