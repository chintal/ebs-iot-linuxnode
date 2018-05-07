

from kivy.uix.floatlayout import FloatLayout
from twisted.internet import reactor

from .log import LoggingGuiMixin
from .nodeid import NodeIDGuiMixin
from .busy import BusySpinnerGuiMixin
from .background import OverlayWindowGuiMixin
from .structure import BaseGuiStructureMixin

from .log import NodeLoggingMixin
from .nodeid import NodeIDMixin
from .busy import NodeBusyMixin


class BaseIoTNode(NodeBusyMixin, NodeIDMixin, NodeLoggingMixin):
    _has_gui = False

    def __init__(self, *args, **kwargs):
        self._reactor = kwargs.pop('reactor', reactor)
        super(BaseIoTNode, self).__init__(*args, **kwargs)

    def start(self):
        self._log.info("Starting Node with ID {log_source.id}")

    def stop(self):
        self._log.info("Stopping Node with ID {log_source.id}")

    @property
    def reactor(self):
        return self._reactor


class BaseIoTNodeGui(BaseGuiStructureMixin, LoggingGuiMixin,
                     OverlayWindowGuiMixin, NodeIDGuiMixin,
                     BusySpinnerGuiMixin, BaseIoTNode):
    _gui_color_1 = (0xff / 255, 0xff / 255, 0xff / 255)
    _gui_color_2 = (0xff / 255, 0xff / 255, 0xff / 255)

    def __init__(self, *args, **kwargs):
        self._application = kwargs.pop('application')
        self._gui_root = None
        super(BaseIoTNodeGui, self).__init__(*args, **kwargs)

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
        self._gui_disable_multitouch_emulation()
        # Setup GUI elements from other Mixins
        OverlayWindowGuiMixin.gui_setup(self)
        NodeIDGuiMixin.gui_setup(self)
        LoggingGuiMixin.gui_setup(self)
        return self.gui_root

    @property
    def gui_color_1(self):
        return self._gui_color_1

    @property
    def gui_color_2(self):
        return self._gui_color_2
