

import os
import subprocess
from kivy.uix.video import Video
from omxplayer.player import OMXPlayer
from twisted.internet.defer import Deferred

from .widgets import StandardImage
from .widgets import ColorBoxLayout
from .log import NodeLoggingMixin
from .background import OverlayWindowGuiMixin


class MediaPlayerBusy(Exception):
    def __init__(self, now_playing, collision_count):
        self.now_playing = now_playing
        self.collision_count = collision_count

    def __repr__(self):
        return "<MediaPlayerBusy Now Playing {0}" \
               "".format(self.now_playing)


class BackdropManager(object):
    def __init__(self):
        self._process = None

    def start(self, layer=None, x=None, y=None, width=None, height=None):
        cmd = ['backdrop']
        if layer:
            cmd.extend(['-l', str(layer)])
        if x:
            cmd.extend(['-x', str(x)])
        if y:
            cmd.extend(['-y', str(y)])
        if width:
            cmd.extend(['-w', str(width)])
        if height:
            cmd.extend(['-h', str(height)])
        self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def set_geometry(self, x, y, width, height):
        if not self._process:
            self.start(x, y, width, height)
        self._process.stdin.write(
            "{0},{1},{2},{3}\n".format(x, y, width, height)
        )

    def close(self):
        if self._process:
            self._process.terminate()


class ExternalMediaPlayer(object):
    def __init__(self, filepath, geometry, when_done, node, loop=False):
        
        self._node = node
        x, y, width, height = geometry
        
        args = [
            '--no-osd', '--aspect-mode', 'letterbox',
            '--win', '{0},{1},{2},{3}'.format(x, y, x + width, y + height),
            '--layer', self._node.config.video_dispmanx_layer
        ]

        if loop:
            args.append('--loop')

        self._player = OMXPlayer(filepath, args=args)

        def _exit_handler(player, exit_state):
            self._node.reactor.callFromThread(when_done)

        self._player.exitEvent = _exit_handler

    def force_stop(self):
        self._player.stop()

    def set_geometry(self, x, y, width, height):
        pass


class MediaPlayerMixin(NodeLoggingMixin):
    _media_extentions_image = ['.png', '.jpg', '.bmp', '.gif', '.jpeg']
    _media_extentions_video = []

    def __init__(self, *args, **kwargs):
        super(MediaPlayerMixin, self).__init__(*args, **kwargs)
        self._media_player_deferred = None
        self._mediaplayer_now_playing = None
        self._end_call = None
        self._mediaplayer_collision_count = 0

    def media_play(self, content, duration=None, loop=False):
        # Play the media file at filepath. If loop is true, restart the media
        # when it's done. You probably would want to provide a duration with
        # an image or with a looping video, not otherwise.
        if self._mediaplayer_now_playing:
            self._mediaplayer_collision_count += 1
            if self._mediaplayer_collision_count > 30:
                self.media_stop(forced=True)
            raise MediaPlayerBusy(self._mediaplayer_now_playing,
                                  self._mediaplayer_collision_count)
        self._mediaplayer_collision_count = 0
        if hasattr(content, 'filepath'):
            content = content.filepath
        if not os.path.exists(content):
            self.log.warn("Could not find media to play at {filepath}",
                          filepath=content)
            return
        if duration:
            self._end_call = self.reactor.callLater(duration, self.media_stop)
        self.gui_bg_pause()
        if os.path.splitext(content)[1] in self._media_extentions_image:
            self.log.debug("Showing image {filename}",
                           filename=os.path.basename(content))
            self._media_play_image(content)
        else:
            self.log.debug("Starting video {filename}",
                           filename=os.path.basename(content))
            self._media_play_video(content, loop)
        self._media_player_deferred = Deferred()
        self._mediaplayer_now_playing = os.path.basename(content)
        return self._media_player_deferred

    def _media_play_image(self, filepath):
        raise NotImplementedError

    def _media_play_video(self, filepath, loop=False):
        raise NotImplementedError

    def media_stop(self, forced=False):
        self.log.info("End Offset by {0} collisions."
                      "".format(self._mediaplayer_collision_count))
        self._mediaplayer_collision_count = 0

        def _resume_bg():
            if not self._mediaplayer_now_playing:
                self.gui_bg_resume()
                self.gui_mediaview.make_transparent()
        self.reactor.callLater(1.5, _resume_bg)

        if self._end_call and self._end_call.active():
            self._end_call.cancel()

        if self._mediaplayer_now_playing:
            self._mediaplayer_now_playing = None

        if self._media_player_deferred:
            self._media_player_deferred.callback(forced)
            self._media_player_deferred = None

    def stop(self):
        self.media_stop(forced=True)
        super(MediaPlayerMixin, self).stop()


