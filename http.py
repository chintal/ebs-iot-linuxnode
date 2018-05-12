

from .config import http_client_provider

if http_client_provider == 'treq':
    from .http_treq import HttpClientMixin

elif http_client_provider == 'requests':
    from .http_requests import HttpClientMixin

else:
    raise NotImplementedError


from .http_utils import swallow_http_error