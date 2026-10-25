from datetime import date

from django.db import migrations, models


def seed(apps, schema_editor):
    """Start the table with the rules that were built into the code, so nothing changes the day this is installed."""
    from notepad import rules
    TaxRule = apps.get_model('notepad', 'TaxRule')
    for rule_id, versions in rules.RULES.items():
        for v in versions:
            TaxRule.objects.create(
                rule_id=rule_id, label=v['label'], rate=v['rate'], effective_from=v['effective_from'], status=v['status'],
                source=v['source'], url=v['url'], retrieved=date.fromisoformat(v['retrieved']), caveat=v['caveat'], active=True,
            )


class Migration(migrations.Migration):

    dependencies = [('notepad', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='TaxRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_id', models.CharField(db_index=True, max_length=40)),
                ('label', models.CharField(max_length=200)),
                ('rate', models.DecimalField(decimal_places=3, help_text='A percentage (such as 15), or a number of days for day-count rules.', max_digits=7)),
                ('effective_from', models.DateField(blank=True, help_text='The date this version starts to apply. Leave empty if the source does not say.', null=True)),
                ('status', models.CharField(help_text='What the source says, in plain words.', max_length=300)),
                ('source', models.CharField(help_text='The document or publication, with its date.', max_length=300)),
                ('url', models.URLField(help_text='A link to the source.', max_length=500)),
                ('retrieved', models.DateField(help_text='The date someone read the source.')),
                ('caveat', models.TextField(blank=True, help_text='What is uncertain or what the reader should check. Shown to learners next to the rate.')),
                ('active', models.BooleanField(default=True, help_text='Untick to keep this version as a draft. Drafts are not used by the calculators.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ('rule_id', 'effective_from', 'id')},
        ),
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
