from functools import wraps
from django.utils.cache import add_never_cache_headers

def no_cache(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        add_never_cache_headers(response)
        return response
    return _wrapped