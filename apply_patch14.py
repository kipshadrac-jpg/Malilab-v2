"""Applies the patch-14 edits (staff password-only sign-in, long sessions). Changes nothing if a file looks different."""
import pathlib, sys

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('.')
MARK = '# --- patch 14: staff sign in'
BLOCK = f"""
{MARK} with a password only; long-lived sessions ---------------------------------
# Set MALILAB_STAFF_OTP=1 in the environment file to ask for the authenticator code again.
STAFF_OTP_REQUIRED = os.environ.get('MALILAB_STAFF_OTP', '0') == '1'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365      # stay signed in for a year, renewed every time the site is used
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
"""


def main():
    settings = ROOT / 'config/settings.py'
    test_settings = ROOT / 'config/test_settings.py'
    for f in (settings, test_settings):
        if not f.exists():
            sys.exit(f'STOP: {f} not found')
    text = settings.read_text()
    if 'StaffWithoutOTPMiddleware' not in text:
        old = "'django_otp.middleware.OTPMiddleware',"
        if text.count(old) != 1:
            sys.exit('STOP: the OTP middleware line was not found exactly once in config/settings.py. Nothing was changed.')
        text = text.replace(old, old + " 'config.middleware.StaffWithoutOTPMiddleware',", 1)
    if MARK not in text:
        text = text.rstrip('\n') + '\n' + BLOCK
    t = test_settings.read_text()
    if 'STAFF_OTP_REQUIRED' not in t:
        t = t.rstrip('\n') + '\nSTAFF_OTP_REQUIRED = True    # the existing tests cover the code-required behaviour\n'
    settings.write_text(text)
    test_settings.write_text(t)
    print('Patch 14 edits applied.')


main()
