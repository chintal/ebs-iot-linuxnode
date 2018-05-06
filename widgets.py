

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.properties import ListProperty


class BackgroundColorMixin(object):
    bgcolor = ListProperty([1, 1, 1, 1])

    def __init__(self, bgcolor):
        self.bgcolor = bgcolor
        self._render_bg()
        self.bind(size=self._render_bg, pos=self._render_bg)

    def _render_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bgcolor)
            Rectangle(pos=self.pos, size=self.size)


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class BleedImage(BackgroundColorMixin, Image):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Image.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)
