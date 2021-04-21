

from ..log import NodeLoggingMixin
from ..http import HttpClientMixin


class ModularApiEngineManagerMixin(HttpClientMixin, NodeLoggingMixin):
    def __init__(self, *args, **kwargs):
        self._api_engines = []
        super(ModularApiEngineManagerMixin, self).__init__(*args, **kwargs)

    def modapi_install(self, engine):
        self.log.info("Installing Modular API Engine {0}".format(engine))
        self._api_engines.append(engine)

    def modapi_activate(self):
        for engine in self._api_engines:
            self.log.info("Starting Modular API Engine {0}".format(engine))
            engine.start()

    def modapi_stop(self):
        for engine in self._api_engines:
            self.log.info("Stopping Modular API Engine {0}".format(engine))
            engine.stop()

    def start(self):
        super(ModularApiEngineManagerMixin, self).start()
        self.modapi_activate()

    def stop(self):
        self.modapi_stop()
        super(ModularApiEngineManagerMixin, self).stop()