class MediaPlayerGuiMixin(OverlayWindowGuiMixin):
    def __init__(self, *args, **kwargs):
        super(MediaPlayerGuiMixin, self).__init__(*args, **kwargs)
        self._media_player_external = None
        self._media_player_backdrop = BackdropManager()
        self._media_playing = None
        self._gui_mediaview = None

    def _media_play_image(self, filepath):
        self._media_playing = StandardImage(source=filepath,
                                            allow_stretch=True,
                                            keep_ratio=True)
        self.gui_mediaview.add_widget(self._media_playing)

    def _media_play_video(self, *args, **kwargs):
        if self.config.video_external_player:
            self._media_play_video_omxplayer(*args, **kwargs)
        else:
            self._media_play_video_native(*args, **kwargs)

    def _media_play_video_native(self, filepath, loop=False):
        if loop:
            eos = 'loop'
        else:
            eos = 'stop'
        self._media_playing = Video(source=filepath, state='play',
                                    eos=eos, allow_stretch=True)
        self._media_playing.opacity = 0
        self.gui_mediaview.make_opaque()

        def _while_playing(*_):
            self._media_playing.opacity = 1
        self._media_playing.bind(texture=_while_playing)

        def _when_done(*_):
            self.media_stop()
        self._media_playing.bind(eos=_when_done)

        self.gui_mediaview.add_widget(self._media_playing)

    def _media_play_video_omxplayer(self, filepath, loop=False):
        self._media_playing = ExternalMediaPlayer(
            filepath,
            (self.gui_mediaview.x, self.gui_mediaview.y,
             self.gui_mediaview.width, self.gui_mediaview.height),
            self.media_stop, self, loop
        )

    def media_stop(self, forced=False):
        print("Stopping Media : {0}".format(self._media_playing))
        if isinstance(self._media_playing, Video):
            self._media_playing.unload()
        elif isinstance(self._media_playing, ExternalMediaPlayer):
            self._media_playing.force_stop()
            self._media_playing = None
        elif isinstance(self._media_playing, StandardImage):
            pass
        self.gui_mediaview.clear_widgets()
        MediaPlayerMixin.media_stop(self, forced=forced)

    @property
    def gui_mediaview(self):
        if self._gui_mediaview is None:
            self._gui_mediaview = ColorBoxLayout(bgcolor=(0, 0, 0, 0))
            self.gui_main_content.add_widget(self._gui_mediaview)

            if self.config.video_show_backdrop:
                self._media_player_backdrop.start(
                    self.config.video_backdrop_dispmanx_layer,
                    self.gui_mediaview.x, self.gui_mediaview.y,
                    self.gui_mediaview.width, self.gui_mediaview.height
                )

                def _backdrop_geometry(widget, _):
                    self._media_player_backdrop.set_geometry(
                        widget.x, widget.y, widget.width, widget.height
                    )
                self.gui_mediaview.bind(size=_backdrop_geometry,
                                        pos=_backdrop_geometry)
        return self._gui_mediaview

    def gui_setup(self):
        super(MediaPlayerGuiMixin, self).gui_setup()
        _ = self.gui_mediaview
