

import math

from kivy.uix.image import Image

from kivy.properties import BooleanProperty
from kivy.animation import Animation

from .colors import ColorBoxLayout
from .image import StandardImage


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
