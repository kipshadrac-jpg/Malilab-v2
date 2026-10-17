from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

User = get_user_model()

class AccountAuthenticationTests(TestCase):
    def test_email_is_normalized_and_is_login_identity(self):
        user = User.objects.create_user('  Person@Example.COM ', 'strong-password-123')
        self.assertEqual(user.email, 'person@example.com')
        self.assertEqual(user.get_username(), 'person@example.com')
        self.assertEqual(authenticate(email='PERSON@example.com', password='strong-password-123'), user)
    def test_personal_access_requires_verified_active_account(self):
        user = User.objects.create_user('reader@example.com', 'strong-password-123')
        self.assertFalse(user.can_use_personal_features)
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.can_use_personal_features)
        user.account_status = 'disabled'
        user.save()
        self.assertFalse(user.can_use_personal_features)
    def test_verification_timestamp_consistency_is_database_enforced(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(email='bad@example.com', email_verified=True)
