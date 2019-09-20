

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.properties import ListProperty

from itertools import chain
from kivy.graphics.texture import Texture


def color_set_alpha(color, alpha):
    cl = list(color[:3])
    cl.append(alpha)
    return cl


class Gradient(object):

    @staticmethod
    def horizontal(*args):
        texture = Texture.create(size=(len(args), 1), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(*args):
        texture = Texture.create(size=(1, len(args)), colorfmt='rgba')
        buf = bytes([int(v * 255) for v in chain(*args)])  # flattens
        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture


class BackgroundColorMixin(object):
    bgcolor = ListProperty([1, 1, 1, 1])

    def __init__(self, bgcolor=None):
        self.bgcolor = bgcolor or [1, 1, 1, 1]
        self._render_bg()
        self.bind(size=self._render_bg, pos=self._render_bg)
        self.bind(bgcolor=self._render_bg)

    def _render_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bgcolor)
            Rectangle(pos=self.pos, size=self.size)

    def make_transparent(self):
        self.bgcolor = color_set_alpha(self.bgcolor, 0)

    def make_opaque(self):
        self.bgcolor = color_set_alpha(self.bgcolor, 1)


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class ColorBoxLayout(BackgroundColorMixin, BoxLayout):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        BoxLayout.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)
