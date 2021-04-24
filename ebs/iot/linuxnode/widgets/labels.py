

from kivy.uix.label import Label
from .colors import BackgroundColorMixin


class ColorLabel(BackgroundColorMixin, Label):
    def __init__(self, **kwargs):
        bgcolor = kwargs.pop('bgcolor')
        Label.__init__(self, **kwargs)
        BackgroundColorMixin.__init__(self, bgcolor=bgcolor)


# TODO This doesnt seem to work. The typical texture_size binding
#  causes this code to be useless
class SelfScalingLabel(ColorLabel):
    def __init__(self, **kwargs):
        kwargs['max_lines'] = 1
        super(SelfScalingLabel, self).__init__(**kwargs)
        self.bind(texture_size=self._scale_font)

    def _scale_font(self, *_):
        # print("Scaling {0} ?> {1}".format(self.texture_size[0], self.width))
        if self.texture_size[0] > self.width:
            self.font_size -= 1  # reduce font size if too wide
