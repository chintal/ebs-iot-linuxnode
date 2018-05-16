

from .config import http_client_provider

if http_client_provider == 'treq':
    from twisted.internet.error import DNSLookupError

    class HTTPError(Exception):
        def __init__(self, response):
            self.response = response

    _http_errors = (HTTPError, DNSLookupError)

elif http_client_provider == 'requests':
    from requests import HTTPError
    _http_errors = (HTTPError, )


def swallow_http_error(failure):
    failure.trap(*_http_errors)
    print("Swallowing HTTP Error")
    # print(failure)
