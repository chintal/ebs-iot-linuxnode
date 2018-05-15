

import os
import treq
from functools import partial
from six.moves.urllib.parse import urlparse
from twisted.web.client import Agent
from twisted.internet.defer import DeferredSemaphore
from treq.client import HTTPClient

from .basemixin import BaseMixin
from .log import NodeLoggingMixin
from .busy import NodeBusyMixin
from .http_utils import HTTPError
from twisted.internet.error import DNSLookupError
from .config import http_max_concurrent_downloads


class NoResumeResponseError(Exception):
    def __init__(self, code):
        self.code = code


class TreqHttpClientMixin(NodeBusyMixin, NodeLoggingMixin, BaseMixin):
    def __init__(self, *args, **kwargs):
        self._http_client = None
        self._http_semaphore = None
        super(TreqHttpClientMixin, self).__init__(*args, **kwargs)

    def http_get(self, url, **kwargs):
        deferred_response = self.http_semaphore.run(
            self.http_client.get, url, **kwargs
        )
        deferred_response.addCallback(self._http_check_response)
        deferred_response.addErrback(self._deferred_error_passthrough)
        deferred_response.addErrback(
            partial(self._http_error_handler, url=url)
        )
        return deferred_response

    def http_download(self, url, dst, callback=None, errback=None, **kwargs):
        deferred_response = self._http_semaphore.run(
            self._http_download, url, dst,
            callback=callback, errback=errback, **kwargs
        )
        # TODO Add an errback here which triggers a retry?
        return deferred_response

    def _http_download(self, url, dst, callback=None, errback=None, **kwargs):
        dst = os.path.abspath(dst)
        self.log.debug("Starting download {url} to {destination}",
                       url=url, destination=dst)
        if os.path.isdir(dst):
            fname = os.path.basename(urlparse(url).path)
            dst = os.path.join(dst, fname)

        if not os.path.exists(os.path.split(dst)[0]):
            os.makedirs(os.path.split(dst)[0])

        self.busy_set()

        _clear_partial_file = None
        if os.path.exists(dst + '.partial'):
            csize = os.path.getsize(dst + '.partial')
            deferred_response = self.http_client.get(
                url, headers={'Range': 'bytes={0}-'.format(csize)}, **kwargs
            )
            _clear_partial_file = dst + '.partial'
        else:
            deferred_response = self.http_client.get(url, **kwargs)

        deferred_response.addCallback(self._http_check_response)
        deferred_response.addErrback(self._deferred_error_passthrough)

        deferred_response.addCallback(
            self._http_download_response, destination_path=dst
        )
        deferred_response.addErrback(
            partial(self._http_error_handler, url=url)
        )

        if _clear_partial_file:
            # If a range request resulted in an error, get rid of the partial
            # file so it'll work the next time
            def _eb_clear_partial_file(failure):
                os.remove(_clear_partial_file)
                return failure
            deferred_response.addErrback(_eb_clear_partial_file)

        def _busy_clear(maybe_failure):
            self.busy_clear()
            return maybe_failure
        deferred_response.addBoth(_busy_clear)

        if callback:
            deferred_response.addCallback(callback, url=url, destination=dst)
        if errback:
            deferred_response.addErrback(errback)

        return deferred_response

    def _http_download_response(self, response, destination_path):
        # self.log.debug("Actual download for {destination}",
        #                destination=destination_path)
        if response.code == 206:
            # TODO Check that the range is actually correct?
            self.log.debug("Got partial content response for {dst}",
                           dst=destination_path)
            append = True
        else:
            self.log.debug("Got full content response for {dst}",
                           dst=destination_path)
            append = False
        temp_path = destination_path + '.partial'
        if not append:
            destination = open(temp_path, 'wb')
        else:
            destination = open(temp_path, 'ab')
        d = treq.collect(response, destination.write)

        # TODO Figure out what happens when the connection drops midway
        def _close_download_file(maybe_failure):
            destination.close()
            return maybe_failure
        d.addBoth(_close_download_file)

        def _finalize_successful_download(_):
            os.rename(temp_path, destination_path)
        d.addCallback(_finalize_successful_download)

        return d

    def _http_error_handler(self, failure, url=None):
        failure.trap(HTTPError, DNSLookupError)
        if isinstance(failure.value, HTTPError):
            self.log.warn(
                "Encountered error {e} while trying to {method} {url}",
                e=failure.value.response.code, url=url,
                method=failure.value.response.request.method
            )
        if isinstance(failure.value, DNSLookupError):
            self.log.warn(
                "Got a DNS lookup error for {url}. Check your URL and "
                "internet connection.", url=url
            )
        return failure

    @staticmethod
    def _http_check_response(response):
        if 400 < response.code < 600:
            raise HTTPError(response=response)
        return response

    @property
    def http_semaphore(self):
        if self._http_semaphore is None:
            n = http_max_concurrent_downloads
            self._http_semaphore = DeferredSemaphore(n)
            _ = self.http_client
        return self._http_semaphore

    @property
    def http_client(self):
        if not self._http_client:
            self.log.info("Creating treq HTTPClient")
            # Silence the twisted.web.client._HTTP11ClientFactory
            from twisted.web.client import _HTTP11ClientFactory
            _HTTP11ClientFactory.noisy = False
            agent = Agent(reactor=self.reactor)
            self._http_client = HTTPClient(agent=agent)
        return self._http_client

    def stop(self):
        self.log.debug("Closing HTTP client session")
        super(TreqHttpClientMixin, self).stop()


# TODO
# Treq implementation does not currently support retries.
# If you don't need large file / streaming download,
# use the requests provider instead.

HttpClientMixin = TreqHttpClientMixin
