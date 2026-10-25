import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(unique=True)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('blocks', models.JSONField(default=list)),
                ('collection', models.CharField(blank=True, max_length=60)),
                ('tags', models.JSONField(default=list)),
                ('favourite', models.BooleanField(default=False)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('template', models.CharField(blank=True, max_length=40)),
                ('version', models.PositiveIntegerField(default=1)),
                ('search_text', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_notes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PlanNoteVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('title', models.CharField(blank=True, max_length=200)),
                ('blocks', models.JSONField(default=list)),
                ('label', models.CharField(blank=True, max_length=60)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='notepad.plannote')),
            ],
            options={
                'ordering': ['-number'],
            },
        ),
        migrations.AddIndex(
            model_name='plannote',
            index=models.Index(fields=['owner', 'updated_at'], name='plannote_owner_updated_idx'),
        ),
        migrations.AddConstraint(
            model_name='plannoteversion',
            constraint=models.UniqueConstraint(fields=('note', 'number'), name='plannoteversion_number_uniq'),
        ),
    ]
