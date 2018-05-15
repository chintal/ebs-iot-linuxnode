

from .config import http_client_provider

if http_client_provider == 'treq':
    from twisted.internet.error import DNSLookupError
    class HTTPError(Exception):
        def __init__(self, response):
            self.response = response

elif http_client_provider == 'requests':
    from requests import HTTPError


def swallow_http_error(failure):
    failure.trap(HTTPError, DNSLookupError)
    print("Swallowing HTTP Error")
    print(failure)

