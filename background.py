

from .widgets import BleedImage


class BackgroundGuiMixin(object):
    _gui_background_color = [0, 1, 0, 0.25]
    _gui_background_source = 'images/background.png'

    def __init__(self, *args, **kwargs):
        super(BackgroundGuiMixin, self).__init__(*args, **kwargs)
        bg_image = BleedImage(source=self._gui_background_source,
                              bgcolor=self._gui_background_color)
        self.gui_root.add_widget(bg_image)
