

from itertools import chain
from colorthief import ColorThief
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.properties import ListProperty
from kivy.graphics.texture import Texture


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


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class BleedImage(BackgroundColorMixin, Image):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor', 'auto')
        Image.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self)
        if bgcolor == 'auto':
            self._autoset_bg_color()
            self.bind(source=self._autoset_bg_color)
        else:
            self.bgcolor = bgcolor

    def _autoset_bg_color(self, *_):
        color = ColorThief(self.source).get_color(5)
        self.bgcolor = (x/255 for x in color)


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


def color_set_alpha(color, alpha):
    cl = list(color[:3])
    cl.append(alpha)
    return cl
