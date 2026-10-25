"""Check the M-Pesa settings: lists anything missing, then asks Safaricom for an access token."""
from django.core.management.base import BaseCommand

from billing import daraja


class Command(BaseCommand):
    help = 'Check the M-Pesa (Daraja) settings and sign in to Safaricom.'

    def handle(self, *args, **options):
        self.stdout.write('Environment: %s' % ('sandbox' if daraja.sandbox() else 'PRODUCTION'))
        gaps = daraja.missing()
        if gaps:
            self.stdout.write(self.style.ERROR('Missing in the environment file: ' + ', '.join(gaps)))
            return
        try:
            daraja.access_token()
        except daraja.DarajaError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
            return
        self.stdout.write(self.style.SUCCESS('Signed in to Safaricom. Callback address: ' + daraja.callback_url().rsplit('/', 2)[0] + '/<secret>/'))
