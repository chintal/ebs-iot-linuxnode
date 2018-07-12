

from .config import current_config

if current_config.http_client_provider == 'treq':
    from twisted.internet.error import DNSLookupError
    from twisted.internet.error import ConnectError
    from twisted.web.client import ResponseNeverReceived

    class HTTPError(Exception):
        def __init__(self, response):
            self.response = response

    _http_errors = (HTTPError, DNSLookupError,
                    ConnectError, ResponseNeverReceived)

elif current_config.http_client_provider == 'requests':
    from requests import HTTPError
    _http_errors = (HTTPError, )


def swallow_http_error(failure):
    failure.trap(*_http_errors)
    print("Swallowing HTTP Error")
