

from kivy.uix.floatlayout import FloatLayout
from twisted.internet import reactor

from .log import NodeLoggingMixin
from .nodeid import NodeIDMixin

from .nodeid import NodeIDGuiMixin
from .structure import BaseGuiStructureMixin
from .background import BackgroundGuiMixin


class BaseIoTNode(NodeIDMixin, NodeLoggingMixin):
    def __init__(self, *args, **kwargs):
        self._reactor = kwargs.pop('reactor', reactor)
        super(BaseIoTNode, self).__init__(*args, **kwargs)

    def start(self):
        self._log.info("Starting Node with ID {log_source.id}")

    def stop(self):
        self._log.info("Stopping Node with ID {log_source.id}")


class BaseIoTNodeGui(BackgroundGuiMixin, NodeIDGuiMixin,
                     BaseGuiStructureMixin, BaseIoTNode):
    def __init__(self, *args, **kwargs):
        self._application = kwargs.pop('application')
        self._gui_root = None
        super(BaseIoTNodeGui, self).__init__(*args, **kwargs)

    @staticmethod
    def _gui_fullscreen():
        from kivy.config import Config
        Config.set('graphics', 'fullscreen', 'auto')

    @staticmethod
    def _gui_disable_multitouch_emulation():
        from kivy.config import Config
        Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

    @property
    def gui_root(self):
        if not self._gui_root:
            self._gui_root = FloatLayout()
        return self._gui_root

    def gui_setup(self):
        # TODO Force to fullscreen in case the device happens to
        # support windowed mode
        # self._gui_fullscreen()
        self._gui_disable_multitouch_emulation()
        # Setup GUI elements from other Mixins
        NodeIDGuiMixin.gui_setup(self)
        return self.gui_root
