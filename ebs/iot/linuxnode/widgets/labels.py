

from kivy.uix.label import Label
from .colors import BackgroundColorMixin


class WrappingLabel(Label):
    def __init__(self, **kwargs):
        super(WrappingLabel, self).__init__(**kwargs)
        self.bind(
            width=lambda *x: self.setter('text_size')(self, (self.width, None)),
            texture_size=lambda *x: self.setter('height')(self, self.texture_size[1])
        )


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor', None)
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


class SelfScalingLabel(Label):
    def __init__(self, **kwargs):
        kwargs['max_lines'] = 1
        super(SelfScalingLabel, self).__init__(**kwargs)
        self.bind(texture_size=self._scale_font)

    def _scale_font(self, *_):
        # print("Scaling {0} ?> {1}".format(self.texture_size[0], self.width))
        if self.texture_size[0] > self.width:
            self.font_size -= 1  # reduce font size if too wide


class SelfScalingColorLabel(SelfScalingLabel, ColorLabel):
    def __init__(self, **kwargs):
        super(SelfScalingColorLabel, self).__init__(**kwargs)
