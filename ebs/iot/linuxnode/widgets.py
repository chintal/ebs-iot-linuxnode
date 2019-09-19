

import re
import math
from PIL import Image as PILImage
from itertools import chain
from colorthief import ColorThief

from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView

from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics import Rectangle
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty
from kivy.graphics.texture import Texture
from kivy.animation import Animation

from kivy.graphics.opengl import glGetIntegerv
from kivy.graphics.opengl import GL_MAX_TEXTURE_SIZE
_image_max_size = glGetIntegerv(GL_MAX_TEXTURE_SIZE)[0]


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


class MarqueeLabel(ScrollView):
    spacer_width = NumericProperty(None)

    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        ScrollView.__init__(self, bar_width=0)

        self._layout = ColorBoxLayout(size_hint_x=None,
                                      bgcolor=bgcolor,
                                      orientation='horizontal')
        self._mainlabels = []
        self._lspacer = Widget(size_hint_x=None, width=Window.width)
        self._rspacer = Widget(size_hint_x=None, width=Window.width)
        self.add_widget(self._layout)

        text = kwargs.pop('text')
        self._label_params = kwargs
        self.text = text

    def update_widths(self):
        width = self._lspacer.width + \
                self._rspacer.width + \
                sum([x.width for x in self._mainlabels])
        self._layout.width = width
        self.width = width

    def _set_spacer_width(self, _, size):
        self._lspacer.width = size[0]
        self._rspacer.width = size[0]
        self.update_widths()

    def on_parent(self, _, parent):
        if parent:
            parent.bind(size=self._set_spacer_width)

    @property
    def text(self):
        return ' '.join([x.text for x in self._mainlabels])

    def _set_mainlabel_width(self, l, size):
        l.width = size[0]
        self.update_widths()

    @text.setter
    def text(self, value):
        self.remove_widget(self._layout)

        texts = split_string(value, 64)
        self._layout.clear_widgets()
        self._layout.add_widget(self._lspacer)

        self._mainlabels = []
        for t in texts:
            l = Label(text=t, size_hint_x=None,
                      text_size=(None, None), **self._label_params)
            self._layout.add_widget(l)
            l.bind(texture_size=self._set_mainlabel_width)
            l.texture_update()
            self._mainlabels.append(l)

        self._layout.add_widget(self._rspacer)
        self.add_widget(self._layout)
        self.update_widths()

    def start(self, loop=True):
        speed = 75
        scroll_distance = self._layout.width - self._lspacer.width
        duration = scroll_distance / speed
        # print("Scroll was", self.scroll_x)
        self.scroll_x = 0
        # print("Using duration", duration)
        self._animation = Animation(scroll_x=1, duration=duration)
        if loop:
            self._animation.bind(on_complete=self._check_complete)
            pass
        self._animation.start(self)

    def _check_complete(self, animation, instance):
        # print(instance.scroll_x)
        # print(self._mainlabels[-1].x + self._mainlabels[-1].width)
        if instance.scroll_x > 0.95:
            # print("Repeating")
            self._animation.unbind(on_scroll=self._check_complete)
            animation.stop(self)
            self.start()

    def stop(self):
        self._animation.unbind(on_scroll=self._check_complete)
        self._animation.stop(self)
        self.clear_widgets()


class SizeProofImage(Image):
    def __init__(self, **kwargs):
        source = kwargs.get('source', None)
        if source:
            PILImage.MAX_IMAGE_PIXELS = None
            im = PILImage.open(source)
            size = im.size
            sf = max([float(s) / _image_max_size for s in size])
            if sf > 1:
                target = [int(s / sf) for s in size]
                print("Resizing image {1} to {2} {0}"
                      "".format(source, size, target))
                im = im.resize(target, PILImage.ANTIALIAS)
                im.save(source)
            im.close()
            del im
        Image.__init__(self, **kwargs)


class StandardImage(SizeProofImage):
    pass


