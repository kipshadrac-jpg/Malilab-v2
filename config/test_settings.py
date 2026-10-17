"""In-memory backend for application behavior tests; production schema is PostgreSQL-only."""
from .settings import *
DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
STAFF_OTP_REQUIRED = True    # the existing tests cover the code-required behaviour
