from functools import wraps

from django.utils.cache import add_never_cache_headers, patch_vary_headers


def private_for_signed_in(view):
    """Pages show the signed-in email in the header: never let a shared cache keep them for a signed-in user."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        patch_vary_headers(response, ('Cookie',))
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
    return wrapped
