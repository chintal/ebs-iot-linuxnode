

from twisted.internet import reactor
from .structure import BaseGuiStructureMixin


class BaseMixin(object):
    _appname = 'iotnode'

    def __init__(self, *args, **kwargs):
        self._reactor = kwargs.pop('reactor', reactor)
        super(BaseMixin, self).__init__(*args, **kwargs)

    def start(self):
        pass

    def stop(self):
        pass

    def _deferred_error_passthrough(self, failure):
        return failure

    @property
    def reactor(self):
        return self._reactor


class BaseGuiMixin(BaseGuiStructureMixin):
    _gui_color_1 = (0xff / 255, 0xff / 255, 0xff / 255)
    _gui_color_2 = (0xff / 255, 0xff / 255, 0xff / 255)

    def gui_setup(self):
        pass

    @property
    def gui_color_1(self):
        return self._gui_color_1

    @property
    def gui_color_2(self):
        return self._gui_color_2
