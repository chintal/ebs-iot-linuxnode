

import io
from twisted import logger
from twisted.logger import textFileLogObserver
from twisted.logger import STDLibLogObserver
from twisted.logger import formatEvent

from datetime import datetime
from collections import deque
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.effects.scroll import ScrollEffect
from kivy.utils import get_hex_from_color
from .widgets import ColorLabel

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


class LoggingGuiMixin(NodeLoggingMixin):
    def __init__(self, *args, **kwargs):
        self._gui_display_log = kwargs.pop('debug', False)
        self._gui_log = None
        self._gui_log_end = None
        self._gui_log_layout = None
        self._gui_log_scroll = None
        self._gui_log_lines = deque([], maxlen=100)
        super(LoggingGuiMixin, self).__init__(*args, **kwargs)

    def _start_logging(self):
        observers = self._log_observers
        if self._gui_display_log:
            observers += [self.gui_log_observer]
        logger.globalLogBeginner.beginLoggingTo(observers)

    @property
    def gui_log(self):
        if not self._gui_log:
            self._gui_log_scroll = ScrollView(
                size_hint=(None, None), bar_pos_y='right',
                bar_color=[1, 1, 1, 1], effect_cls=ScrollEffect,
                do_scroll_x=False, do_scroll_y=True,
                size=(Window.width * 0.3, Window.height * 0.3))

            self._gui_log_layout = BoxLayout(orientation='vertical',
                                             size_hint=(1, None))

            self._gui_log = ColorLabel(
                size_hint=(1, 1), padding=(8, 8), bgcolor=[0, 0, 0, 0.2],
                halign='left', valign='top', markup=True, font_size='12sp',
            )

            self._gui_log_end = Label(size_hint=(1, None), height=1)

            def _set_label_height(_, size):
                if size[1] > Window.height * 0.3:
                    self._gui_log.height = size[1]
                else:
                    self._gui_log.height = Window.height * 0.3
            self._gui_log.bind(texture_size=_set_label_height)

            def _set_layout_height(_, size):
                if size[1] > Window.height * 0.3:
                    self._gui_log_layout.height = size[1]
                else:
                    self._gui_log_layout.height = Window.height * 0.3
                self._gui_log_scroll.scroll_to(self._gui_log_end)
            self._gui_log.bind(texture_size=_set_layout_height)

            def _set_text_width(_, size):
                self._gui_log.text_size = size[0], None
            self._gui_log.bind(size=_set_text_width)

            self._gui_log_layout.add_widget(self._gui_log)
            self._gui_log_layout.add_widget(self._gui_log_end)
            self._gui_log_scroll.add_widget(self._gui_log_layout)
            self.gui_debug_stack.add_widget(self._gui_log_scroll)
        return self._gui_log

    def gui_log_observer(self, event):
        ll = event['log_level'].name
        msg = "[font=RobotoMono-Regular][{0:^8}][/font] {1} {2}".format(
            ll.upper(),
            datetime.fromtimestamp(event['log_time']).strftime("%d%m %H:%M:%S"),
            formatEvent(event)
        )
        color = None
        if ll == 'warn':
            color = [1, 1, 0, 1]
        elif ll == 'error':
            color = [1, 0, 0, 1]
        elif ll == 'critical':
            color = [1, 0, 0, 1]
        if color:
            color = get_hex_from_color(color)
            msg = '[color={0}]{1}[/color]'.format(color, msg)

        self._gui_log_lines.append(msg)
        self._gui_log.text = '\n'.join(self._gui_log_lines)

    def gui_setup(self):
        if not self._gui_display_log:
            return
        _ = self.gui_log
