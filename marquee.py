
from twisted.internet.defer import Deferred

from .widgets import ColorLabel
from .widgets import color_set_alpha

from .basemixin import BaseGuiMixin
from .config import ConfigMixin


class MarqueeGuiMixin(ConfigMixin, BaseGuiMixin):
    _gui_marquee_bgcolor = None
    _gui_marquee_color = None

    def __init__(self, *args, **kwargs):
        super(MarqueeGuiMixin, self).__init__(*args, **kwargs)
        self._gui_marquee = None
        self._marquee_text = None
        self._marquee_loop = False
        self._marquee_deferred = None

    @property
    def marquee_text(self):
        return self._gui_marquee.text

    @marquee_text.setter
    def marquee_text(self, value):
        self.gui_marquee.text = value

    def marquee_show(self):
        self.gui_footer_show()

    def marquee_hide(self):
        self.gui_footer_hide()

    def marquee_play(self, text, duration=None, loop=False):
        self.marquee_text = text
        self._marquee_loop = loop
        self.marquee_start()
        if duration:
            self.reactor.callLater(duration, self.marquee_stop)
        self._marquee_deferred = Deferred()
        return self._marquee_deferred

    def marquee_start(self):
        self.marquee_show()

    def marquee_stop(self):
        self.marquee_hide()
        if self._marquee_deferred:
            self._marquee_deferred.callback(True)

    @property
    def gui_marquee(self):
        if not self._gui_marquee:
            params = {'bgcolor': (self._gui_marquee_bgcolor or
                                  color_set_alpha(self.gui_color_2, 0.4)),
                      'color': [1, 1, 1, 1]}
            self._gui_marquee = ColorLabel(
                text="Lorem Ipsum", size_hint=(1, 1), font_size='20sp',
                valign='middle', halign='center', **params
            )
            self.gui_footer.add_widget(self._gui_marquee)
        return self._gui_marquee

    def gui_setup(self):
        super(MarqueeGuiMixin, self).gui_setup()
        _ = self.gui_marquee
