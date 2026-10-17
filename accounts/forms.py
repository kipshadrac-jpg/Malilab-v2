from django import forms


class SignInForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
