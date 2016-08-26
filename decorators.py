import base64

from django.http import HttpResponseForbidden
from django.utils.encoding import force_str


def basic_auth(t):
    """
    checks basic auth given by the (username, password) pair
    http://francoisgaudin.com/2013/08/22/decorators-in-django/
    """
    def decorator(some_view):
        def _wrapped_view(request, *args, **kwargs):
            # the http header must exist
            if 'HTTP_AUTHORIZATION' not in request.META:
                return HttpResponseForbidden()

            # it must be basic auth
            header = request.META['HTTP_AUTHORIZATION']
            method, auth = header.split(' ', 1)
            if 'basic' != method.lower():
                return HttpResponseForbidden()

            # it must contain the right username and password
            auth = force_str(base64.b64decode(auth.strip()))
            username, password = auth.split(':', 1)
            if username != t[0] or password != t[1]:
                return HttpResponseForbidden()

            # otherwise, invoke the view
            return some_view(request, *args, **kwargs)
        return _wrapped_view
    return decorator
