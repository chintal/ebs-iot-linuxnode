
from twisted.internet.task import LoopingCall

from ..iotnode.http import HttpClientMixin
from ..iotnode.nodeid import NodeIDMixin


class BaseApiEngineMixin(HttpClientMixin, NodeIDMixin):
    _api_probe = None
    _api_tasks = []
    _api_headers = {}
    _api_reconnect_frequency = 30

    def __init__(self, *args, **kwargs):
        super(BaseApiEngineMixin, self).__init__(*args, **kwargs)
        self._api_reconnect_task = None
        self._api_token = None
        self._api_engine_active = False

    @property
    def api_token(self):
        raise NotImplementedError

    def api_token_reset(self):
        raise NotImplementedError

    """ Core API Executor """
    def _api_execute(self, ep, request_builder, response_handler):
        url = "{0}/{1}".format(self.api_url, ep)
        d = self.api_token
        d.addCallback(request_builder)

        def _get_response(params):
            r = self.http_post(url, json=params, headers=self._api_headers)
            return r
        d.addCallback(_get_response)

        def _error_handler(failure):
            if failure.value.response.code == 403:
                self.api_token_reset()
            if not self.api_reconnect_task.running:
                self.api_engine_reconnect()
            return failure
        d.addCallbacks(response_handler, _error_handler)
        return d

    """ API Connection Management """
    @property
    def api_tasks(self):
        return self._api_tasks

    @property
    def api_reconnect_task(self):
        if self._api_reconnect_task is None:
            self._api_reconnect_task = LoopingCall(self.api_engine_activate)
        return self._api_reconnect_task

    def api_engine_activate(self):
        self.log.debug("Attempting to activate API engine.")

        d = getattr(self, self._api_probe)()

        def _made_connection(_):
            self.log.debug("Made connection")
            self._api_engine_active = True
            if self.api_reconnect_task.running:
                self.api_reconnect_task.stop()
        d.addCallbacks(
            _made_connection,
            self._deferred_error_passthrough
        )

        for task, period in self.api_tasks:
            d.addCallbacks(
                lambda _: getattr(self, task).start(period),
                self._deferred_error_passthrough
            )

        d.addErrback(self._deferred_error_swallow)
        return d

    def api_engine_reconnect(self):
        if self._api_engine_active:
            self.log.info("Lost connection to server. Attempting to reconnect.")
        self._api_engine_active = False
        if not self.api_reconnect_task.running:
            self.api_reconnect_task.start(self._api_reconnect_frequency)
        for task, _ in self._api_tasks:
            if getattr(self, task).running:
                getattr(self, task).stop()

    def api_engine_stop(self):
        self._api_engine_active = False
        for task, _ in self._api_tasks:
            if getattr(self, task).running:
                getattr(self, task).stop()
        if self.api_reconnect_task.running:
            self.api_reconnect_task.stop()

    @property
    def api_engine_active(self):
        return self._api_engine_active

    @property
    def api_url(self):
        return self.config.api_url

    def start(self):
        super(BaseApiEngineMixin, self).start()
        self.api_engine_activate()

    def stop(self):
        self.api_engine_stop()
        super(BaseApiEngineMixin, self).stop()
