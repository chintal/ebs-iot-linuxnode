

from ..log import NodeLoggingMixin
from ..http import HttpClientMixin


class ModularApiEngineManagerMixin(NodeLoggingMixin, HttpClientMixin):
    def __init__(self, *args, **kwargs):
        super(ModularApiEngineManagerMixin, self).__init__(*args, **kwargs)
        self._api_engines = []

    def modapi_install(self, engine):
        self._api_engines.append(engine)

    def modapi_activate(self):
        for engine in self._api_engines:
            engine.start()

    def modapi_stop(self):
        for engine in self._api_engines:
            engine.stop()

    def start(self):
        super(ModularApiEngineManagerMixin, self).start()
        self.modapi_activate()

    def stop(self):
        self.modapi_stop()
        super(ModularApiEngineManagerMixin, self).stop()
