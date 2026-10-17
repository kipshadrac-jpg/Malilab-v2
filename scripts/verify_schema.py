"""Read-only verification of the migrated PostgreSQL Phase 6A schema."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.apps import apps
from django.db import connection
from django.db.migrations.loader import MigrationLoader

assert connection.vendor == 'postgresql'
with connection.cursor() as cursor:
    cursor.execute('SELECT current_database(), current_user, current_setting(\'server_version_num\')::int')
    db,user,version=cursor.fetchone()
assert db == 'malilab', f'Unexpected database: {db}'
assert user == 'malilab_app', f'Unexpected role: {user}'
assert version >= 140000, f'Unsupported PostgreSQL version number {version}'
with connection.cursor() as cursor:
    cursor.execute("SELECT r.rolsuper, r.rolcreatedb, r.rolcreaterole, pg_get_userbyid(d.datdba), has_database_privilege('malilab_phase6a_test', 'malilab', 'CONNECT') FROM pg_roles r CROSS JOIN pg_database d WHERE r.rolname='malilab_app' AND d.datname='malilab'")
    superuser, createdb, createrole, owner, test_role_can_connect = cursor.fetchone()
assert (superuser, createdb, createrole) == (False, False, False), 'Application role has elevated cluster privileges'
assert owner == 'malilab_app', f'Unexpected database owner: {owner}'
assert not test_role_can_connect, 'PostgreSQL test role can connect to live malilab database'
actual=set(connection.introspection.table_names())
expected={m._meta.db_table for m in apps.get_models(include_auto_created=True)} | {'django_migrations'}
missing=expected-actual
assert not missing, f'Model tables missing from PostgreSQL: {sorted(missing)}'
unexpected=actual-expected
assert not unexpected, f'Unexpected public tables: {sorted(unexpected)}'
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('accounts','content','practice','calculations','planning','learning','discovery')")
    records=cursor.fetchall()
domain_apps={'accounts','content','practice','calculations','planning','learning','discovery'}
expected_records={(app,name) for (app,name) in MigrationLoader(None).disk_migrations if app in domain_apps}
assert set(records)==expected_records, f'Phase 6A migration records differ; missing={sorted(expected_records-set(records))}, unexpected={sorted(set(records)-expected_records)}'
required={
 'accounts_useraccount': {'account_verified_time_consistent'},
 'content_modulelearningrequirement': {'requirement_target_kind_match','requirement_position_uniq','requirement_classification_valid'},
 'learning_requirementevidence': {'evidence_attempt_requirement_uniq','evidence_attempt_accepted_uniq'},
 'learning_journeystep': {'journey_step_seq_positive','journey_step_seq_uniq'},
 'planning_planrevision': {'plan_revision_uniq','plan_revision_positive'},
 'calculations_formulaversion': {'formula_version_key_uniq','formula_one_active_uniq'},
 'discovery_searchprojection': {'search_projection_target_kind_match','search_lesson_revision_uniq','search_module_revision_uniq','search_playbook_revision_uniq','search_practice_revision_uniq'},
}
for table,names in required.items():
    constraints=connection.introspection.get_constraints(connection.cursor(),table)
    absent=names-{name for name in constraints}
    assert not absent, f'{table} missing constraints: {sorted(absent)}'
indexes=connection.introspection.get_constraints(connection.cursor(),'discovery_searchprojection')
assert any('search_vector_gin_idx' in name and detail.get('type')=='gin' for name,detail in indexes.items()), 'Published search GIN index missing'
domain_models=[m for m in apps.get_models() if m._meta.app_label in {'accounts','content','practice','calculations','planning','learning','discovery'}]
for model in domain_models:
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(*) FROM {connection.ops.quote_name(model._meta.db_table)}')
        assert cursor.fetchone()[0] == 0, f'Unexpected seed/import data in {model._meta.db_table}'
print(f'Schema PASS: PostgreSQL {version}; {db}/{user}; {len(actual)} public tables exactly match models/framework/migration bookkeeping; {len(records)} Phase 6A migrations; constraints and GIN index present; no domain seed/import data.')
