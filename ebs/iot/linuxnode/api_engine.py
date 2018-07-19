

import os
from twisted.internet.task import LoopingCall
from twisted.internet.defer import succeed

from .widgets import BleedImage
from .basemixin import BaseGuiMixin
from .log import NodeLoggingMixin
from .http import HttpClientMixin
from .http import HTTPError


class BaseApiEngineMixin(NodeLoggingMixin):
    _api_probe = None
    _api_tasks = []
    _api_reconnect_frequency = 30

    def __init__(self, *args, **kwargs):
        super(BaseApiEngineMixin, self).__init__(*args, **kwargs)
        self._api_reconnect_task = None
        self._api_engine_active = False
        self._api_endpoint_connected = None

    """ API Task Management """
    @property
    def api_tasks(self):
        return self._api_tasks

    def _api_start_all_tasks(self, _):
        for task, period in self.api_tasks:
            t = getattr(self, task)
            if not t.running:
                self.log.info("Starting {task} with period {period}",
                              task=task, period=period)
                t.start(period)
        return succeed(True)

    def _api_stop_all_tasks(self, _):
        for task, _ in self._api_tasks:
            t = getattr(self, task)
            if t.running:
                self.log.info("Stopping {task}", task=task)
                t.stop()
        return succeed(True)

    """ API Connection Management """
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
            self.api_endpoint_connected = True
            self._api_engine_active = True
            if self.api_reconnect_task.running:
                self.api_reconnect_task.stop()

        def _enter_reconnection_cycle(failure):
            self.log.error("Can't connect to API endpoint")
            self.api_endpoint_connected = False
            if not self.api_reconnect_task.running:
                self.api_engine_reconnect()
            return failure

        d.addCallbacks(
            _made_connection,
            _enter_reconnection_cycle
        )

        def _error_handler(failure):
            if self.api_reconnect_task.running:
                return
            else:
                print("Returning failure ", failure)
                return failure

        d.addCallbacks(
            self._api_start_all_tasks,
            _error_handler
        )
        return d

    @property
    def api_endpoint_connected(self):
        return self._api_endpoint_connected

    @api_endpoint_connected.setter
    def api_endpoint_connected(self, value):
        self._api_endpoint_connected = value

    def api_engine_reconnect(self):
        if self._api_engine_active:
            self.api_endpoint_connected = False
            self.log.info("Lost connection to server. Attempting to reconnect.")
        self._api_engine_active = False
        if not self.api_reconnect_task.running:
            self._api_stop_all_tasks(True)
            self.api_reconnect_task.start(self._api_reconnect_frequency)

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

    def start(self):
        super(BaseApiEngineMixin, self).start()
        self.api_engine_activate()

    def stop(self):
        self.api_engine_stop()
        super(BaseApiEngineMixin, self).stop()


class HttpApiEngineMixin(BaseApiEngineMixin, HttpClientMixin):
    _api_headers = {}

    def __init__(self, *args, **kwargs):
        super(HttpApiEngineMixin, self).__init__(*args, **kwargs)
        self._api_token = None
        self._api_internet_connected = None

    def api_engine_activate(self):
        # Probe for internet
        d = self.http_get('https://www.google.com')

        def _made_connection(_):
            self.log.debug("Have Internet Connection")
            self.api_internet_connected = True

        def _enter_reconnection_cycle(failure):
            self.log.error("No Internet!")
            self.api_internet_connected = False
            if not self.api_reconnect_task.running:
                self.api_engine_reconnect()
            return failure

        d.addCallbacks(
            _made_connection,
            _enter_reconnection_cycle
        )

        def _error_handler(failure):
            if self.api_reconnect_task.running:
                return
            else:
                return failure

        d.addCallbacks(
            lambda _: BaseApiEngineMixin.api_engine_activate(self),
            _error_handler
        )
        return d

    @property
    def api_internet_connected(self):
        return self._api_internet_connected

    @api_internet_connected.setter
    def api_internet_connected(self, value):
        self._api_internet_connected = value

    @property
    def api_token(self):
        raise NotImplementedError

    def api_token_reset(self):
        raise NotImplementedError

    """ Core HTTP API Executor """
    def _api_execute(self, ep, request_builder, response_handler):
        url = "{0}/{1}".format(self.api_url, ep)
        d = self.api_token
        d.addCallback(request_builder)

        def _get_response(params):
            r = self.http_post(url, json=params, headers=self._api_headers)
            return r
        d.addCallback(_get_response)

        def _error_handler(failure):
            if isinstance(failure.value, HTTPError) and \
                    failure.value.response.code == 403:
                self.api_token_reset()
            if not self.api_reconnect_task.running:
                self.api_engine_reconnect()
            return failure
        d.addCallbacks(response_handler, _error_handler)
        return d

    @property
    def api_url(self):
        return self.config.api_url

    def start(self):
        super(HttpApiEngineMixin, self).start()

    def stop(self):
        super(HttpApiEngineMixin, self).stop()


class HttpApiEngineGuiMixin(HttpApiEngineMixin, BaseGuiMixin):
    def __init__(self, *args, **kwargs):
        super(HttpApiEngineGuiMixin, self).__init__(*args, **kwargs)
        self._api_internet_indicator = None
        self._api_connected_indicator = None
        self._api_endpoint_indicator = None

    @property
    def api_internet_connected(self):
        return self._api_internet_connected

    @api_internet_connected.setter
    def api_internet_connected(self, value):
        if not value:
            self._api_internet_indicator_show()
        else:
            self._api_internet_indicator_clear()
        self._api_internet_connected = value

    def _api_internet_indicator_show(self):
        if not self.api_internet_indicator.parent:
            self.gui_notification_row.add_widget(self.api_internet_indicator)

    def _api_internet_indicator_clear(self):
        if self.api_internet_indicator.parent:
            self.api_internet_indicator.parent.remove_widget(self.api_internet_indicator)

    @property
    def api_internet_indicator(self):
        if not self._api_internet_indicator:
            _root = os.path.abspath(os.path.dirname(__file__))
            _source = os.path.join(_root, 'images', 'no-internet.png')
            self._api_internet_indicator = BleedImage(
                source=_source, pos_hint={'left': 1},
                size_hint=(None, None), height=50, width=50,
                bgcolor=(0xff/255., 0x00/255., 0x00/255., 0.3),
            )
        return self._api_internet_indicator

    @property
    def api_endpoint_connected(self):
        return self._api_internet_connected

    @api_endpoint_connected.setter
    def api_endpoint_connected(self, value):
        if not value:
            self._api_endpoint_indicator_show()
        else:
            self._api_endpoint_indicator_clear()
        self._api_endpoint_connected = value

    def _api_endpoint_indicator_show(self):
        if not self.api_endpoint_indicator.parent:
            self.gui_notification_row.add_widget(self.api_endpoint_indicator)

    def _api_endpoint_indicator_clear(self):
        if self.api_endpoint_indicator.parent:
            self.api_endpoint_indicator.parent.remove_widget(self.api_endpoint_indicator)

    @property
    def api_endpoint_indicator(self):
        if not self._api_endpoint_indicator:
            _root = os.path.abspath(os.path.dirname(__file__))
            _source = os.path.join(_root, 'images', 'no-server.png')
            self._api_endpoint_indicator = BleedImage(
                source=_source, pos_hint={'left': 1},
                size_hint=(None, None), height=50, width=50,
                bgcolor=(0xff/255., 0x00/255., 0x00/255., 0.3),
            )
        return self._api_endpoint_indicator
