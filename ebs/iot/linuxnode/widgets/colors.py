

from kivy.uix.boxlayout import BoxLayout

from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.graphics import RoundedRectangle
from kivy.properties import ListProperty

from itertools import chain
from kivy.graphics.texture import Texture


def color_set_alpha(color, alpha):
    cl = list(color[:3])
    cl.append(alpha)
    return cl


class GuiPalette(object):
    def __init__(self, background, foreground, color_1, color_2):
        self.background = background
        self.foreground = foreground
        self.color_1 = color_1
        self.color_2 = color_2

    def __repr__(self):
        rv = "<{0}>".format(self.__class__.__name__)
        rv += "\n - background : {}".format(self.background)
        rv += "\n - foreground : {}".format(self.foreground)
        rv += "\n - color_1 : {}".format(self.color_1)
        rv += "\n - color_2 : {}".format(self.color_2)
        return rv


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
    _bgelement = Rectangle

    def __init__(self, bgcolor=None, **bgparams):
        self._bgparams = bgparams
        self.bgcolor = bgcolor or [1, 1, 1, 1]
        self._render_bg()
        self.bind(size=self._render_bg, pos=self._render_bg)
        self.bind(bgcolor=self._render_bg)

    def _render_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bgcolor)
            self._bgelement(pos=self.pos, size=self.size, **self._bgparams)

    def make_transparent(self):
        self.bgcolor = color_set_alpha(self.bgcolor, 0)

    def make_opaque(self):
        self.bgcolor = color_set_alpha(self.bgcolor, 1)

    def set_bgopacity(self, opacity):
        self.bgcolor = color_set_alpha(self.bgcolor, opacity)


class ColorBoxLayout(BackgroundColorMixin, BoxLayout):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        bgparams = kwargs.pop('bgparams', {})
        BoxLayout.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor, **bgparams)


class RoundedColorBoxLayout(ColorBoxLayout):
    _bgelement = RoundedRectangle

    def __init__(self, radius=None, **kwargs):
        super(RoundedColorBoxLayout, self).__init__(bgparams={'radius': radius}, **kwargs)
