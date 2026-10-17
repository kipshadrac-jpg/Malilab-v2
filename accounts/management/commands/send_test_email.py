"""Send one test email to check the SMTP settings:  python manage.py send_test_email you@example.com"""
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Send a test email using the configured email backend.'

    def add_arguments(self, parser):
        parser.add_argument('to')

    def handle(self, *args, **opts):
        self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}  via {settings.EMAIL_HOST}:{settings.EMAIL_PORT}  user={settings.EMAIL_HOST_USER or "(none)"}')
        try:
            sent = EmailMessage('MaliLab test email', 'If you can read this, MaliLab can send email.', to=[opts['to']]).send()
        except Exception as exc:  # show the real reason (bad app password, blocked port, ...)
            raise CommandError(f'Sending failed: {exc.__class__.__name__}: {exc}')
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} message to {opts["to"]}'))
