

import os
import re
from functools import partial
from six.moves.urllib.parse import urlparse

from requests import HTTPError
from requests.adapters import HTTPAdapter
from twisted.internet.task import cooperate
from txrequests import Session
from urllib3 import Retry


class HttpClientMixin(object):
    def __init__(self, *args, **kwargs):
        self._http_session = None
        super(HttpClientMixin, self).__init__(*args, **kwargs)

    def http_get(self, url, callback, errback=None, **kwargs):
        deferred_response = self.http_session.get(url, **kwargs)
        deferred_response.addCallback(self._http_check_response)
        deferred_response.addCallbacks(
            callback,
            partial(self._http_error_handler, url=url, errback=errback)
        )

    def http_download(self, url, dst, callback, errback=None, **kwargs):
        dst = os.path.abspath(dst)
        self.log.info("Starting download {url} to {destination}",
                      url=url, destination=dst)
        deferred_response = self._http_session.get(url, stream=True, **kwargs)
        deferred_response.addCallback(self._http_check_response)
        deferred_response.addCallbacks(
            partial(self._http_download, destination=dst, callback=callback),
            partial(self._http_error_handler, url=url, errback=errback)
        )

    def _http_download(self, response, destination=None, callback=None):
        def _stream_download(r, f):
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
                yield None

        def _rollback(r, f, d):
            if r:
                r.close()
            if f:
                f.close()
            if os.path.exists(d):
                os.remove(d)

        if os.path.isdir(destination):
            try:
                fname = re.findall("filename=(.+)",
                                   response.headers['content-disposition'])
            except KeyError:
                fname = os.path.basename(urlparse(response.url).path)
            destination = os.path.join(destination, fname)

        if not os.path.exists(os.path.split(destination)[0]):
            os.makedirs(os.path.split(destination)[0])

        filehandle = open(destination, 'wb')
        cooperative_dl = cooperate(_stream_download(response, filehandle))
        cooperative_dl.whenDone().addCallback(lambda _: response.close)
        cooperative_dl.whenDone().addCallback(lambda _: filehandle.close)
        cooperative_dl.whenDone().addCallback(
            partial(callback, url=response.url, destination=destination)
        )
        cooperative_dl.whenDone().addErrback(
            partial(_rollback, r=response, f=filehandle, d=destination)
        )

    def _http_error_handler(self, failure, url=None, errback=None):
        failure.trap(HTTPError)
        self.log.warn("Encountered error {e} when trying to get {url}",
                      e=failure.value.response.status_code, url=url)
        if errback:
            errback(failure)

    @staticmethod
    def _http_check_response(response):
        response.raise_for_status()
        return response

    @property
    def http_session(self):
        if not self._http_session:
            self.log.debug("Starting HTTP client session")
            r = Retry(backoff_factor=2,
                      raise_on_status=True, raise_on_redirect=True)
            self._http_session = Session()
            self._http_session.mount('http://', HTTPAdapter(max_retries=r))
            self._http_session.mount('https://', HTTPAdapter(max_retries=r))
        return self._http_session

    def stop(self):
        if self._http_session:
            self.log.debug("Closing HTTP client session")
            self._http_session.close()
