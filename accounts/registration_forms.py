from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ValidationError

from . import registration


class EmailForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'autofocus': True}),
    )


class CodeSetPasswordForm(SetPasswordForm):
    """Emailed code plus the new password, in one step."""
    field_order = ['code', 'new_password1', 'new_password2']
    code = forms.CharField(
        label='6-digit code from your email',
        max_length=20,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'one-time-code', 'autofocus': True}),
    )

    def __init__(self, user, *args, challenge=None, **kwargs):
        self.challenge = challenge
        super().__init__(user, *args, **kwargs)

    def clean_code(self):
        value = self.cleaned_data['code']
        if self.challenge is None or not registration.code_is_right(self.challenge, value):
            raise ValidationError('That code is not right or has expired.')
        return value
