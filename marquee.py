
from twisted.internet.defer import Deferred
from twisted.internet.defer import failure

from .widgets import color_set_alpha
from .widgets import MarqueeLabel

from .basemixin import BaseGuiMixin
from .config import ConfigMixin


class MarqueeInterrupted(Exception):
    pass


class MarqueeGuiMixin(ConfigMixin, BaseGuiMixin):
    _gui_marquee_bgcolor = None
    _gui_marquee_color = None

    def __init__(self, *args, **kwargs):
        super(MarqueeGuiMixin, self).__init__(*args, **kwargs)
        self._gui_marquee = None
        self._marquee_text = None
        self._marquee_deferred = None

    def marquee_show(self):
        self.gui_footer_show()

    def marquee_hide(self):
        self.gui_footer_hide()

    def marquee_play(self, text, duration=None, loop=True):
        if self._marquee_deferred:
            self._marquee_deferred.cancel()
        self.gui_marquee.text = text
        self.marquee_show()

        if duration:
            self._gui_marquee.start(loop=loop)
            self.reactor.callLater(duration, self.marquee_stop)
        else:
            self._gui_marquee.start(callback=self.marquee_stop)
        self._marquee_deferred = Deferred()
        return self._marquee_deferred

    def marquee_stop(self):
        self._gui_marquee.stop()
        self.marquee_hide()
        if self._marquee_deferred:
            self._marquee_deferred.callback(True)
            self._marquee_deferred = None

    @property
    def gui_marquee(self):
        if not self._gui_marquee:
            params = {'bgcolor': (self._gui_marquee_bgcolor or
                                  color_set_alpha(self.gui_color_2, 0.4)),
                      'color': [1, 1, 1, 1],
                      'font_name': 'fonts/FreeSans.ttf',
                      'font_size': '20sp'}
            self._gui_marquee = MarqueeLabel(text='Marquee Text', **params)

            self.gui_footer.add_widget(self._gui_marquee)
            self.marquee_hide()
        return self._gui_marquee

    def gui_setup(self):
        super(MarqueeGuiMixin, self).gui_setup()
        _ = self.gui_marquee