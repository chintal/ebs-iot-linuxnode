

import os
from appdirs import user_cache_dir
from twisted.internet import reactor
from .structure import BaseGuiStructureMixin


class BaseMixin(object):
    _appname = 'iotnode'

    def __init__(self, *args, **kwargs):
        self._reactor = kwargs.pop('reactor', reactor)
        self._cache_dir = None
        self._db_dir = None
        super(BaseMixin, self).__init__(*args, **kwargs)

    def start(self):
        pass

    def stop(self):
        pass

    def _deferred_error_passthrough(self, failure):
        return failure

    def _deferred_error_swallow(self, failure):
        return

    @property
    def reactor(self):
        return self._reactor

    @property
    def appname(self):
        return self._appname

    @property
    def cache_dir(self):
        if not self._cache_dir:
            self._cache_dir = user_cache_dir(self.appname)
            os.makedirs(self._cache_dir, exist_ok=True)
        return self._cache_dir

    @property
    def db_dir(self):
        if not self._db_dir:
            self._db_dir = os.path.join(self.cache_dir, 'db')
            os.makedirs(self._db_dir, exist_ok=True)
        return self._db_dir


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
