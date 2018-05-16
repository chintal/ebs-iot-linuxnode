

import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video
from kivy.uix.image import Image

from .log import NodeLoggingMixin
from .background import OverlayWindowGuiMixin


class MediaPlayerMixin(NodeLoggingMixin):
    _media_extentions_image = ['.png', '.jpg', '.bmp']
    _media_extentions_video = []

    def __init__(self, *args, **kwargs):
        super(MediaPlayerMixin, self).__init__(*args, **kwargs)

    def media_play(self, content, duration=None, loop=False):
        # Play the media file at filepath. If loop is true, restart the media
        # when it's done. You probably would want to provide a duration with
        # an image or with a looping video, not otherwise.
        if hasattr(content, 'filepath'):
            content = content.filepath
        if duration:
            self.reactor.callLater(duration, self.media_stop)
        if os.path.splitext(content)[1] in self._media_extentions_image:
            self.log.info("Showing image {filename}",
                          filename=os.path.basename(content))
            self._media_play_image(content)
        else:
            self.log.info("Starting video {filename}",
                          filename=os.path.basename(content))
            self._media_play_video(content, loop)

    def _media_play_image(self, filepath):
        raise NotImplementedError

    def _media_play_video(self, filepath, loop=False):
        raise NotImplementedError

    def media_stop(self):
        self.log.info("Media play done")
        pass


class MediaPlayerGuiMixin(OverlayWindowGuiMixin):
    def __init__(self, *args, **kwargs):
        super(MediaPlayerGuiMixin, self).__init__(*args, **kwargs)
        self._media_playing = None
        self._gui_mediaview = None

    def _media_play_image(self, filepath):
        self._media_playing = Image(source=filepath)
        self.gui_mediaview.add_widget(self._media_playing)

    def _media_play_video(self, filepath, loop=False):
        if loop:
            eos = 'loop'
        else:
            eos = 'stop'
        self._media_playing = Video(source=filepath, state='play',
                                    eos=eos, allow_stretch=True)
        self._media_playing.opacity = 0

        def _while_playing(*_):
            self._media_playing.opacity = 1
        self._media_playing.bind(texture=_while_playing)

        def _when_done(*_):
            self.media_stop()
        self._media_playing.bind(eos=_when_done)

        self.gui_mediaview.add_widget(self._media_playing)

    def media_stop(self):
        self._media_playing.unload()
        self.gui_mediaview.clear_widgets()
        MediaPlayerMixin.media_stop(self)

    @property
    def gui_mediaview(self):
        if self._gui_mediaview is None:
            self._gui_mediaview = BoxLayout()
            self.gui_root.add_widget(self._gui_mediaview,
                                     len(self.gui_root.children) - 1)
        return self._gui_mediaview

    def gui_setup(self):
        super(MediaPlayerGuiMixin, self).gui_setup()
        _ = self.gui_mediaview
