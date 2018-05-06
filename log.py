

import io
from twisted import logger
from twisted.logger import textFileLogObserver
from twisted.logger import STDLibLogObserver

import logging
logging.basicConfig(level=logging.DEBUG)


class NodeLoggingMixin(object):
    _log_observers = [
        # STDLibLogObserver(),
        textFileLogObserver(io.open('runlog', 'a'))
    ]
    _log = None
    _node_log_namespace = None

    def __init__(self, *args, **kwargs):
        super(NodeLoggingMixin, self).__init__(*args, **kwargs)
        self._log = logger.Logger(namespace=self._node_log_namespace,
                                  source=self)
        self._reactor.callWhenRunning(self._start_logging)

    def _start_logging(self):
        # TODO Mention that docs don't say reactor should be running
        # TODO Mention that docs are confusing about how extract works
        # TODO Find out about a functional print to console observer
        # TODO Mention problem with IOBase vs TextIOWrapper
        # TODO log_source is not set when logger instantiated in __init__
        logger.globalLogBeginner.beginLoggingTo(self._log_observers)
