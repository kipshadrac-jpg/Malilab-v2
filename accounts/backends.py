from django.contrib.auth.backends import ModelBackend

class NormalizedEmailBackend(ModelBackend):
    """Authenticate the normalized email identity without exposing account existence."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if email is None or password is None:
            return None
        from .models import AccountManager
        return super().authenticate(request, username=AccountManager.normalize_identity(email), password=password, **kwargs)
