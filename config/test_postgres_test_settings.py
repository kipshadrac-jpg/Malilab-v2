import os
import subprocess
import sys
from django.test import SimpleTestCase


class PostgreSQLTestSettingsSafetyTests(SimpleTestCase):
    def _load(self, overrides):
        env = os.environ.copy()
        for key in ('MALILAB_TEST_DB_NAME', 'MALILAB_TEST_DATABASE', 'MALILAB_TEST_DB_USER', 'MALILAB_DB_NAME', 'MALILAB_DB_USER'):
            env.pop(key, None)
        env.update(overrides)
        return subprocess.run(
            [sys.executable, '-c', 'import config.postgres_test_settings as s; print(s.DATABASES["default"]["NAME"], s.DATABASES["default"]["USER"], s.DATABASES["default"]["TEST"]["NAME"])'],
            env=env, text=True, capture_output=True,
        )

    def test_safe_configuration_uses_separate_database_and_role(self):
        result = self._load({})
        self.assertEqual(result.returncode, 0, result.stderr)
        db, role, test_db = result.stdout.split()
        self.assertNotEqual(db, 'malilab')
        self.assertNotEqual(test_db, 'malilab')
        self.assertNotEqual(role, 'malilab_app')

    def test_live_database_names_are_rejected_for_both_overrides(self):
        for name in ('MALILAB_TEST_DB_NAME', 'MALILAB_TEST_DATABASE'):
            with self.subTest(name=name):
                result = self._load({name: 'malilab'})
                self.assertNotEqual(result.returncode, 0)

    def test_application_role_is_rejected(self):
        result = self._load({'MALILAB_TEST_DB_USER': 'malilab_app'})
        self.assertNotEqual(result.returncode, 0)

    def test_override_cannot_make_test_target_follow_live_database(self):
        result = self._load({'MALILAB_DB_NAME': 'safe_test_name', 'MALILAB_TEST_DATABASE': 'safe_test_name'})
        self.assertNotEqual(result.returncode, 0)
