

from kivy.garden.progressspinner import TextureProgressSpinner
from .widgets import Gradient


class NodeBusyMixin(object):
    def __init__(self, *args, **kwargs):
        super(NodeBusyMixin, self).__init__(*args, **kwargs)
        self._busy = False

    @property
    def busy(self):
        return self._busy

    @busy.setter
    def busy(self, value):
        self._busy = value


class BusySpinnerGuiMixin(NodeBusyMixin):
    _gui_busy_spinner_class = TextureProgressSpinner
    _gui_busy_spinner_props = {}

    def __init__(self, *args, **kwargs):
        self._gui_busy_spinner = None
        super(BusySpinnerGuiMixin, self).__init__(*args, **kwargs)

    @property
    def busy(self):
        return self._busy

    @busy.setter
    def busy(self, value):
        self._busy = value
        self._gui_update_busy()

    def _gui_update_busy(self):
        if self._busy is True:
            self._gui_busy_show()
        else:
            self._gui_busy_clear()

    def _gui_busy_show(self):
        parent = self.gui_busy_spinner.parent
        if not parent:
            self.gui_notification_stack.add_widget(self.gui_busy_spinner)

    def _gui_busy_clear(self):
        parent = self.gui_busy_spinner.parent
        if parent:
            parent.remove_widget(self.gui_busy_spinner)

    @property
    def gui_busy_spinner(self):
        if not self._gui_busy_spinner:
            props = self._gui_busy_spinner_props
            _texture = Gradient.horizontal(self._gui_color_1, self._gui_color_2)
            props['texture'] = _texture
            self._gui_busy_spinner = self._gui_busy_spinner_class(
                size_hint=(None, None), height=50, pos_hint={'left': 1},
                **self._gui_busy_spinner_props
            )
        return self._gui_busy_spinner
