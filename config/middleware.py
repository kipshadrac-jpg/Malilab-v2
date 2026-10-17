from django.conf import settings


class StaffWithoutOTPMiddleware:
    """Staff who have signed in with their password count as verified, unless STAFF_OTP_REQUIRED is switched on.

    Everything that asks "is this staff member verified?" (the Studio, the admin, publishing, reviewing)
    goes through request.user.is_verified(). The sign-in itself is still checked; only the extra code is skipped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'STAFF_OTP_REQUIRED', True):
            user = request.user
            if user.is_authenticated and user.is_active and user.is_staff:
                user.is_verified = lambda: True
        return self.get_response(request)
