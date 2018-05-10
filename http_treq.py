

import os
import treq
from functools import partial
from six.moves.urllib.parse import urlparse
from twisted.web.client import Agent
from treq.client import HTTPClient

from .basemixin import BaseMixin
from .log import NodeLoggingMixin


class HttpError(Exception):
    def __init__(self, response):
        self.response = response


class TreqHttpClientMixin(NodeLoggingMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        self._http_client = None
        super(TreqHttpClientMixin, self).__init__(*args, **kwargs)

    def http_get(self, url, callback, errback=None, **kwargs):
        deferred_response = self.http_client.get(url, **kwargs)
        deferred_response.addCallback(
            self._http_check_response
        )
        deferred_response.addCallbacks(
            callback,
            partial(self._http_error_handler, url=url, errback=errback)
        )
        return deferred_response

    def http_download(self, url, dst, callback, errback=None, **kwargs):
        dst = os.path.abspath(dst)
        if os.path.isdir(dst):
            fname = os.path.basename(urlparse(url).path)
            dst = os.path.join(dst, fname)

        if not os.path.exists(os.path.split(dst)[0]):
            os.makedirs(os.path.split(dst)[0])

        deferred_response = self.http_client.get(url, **kwargs)
        deferred_response.addCallback(self._http_check_response)
        deferred_response.addErrback(
            partial(self._http_error_handler, url=url, errback=errback)
        )

        deferred_response.addCallback(self._http_download, destination_path=dst)
        deferred_response.addErrback(self._deferred_error_passthrough)

        deferred_response.addCallback(
            partial(callback, url=url, destination=dst),
        )
        deferred_response.addErrback(self._http_error_swallow)

        return deferred_response

    def _http_download(self, response, destination_path):
        destination = open(destination_path, 'wb')
        d = treq.collect(response, destination.write)
        d.addBoth(lambda _ : destination.close())

    def _http_error_swallow(self, failure):
        failure.trap(HttpError)

    def _http_error_handler(self, failure, url=None, errback=None):
        failure.trap(HttpError)
        self.log.warn("Encountered error {e} when trying to {method} {url}",
                      e=failure.value.response.code,
                      method=failure.value.response.request.method, url=url)
        if errback:
            errback(failure)
        return failure

    @staticmethod
    def _http_check_response(response):
        if 400 < response.code < 600:
            raise HttpError(response=response)
        return response

    @property
    def http_client(self):
        if not self._http_client:
            self._http_client = HTTPClient(agent=Agent(reactor=self.reactor))
        return self._http_client

    def stop(self):
        self.log.debug("Closing HTTP client session")
        super(TreqHttpClientMixin, self).stop()


# TODO
# Treq implementation does not currently support retries.

HttpClientMixin = TreqHttpClientMixin
