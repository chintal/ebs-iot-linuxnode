

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
            self._process.terminate()


class ExternalMediaPlayer(object):
    def __init__(self, filepath, geometry, when_done, node,
                 layer=None, loop=False, dbus_name=None):

        if not layer:
            layer = self._node.config.video_dispmanx_layer
        self._node = node
        x, y, width, height = geometry

        args = [
            '--no-osd', '--aspect-mode', 'letterbox', '--layer', str(layer),
            '--win', '{0},{1},{2},{3}'.format(x, y, x + width, y + height),
        ]

        if loop:
            args.append('--loop')

        def _exit_handler(player, exit_state):
            if when_done:
                self._node.reactor.callFromThread(when_done)

        try:
            if dbus_name:
                self._player = OMXPlayer(filepath, args=args, dbus_name=dbus_name)
            else:
                self._player = OMXPlayer(filepath, args=args)
            self._player.exitEvent = _exit_handler
        except SystemError as e:
            print("Got Exception")
            print(e)
            raise
            self._player = None
            _exit_handler(None, 1)

    def force_stop(self):
        if self._player:
            self._player.stop()

    def pause(self):
        if self._player:
            self._player.pause()

    def resume(self):
        if self._player:
            self._player.play()

    def set_geometry(self, x, y, width, height):
        if self._player:
            try:
                self._player.set_video_pos(x, y, x + width, y + height)
            except DBusException:
                pass
