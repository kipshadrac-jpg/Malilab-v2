from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

class AccountManager(BaseUserManager):
    use_in_migrations = True
    @staticmethod
    def normalize_identity(email):
        return BaseUserManager.normalize_email(email).strip().casefold()
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_identity(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True or extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusers must have staff and superuser privileges')
        return self.create_user(email, password, **extra_fields)

class UserAccount(AbstractUser):
    username = None
    email = models.EmailField(max_length=254, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    account_status = models.CharField(max_length=16, default='active', choices=[('active','Active'),('disabled','Disabled'),('closed','Closed')])
    closed_at = models.DateTimeField(null=True, blank=True)
    objects = AccountManager()
    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(email_verified=False, email_verified_at__isnull=True) | models.Q(email_verified=True, email_verified_at__isnull=False)), name='account_verified_time_consistent')]
        indexes = [models.Index(fields=['account_status','date_joined'], name='account_status_joined_idx')]
    def save(self, *args, **kwargs):
        if self.email:
            self.email = AccountManager.normalize_identity(self.email)
        super().save(*args, **kwargs)
    @property
    def can_use_personal_features(self):
        return self.is_authenticated and self.is_active and self.account_status == 'active' and self.email_verified