class BleedImage(BackgroundColorMixin, SizeProofImage):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor', 'auto')
        SizeProofImage.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self)
        if bgcolor == 'auto':
            self._autoset_bg_color()
            self.bind(source=self._autoset_bg_color)
        else:
            self.bgcolor = bgcolor

    def _autoset_bg_color(self, *_):
        color = ColorThief(self.source).get_color(5)
        self.bgcolor = (x/255 for x in color)


class ImageGallery(ColorBoxLayout):
    visible = BooleanProperty(False)
    _animation_vector = (0, 1)

    def __init__(self, **kwargs):
        self.parent_layout = kwargs.pop('parent_layout')
        self.animation_layer = kwargs.pop('animation_layer', None)
        super(ImageGallery, self).__init__(bgcolor=[0, 0, 0, 1], **kwargs)
        self.bind(visible=self._set_visibility)
        self.bind(size=self._calculate_animation_distance)
        self._exit_animation = None
        self._entry_animation = None
        self._anim_distance_x = None
        self._anim_distance_y = None
        self._image = None

    def _set_visibility(self, *args):
        if self.visible:
            self.show()
        else:
            self.hide()

    def show(self):
        self.parent_layout.add_widget(self)

    def hide(self):
        self.parent_layout.remove_widget(self)
        self.animation_layer.clear_widgets()

    def _calculate_animation_distance(self, *args):
        self._anim_distance_x = (self._animation_vector[0] * self.width)
        self._anim_distance_y = (self._animation_vector[1] * self.height)
        self._entry_animation = None
        self._exit_animation = None
        self._animation_distance = math.sqrt(self._anim_distance_x ** 2 + self._anim_distance_y ** 2)

    @property
    def animation_distance(self):
        if not self._animation_distance:
            self._calculate_animation_distance()
        return self._animation_distance

    @property
    def exit_animation(self):
        if not self._exit_animation:
            def _when_done(_, instance):
                self.animation_layer.remove_widget(instance)
            self._exit_animation = Animation(y=self.pos[1] + self._anim_distance_y,
                                             x=self.pos[0] + self._anim_distance_x,
                                             t='in_out_elastic', duration=2)
            self._exit_animation.bind(on_complete=_when_done)
        return self._exit_animation

    @property
    def entry_animation(self):
        if not self._entry_animation:
            def _when_done(_, instance):
                self.animation_layer.remove_widget(instance)
                instance.size_hint = (1, 1)
                if self.parent == self.parent_layout:
                    self.add_widget(instance)
            self._entry_animation = Animation(y=self.pos[1], x=self.pos[0],
                                              t='in_out_elastic', duration=2)
            self._entry_animation.bind(on_complete=_when_done)
        return self._entry_animation

    @property
    def current(self):
        return self._image

    @current.setter
    def current(self, value):
        if value is None:
            if not self._image:
                return
            self.remove_widget(self._image)
            self._image = None
            self.visible = False
            return
        if self._image:
            pos = self._image.pos
            self.remove_widget(self._image)
            self._image.size_hint = (None, None)
            self._image.pos = pos
            self.animation_layer.add_widget(self._image)
            self.exit_animation.start(self._image)

        if isinstance(value, Image):
            self._image = value
        else:
            self._image = StandardImage(source=value, allow_stretch=True,
                                        keep_ratio=True, anim_delay=0.08)
        if not self.visible:
            self.add_widget(self._image)
            self.visible = True
            return
        self._image.size_hint = (None, None)
        self._image.size = self.size
        self._image.pos = (self.pos[0] - self._anim_distance_x,
                           self.pos[1] - self._anim_distance_y)
        self.animation_layer.add_widget(self._image)
        self.entry_animation.start(self._image)


class PDFPlayer(ImageGallery):
    _animation_vector = (-1, 0)

    def __init__(self, **kwargs):
        super(PDFPlayer, self).__init__(**kwargs)


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


def split_string(text, limit):
    words = re.split('(\W)', text)
    if max(map(len, words)) > limit:
        raise ValueError("limit is too small")
    result = []
    cpart = ''
    for word in words:
        if len(word) > limit - len(cpart):
            result.append(cpart)
            cpart = word
        else:
            cpart += word
    if cpart:
        result.append(cpart)
    return result
