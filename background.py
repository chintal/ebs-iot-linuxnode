

import os
from kivy.core.window import Window
from kivy.uix.video import Video
from kivy.uix.boxlayout import BoxLayout
from six.moves.urllib.parse import urlparse

from .widgets import BleedImage
from .basemixin import BaseGuiMixin
from .config import ConfigMixin


class BackgroundGuiMixin(ConfigMixin, BaseGuiMixin):
    def __init__(self, *args, **kwargs):
        self._bg_image = None
        self._bg_video = None
        self._bg = None
        self._gui_background_color = kwargs.pop('background_color', None)
        self._bg_container = None
        super(BackgroundGuiMixin, self).__init__(*args, **kwargs)

    def background_set(self, fpath):
        if not os.path.exists(fpath):
            fpath = 'images/background.png'
        #old_bg = os.path.basename(urlparse(fpath).path)
        #if self.resource_manager.has(old_bg):
        #    self.resource_manager.remove(old_bg)
        if self.config.background != fpath:
            self.config.background = fpath
        self.gui_bg = fpath

    @property
    def gui_bg_container(self):
        if self._bg_container is None:
            self._bg_container = BoxLayout()
            self.gui_root.add_widget(self._bg_container)
        return self._bg_container

    @property
    def gui_bg_image(self):
        return self._bg_image

    @gui_bg_image.setter
    def gui_bg_image(self, value):
        if not os.path.exists(value):
            return
        if self._bg_image:
            self.gui_bg_container.remove_widget(self._bg_image)
        if self._bg_video:
            self.gui_bg_container.remove_widget(self._bg_video)
        self._bg_image = BleedImage(
            source=value,
            bgcolor=self._gui_background_color or 'auto'
        )
        self._bg = self._bg_image
        self.gui_bg_container.add_widget(self._bg_image)

    @property
    def gui_bg_video(self):
        return self._bg_video

    @gui_bg_video.setter
    def gui_bg_video(self, value):
        if not os.path.exists(value):
            return
        if self._bg_image:
            self.gui_bg_container.remove_widget(self._bg_image)
        if self._bg_video:
            self.gui_bg_container.remove_widget(self._bg_video)
        self._bg_video = Video(
            source=value, state='play',
            eos='loop', allow_stretch=True
        )

        def _when_done(*_):
            self._bg_video.state = 'play'
        self._bg_video.bind(eos=_when_done)
        self._bg = self._bg_video
        self.gui_bg_container.add_widget(self._bg_video)

    @property
    def gui_bg(self):
        return self._bg

    @gui_bg.setter
    def gui_bg(self, value):
        if not os.path.exists(value):
            self.config.background = value

        _media_extentions_image = ['.png', '.jpg', '.bmp', '.gif', '.jpeg']
        if os.path.splitext(value)[1] in _media_extentions_image:
            self.gui_bg_image = value
        else:
            self.gui_bg_video = value

    def gui_bg_pause(self):
        self.gui_root.remove_widget(self._bg_container)
        if isinstance(self.gui_bg, Video):
            self.gui_bg.state = 'pause'

    def gui_bg_resume(self):
        self.gui_root.add_widget(self._bg_container, len(self.gui_root.children))
        if isinstance(self.gui_bg, Video):
            self.gui_bg.state = 'play'

    def gui_setup(self):
        super(BackgroundGuiMixin, self).gui_setup()
        self.gui_bg = self.config.background


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
        self.gui_bg_pause()

    def _gui_overlay_mode_exit(self):
        if not self._overlay_mode:
            return
        self._overlay_mode = False
        self.gui_bg_resume()
        Window.clearcolor = [0, 0, 0, 1]

    def gui_setup(self):
        super(OverlayWindowGuiMixin, self).gui_setup()
        self.overlay_mode = self.config.overlay_mode
