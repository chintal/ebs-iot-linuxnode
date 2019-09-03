

import subprocess

from omxplayer.player import OMXPlayer
from dbus.exceptions import DBusException


class BackdropManager(object):
    def __init__(self):
        self._process = None

    def start(self, layer=None, x=None, y=None, width=None, height=None):
        cmd = ['backdrop']
        if layer:
            cmd.extend(['-l', str(layer)])
        if x:
            cmd.extend(['-x', str(int(x))])
        if y:
            cmd.extend(['-y', str(int(y))])
        if width:
            cmd.extend(['-w', str(int(width))])
        if height:
            cmd.extend(['-h', str(int(height))])
        print("Starting backdrop  : ", cmd)
        self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def set_geometry(self, x, y, width, height):
        if not self._process:
            self.start(x, y, width, height)
        geometry = "{0},{1},{2},{3}\n".format(int(x), int(y),
                                              int(width), int(height))
        self._process.stdin.write(geometry.encode())
        self._process.stdin.flush()

    def close(self):
        if self._process:
            print("Terminating Backdrop")
            self._process.stdin.write('0,0,0,0'.encode())
            self._process.stdin.flush()
            self._process.terminate()


class ExternalMediaPlayer(object):
    def __init__(self, filepath, geometry, when_done, node,
                 layer=None, loop=False, dbus_name=None):
        self._player = None
        self._pposition = None
        self._pstate = None
        self._paused = False
        self._filepath = filepath
        self._cover = None
        self._node = node
        self._loop = loop
        self._dbus_name = dbus_name
        self._geometry = geometry
        self._when_done = when_done

        if not layer:
            layer = self._node.config.video_dispmanx_layer
        self._layer = layer

        self._launch_player()

    def _exit_handler(self, player, exit_state):
        if self._cover:
            self._cover.close()
            self._cover = None
        if self._when_done and not self._paused:
            self._node.reactor.callFromThread(self._when_done)

    def _launch_player(self, paused=False):
        x, y, width, height = self._geometry
        args = [
            '--no-osd', '--aspect-mode', 'letterbox',
            '--layer', str(self._layer),
            '--win', '{0},{1},{2},{3}'.format(x, y, x + width, y + height),
        ]
        if self._loop:
            args.append('--loop')

        try:
            self._player = OMXPlayer(self._filepath, args=args, dbus_name=self._dbus_name)
            if paused:
                self._player.pause()
            self._player.exitEvent = self._exit_handler
        except SystemError as e:
            self._player = None
            self._exit_handler(None, 1)

    def force_stop(self):
        if self._player:
            self._player.stop()

    def pause(self):
        if self._player:
            self._pposition = self._player.position()
            self._pstate = self._player.playback_status()
            self._player.stop()

    def resume(self):
        self._launch_player(paused=True)
        self._player.set_position(self._pposition)
        if self._pstate == "Playing":
            self._player.play()

    def set_geometry(self, x, y, width, height):
        if self._player:
            try:
                if self._player.playback_status() in ['Playing', 'Paused']:
                    self._player.set_video_pos(x, y, x + width, y + height)
                self._geometry = (x, y, width, height)
            except DBusException:
                pass

