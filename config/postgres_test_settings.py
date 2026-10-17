"""PostgreSQL integration settings that cannot target the live development DB."""
import os
from django.core.exceptions import ImproperlyConfigured
from .settings import *

_development_database = os.environ.get('MALILAB_DB_NAME', 'malilab')
_development_role = os.environ.get('MALILAB_DB_USER', 'malilab_app')
_test_role = os.environ.get('MALILAB_TEST_DB_USER', 'malilab_phase6a_test')
_test_db_name = os.environ.get('MALILAB_TEST_DB_NAME', 'malilab_phase6a_test')
_test_database = os.environ.get('MALILAB_TEST_DATABASE', 'test_malilab_phase6a')

if any(name == 'malilab' or name == _development_database for name in (_test_db_name, _test_database)):
    raise ImproperlyConfigured('PostgreSQL test databases must never be malilab or the configured development database.')
if _test_role == 'malilab_app' or _test_role == _development_role:
    raise ImproperlyConfigured('PostgreSQL tests must use a role distinct from malilab_app and the development role.')

DATABASES['default']['USER'] = _test_role
DATABASES['default']['NAME'] = _test_db_name
DATABASES['default']['TEST'] = {'NAME': _test_database}
