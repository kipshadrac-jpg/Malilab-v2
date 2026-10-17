from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
import django_otp.admin as otp_admin
from django_otp.admin import OTPAdminSite

_OTP_FORM = getattr(otp_admin, 'OTPAdminAuthenticationForm', None) or getattr(OTPAdminSite, 'login_form', AdminAuthenticationForm)
_OTP_TEMPLATE = getattr(OTPAdminSite, 'login_template', None)


class StaffAdminSite(OTPAdminSite):
    """The admin asks for the authenticator code only when STAFF_OTP_REQUIRED is on."""

    @property
    def login_form(self):
        return _OTP_FORM if settings.STAFF_OTP_REQUIRED else AdminAuthenticationForm

    @login_form.setter
    def login_form(self, value):
        pass

    @property
    def login_template(self):
        return _OTP_TEMPLATE if settings.STAFF_OTP_REQUIRED else None

    @login_template.setter
    def login_template(self, value):
        pass


admin_site = StaffAdminSite(name='otp_admin')
