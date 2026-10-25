import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0008_phase6a_remediation_round3'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entitlement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trial_started_at', models.DateTimeField()),
                ('all_modules_at', models.DateTimeField(blank=True, help_text='Set when the all-modules pass was bought or granted. Clear it to take the pass away.', null=True)),
                ('note', models.CharField(blank=True, help_text='Why this was changed by hand, if it was.', max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='entitlement', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(default='mpesa', max_length=16)),
                ('product', models.CharField(choices=[('module', 'One module'), ('all', 'All modules')], max_length=8)),
                ('amount', models.PositiveIntegerField()),
                ('phone', models.CharField(blank=True, max_length=15)),
                ('status', models.CharField(choices=[('pending', 'Waiting for the phone'), ('paid', 'Paid'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('review', 'Needs a look')], db_index=True, default='pending', max_length=10)),
                ('merchant_request_id', models.CharField(blank=True, max_length=64)),
                ('checkout_request_id', models.CharField(blank=True, db_index=True, max_length=64)),
                ('customer_message', models.CharField(blank=True, max_length=300)),
                ('result_code', models.CharField(blank=True, max_length=16)),
                ('result_desc', models.CharField(blank=True, max_length=300)),
                ('receipt', models.CharField(blank=True, db_index=True, max_length=40)),
                ('callback', models.JSONField(blank=True, null=True)),
                ('sandbox', models.BooleanField(default=False)),
                ('last_checked', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('module', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='content.module')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-created_at',)},
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['user', 'status'], name='payment_user_status_idx'),
        ),
        migrations.CreateModel(
            name='ModuleUnlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('payment', 'Payment'), ('grant', 'Given by staff')], default='payment', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='unlocks', to='content.module')),
                ('payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='unlocks', to='billing.payment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_unlocks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='moduleunlock',
            constraint=models.UniqueConstraint(fields=('user', 'module'), name='unlock_user_module_uniq'),
        ),
    ]
