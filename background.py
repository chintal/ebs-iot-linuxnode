

from kivy.core.window import Window
from .widgets import BleedImage
from .basemixin import BaseGuiMixin
from .config import ConfigMixin


class BackgroundGuiMixin(ConfigMixin, BaseGuiMixin):
    _gui_background_color = [0, 1, 0, 0.25]
    _gui_background_source = 'images/background.png'

    def __init__(self, *args, **kwargs):
        self._bg_image = None
        super(BackgroundGuiMixin, self).__init__(*args, **kwargs)

    @property
    def gui_bg_image(self):
        if self._bg_image is None:
            self._bg_image = BleedImage(source=self._gui_background_source,
                                        bgcolor=self._gui_background_color)
            self.gui_root.add_widget(self._bg_image)
        return self._bg_image

    def gui_setup(self):
        super(BackgroundGuiMixin, self).gui_setup()
        _ = self.gui_bg_image


class OverlayWindowGuiMixin(BackgroundGuiMixin):
    # Overlay mode needs specific host support.
    # RPi :
    #   See DISPMANX layers and
    #   http://codedesigner.de/articles/omxplayer-kivy-overlay/index.html
    # Normal Linux Host :
    #   See core-x11 branch and
    #   https://groups.google.com/forum/#!topic/kivy-users/R4aJCph_7IQ
    # Others :
    #   Unknown, see
    #   - https://github.com/kivy/kivy/issues/4307
    #   - https://github.com/kivy/kivy/pull/5252
    _gui_supports_overlay_mode = False

    def __init__(self, *args, **kwargs):
        self._overlay_mode = None
        super(OverlayWindowGuiMixin, self).__init__(*args, **kwargs)

    @property
    def overlay_mode(self):
        return self._overlay_mode

    @overlay_mode.setter
    def overlay_mode(self, value):
        if not self._gui_supports_overlay_mode:
            self.log.warn("Application tried to change overlay mode, "
                          "not supported this platform.")
            return
        if value is True:
            self._gui_overlay_mode_enter()
        else:
            self._gui_overlay_mode_exit()

    def _gui_overlay_mode_enter(self):
        if self._overlay_mode:
            return
        self._overlay_mode = True
        Window.clearcolor = [0, 0, 0, 0]
        self.gui_root.remove_widget(self._bg_image)

    def _gui_overlay_mode_exit(self):
        if not self._overlay_mode:
            return
        self._overlay_mode = False
        self.gui_root.add_widget(self._bg_image, len(self.gui_root.children))
        Window.clearcolor = [0, 0, 0, 1]

    def gui_setup(self):
        super(OverlayWindowGuiMixin, self).gui_setup()
        self.overlay_mode = self.config.overlay_mode
