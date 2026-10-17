"""Read-only gate: validate project migration operations before first apply."""
from io import StringIO
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.core.management import call_command
from django.db import connection
from django.db.migrations.loader import MigrationLoader

apps={'accounts','content','practice','calculations','planning','learning','discovery','otp_totp'}
allowed={'CreateModel','AddField','AddConstraint','AddIndex','AlterField','AlterUniqueTogether','AlterIndexTogether','AlterModelOptions'}
loader=MigrationLoader(None,ignore_no_migrations=True)
count=0
for (app,name), migration in sorted(loader.disk_migrations.items()):
    if app not in apps:
        continue
    unexpected=[op.__class__.__name__ for op in migration.operations if op.__class__.__name__ not in allowed]
    assert not unexpected, f'{app}.{name}: unapproved operations {unexpected}'
    output=StringIO()
    call_command('sqlmigrate',app,name,stdout=output,verbosity=0)
    sql=output.getvalue().upper()
    for forbidden in ('DROP TABLE','DROP COLUMN','DELETE FROM','UPDATE "','MALILAB_USER','MALILAB_LEGACY'):
        assert forbidden not in sql, f'{app}.{name}: forbidden SQL token {forbidden}'
    count += 1
    print(f'{app}.{name}: {len(migration.operations)} additive operations; generated SQL inspected')
print(f'Migration inspection PASS: {count} project migrations; no project data operations or destructive SQL.')
