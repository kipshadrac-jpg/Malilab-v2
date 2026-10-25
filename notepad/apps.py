from django.apps import AppConfig


class NotepadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notepad'

    def ready(self):
        from datetime import date
        from . import rules

        def load(rule_id):
            from .models import TaxRule
            rows = list(TaxRule.objects.filter(rule_id=rule_id, active=True))
            rows.sort(key=lambda row: (row.effective_from or date.min, row.pk))
            return [row.as_version() for row in rows]

        rules.set_loader(load)
