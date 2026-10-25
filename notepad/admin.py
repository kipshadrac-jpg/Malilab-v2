"""Staff screen for the Kenyan tax rules the calculators use (OTP admin site).

Every change is recorded in the admin history (who, what, when). Versions are never deleted: to change a rate, add a new version
with its start date and source, or untick Active to withdraw one. A new version made with "Copy as a draft" stays inactive until
someone has checked it and ticks Active.
"""
from datetime import date

from django import forms
from django.contrib import admin, messages

from config.admin_site import admin_site
from . import rules
from .models import TaxRule


def rule_choices():
    return [(rid, '%s (%s)' % (versions[0]['label'], rid)) for rid, versions in rules.RULES.items()]


class TaxRuleForm(forms.ModelForm):
    rule_id = forms.ChoiceField(choices=rule_choices, label='Rule')

    class Meta:
        model = TaxRule
        fields = '__all__'

    def clean(self):
        data = super().clean()
        rid, rate, url = data.get('rule_id'), data.get('rate'), data.get('url')
        if rid and rate is not None:
            if rid.endswith('_day_basis'):
                if not 1 <= rate <= 400:
                    self.add_error('rate', 'A day count must be between 1 and 400.')
            elif not 0 <= rate <= 100:
                self.add_error('rate', 'A tax rate is a percentage between 0 and 100.')
        if url and not url.startswith('https://'):
            self.add_error('url', 'Use the https:// address of the source.')
        if data.get('retrieved') and data['retrieved'] > date.today():
            self.add_error('retrieved', 'The date the source was read cannot be in the future.')
        start = data.get('effective_from')
        if rid and start:
            clash = TaxRule.objects.filter(rule_id=rid, effective_from=start, active=True).exclude(pk=self.instance.pk)
            if data.get('active') and clash.exists():
                self.add_error('effective_from', 'Another active version of this rule already starts on that date. Withdraw it first, or change the date.')
        return data


class TaxRuleAdmin(admin.ModelAdmin):
    form = TaxRuleForm
    list_display = ('rule_id', 'label', 'rate_shown', 'effective_from', 'retrieved', 'active', 'in_force')
    list_filter = ('rule_id', 'active')
    search_fields = ('label', 'source', 'caveat', 'rule_id')
    readonly_fields = ('created_at', 'updated_at', 'in_force')
    actions = ['copy_as_draft']
    fieldsets = (
        ('The rule', {'fields': ('rule_id', 'label', 'rate', 'effective_from', 'active', 'in_force')}),
        ('Where it came from', {'fields': ('status', 'source', 'url', 'retrieved', 'caveat')}),
        ('Record', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(description='Rate')
    def rate_shown(self, obj):
        return format(obj.rate.normalize(), 'f') + (' days' if obj.rule_id.endswith('_day_basis') else '%')

    @admin.display(boolean=True, description='In force today')
    def in_force(self, obj):
        if not obj.pk or not obj.active or obj.rule_id not in rules.RULES:
            return False
        return rules.rule(obj.rule_id)['stamp'] == obj.stamp

    @admin.action(description='Copy as a draft (inactive) to edit into the next version')
    def copy_as_draft(self, request, queryset):
        for row in queryset:
            row.copy_as_draft()
        self.message_user(request, 'Draft copies made. Edit the rate, start date and source, then tick Active.', messages.SUCCESS)

    def has_delete_permission(self, request, obj=None):
        return False


admin_site.register(TaxRule, TaxRuleAdmin)
