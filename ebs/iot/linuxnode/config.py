

import os
from six.moves.configparser import ConfigParser
from appdirs import user_config_dir


class IoTNodeConfig(object):
    _config_file = os.path.join(user_config_dir('iotnode'), 'config.ini')

    def __init__(self):
        self._config = ConfigParser()
        self._config.read(self._config_file)
        self._config_apply_init()

    def _config_apply_init(self):
        self._apply_display_layer()

    def _write_config(self):
        with open(self._config_file, 'w') as configfile:
            self._config.write(configfile)

    # Platform
    @property
    def platform(self):
        return self._config.get('platform', 'platform', fallback=None)

    # Debug
    @property
    def debug(self):
        return self._config.getboolean('debug', 'debug', fallback=False)

    @property
    def gui_log_display(self):
        return self._config.getboolean('debug', 'gui_log_display', fallback=False)

    @property
    def gui_log_level(self):
        return self._config.get('debug', 'gui_log_level', fallback='info')

    # Display
    @property
    def fullscreen(self):
        return self._config.getboolean('display', 'fullscreen', fallback=True)

    @property
    def overlay_mode(self):
        return self._config.getboolean('display', 'overlay_mode', fallback=False)

    @property
    def background(self):
        return self._config.get('display', 'background', fallback='images/background.png')

    @background.setter
    def background(self, value):
        self._config.set('display', 'background', value)
        self._write_config()

    @property
    def app_dispmanx_layer(self):
        if self.platform != 'rpi':
            raise AttributeError("dispmanx layer is an RPI thing")
        return self._config.getint('display-rpi', 'dispmanx_app_layer', fallback=1)

    def _apply_display_layer(self):
        if self.platform == 'rpi':
            os.environ.setdefault('KIVY_BCM_DISPMANX_LAYER', str(self.app_dispmanx_layer))

    # ID
    @property
    def node_id_getter(self):
        return self._config.get('id', 'getter', fallback='uuid')

    @property
    def node_id_interface(self):
        return self._config.get('id', 'interface', fallback=None)

    @property
    def node_id_override(self):
        return self._config.get('id', 'override', fallback=None)

    @property
    def node_id_display(self):
        return self._config.getboolean('id', 'display', fallback=False)

    @property
    def node_id_display_frequency(self):
        return self._config.getint('id', 'display_frequency', fallback=0)

    @property
    def node_id_display_duration(self):
        return self._config.getint('id', 'display_duration', fallback=15)

    # HTTP
    @property
    def http_max_concurrent_requests(self):
        return self._config.getint('http', 'max_concurrent_requests', fallback=1)

    @property
    def http_max_background_downloads(self):
        return self._config.getint('http', 'max_background_downloads', fallback=1)

    @property
    def http_max_concurrent_downloads(self):
        return self._config.getint('http', 'max_concurrent_downloads', fallback=1)

    # Resource Manager
    @property
    def resource_prefetch_retries(self):
        return self._config.getint('resources', 'prefetch_retries', fallback=3)
    
    @property
    def resource_prefetch_retry_delay(self):
        return self._config.getint('resources', 'prefetch_retry_delay', fallback=5)

    # Cache
    @property
    def cache_max_size(self):
        return self._config.getint('cache', 'max_size', fallback='10000000')

    # Video
    @property
    def video_player(self):
        if self.platform == 'rpi':
            return self._config.get('video-rpi', 'video_player', fallback=None)

    @property
    def video_dispmanx_layer(self):
        if self.platform == 'rpi':
            return self._config.getint('video-rpi', 'dispmanx_video_layer', fallback=0)

    # Fonts
    @property
    def text_font_name(self):
        font_name = self._config.get('text', 'font_name', fallback=None)
        return font_name

    # API
    @property
    def api_url(self):
        return self._config.get('api', 'url', fallback=None)

    @property
    def api_token(self):
        return self._config.get('api', 'token', fallback=None)

    @api_token.setter
    def api_token(self, value):
        if not value:
            self._config.remove_option('api', 'token')
        else:
            self._config.set('api', 'token', value)
        self._write_config()


class ConfigMixin(object):
    def __init__(self, *args, **kwargs):
        global current_config
        self._config = current_config
        super(ConfigMixin, self).__init__(*args, **kwargs)

    @property
    def config(self):
        return self._config
