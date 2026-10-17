"""Create or update an editorial staff account with roles and a confirmed TOTP device.

Usage:  python manage.py create_staff author@example.com --roles author_editor
Roles:  author_editor, reviewer, approver_publisher, administrator (comma separated)
The password is prompted for (never passed on the command line). The authenticator
setup URL is printed once to YOUR terminal: add it to an authenticator app, then clear the screen.
"""
import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django_otp.plugins.otp_totp.models import TOTPDevice

from content.services import ROLE_GROUPS


class Command(BaseCommand):
    help = 'Create/update a staff account, add editorial role groups, and ensure a confirmed TOTP device.'

    def add_arguments(self, parser):
        parser.add_argument('email')
        parser.add_argument('--roles', required=True, help=','.join(ROLE_GROUPS))

    def handle(self, *args, **opts):
        roles = [r.strip() for r in opts['roles'].split(',') if r.strip()]
        unknown = [r for r in roles if r not in ROLE_GROUPS]
        if not roles or unknown:
            raise CommandError(f'Unknown or missing roles {unknown}. Valid: {", ".join(ROLE_GROUPS)}')
        User = get_user_model()
        email = User.objects.normalize_identity(opts['email'])
        user = User.objects.filter(email=email).first()
        if user is None:
            password = getpass.getpass('New password: ')
            if password != getpass.getpass('Repeat password: '):
                raise CommandError('Passwords did not match.')
            try:
                validate_password(password)
            except ValidationError as exc:
                raise CommandError('; '.join(exc.messages))
            user = User.objects.create_user(email, password, is_staff=True, email_verified=True,
                                            email_verified_at=timezone.now())
            self.stdout.write(f'Created staff account {email}')
        else:
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=['is_staff'])
            self.stdout.write(f'Updating existing account {email}')
        for role in roles:
            group, _ = Group.objects.get_or_create(name=ROLE_GROUPS[role])
            user.groups.add(group)
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device is None:
            device = TOTPDevice.objects.create(user=user, name='primary', confirmed=True)
            self.stdout.write('\nAdd this to an authenticator app (shown once):\n' + device.config_url + '\n')
        else:
            self.stdout.write('A confirmed authenticator device already exists; not shown again.')
        self.stdout.write(f'Roles now: {", ".join(sorted(g.name for g in user.groups.all()))}')
