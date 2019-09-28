

# foundation    ()
# backdrop      1
# background    2
# backdrop      3
# video         4
# app           5


import os
import atexit
import shutil
import tempfile
from six.moves.configparser import ConfigParser
from appdirs import user_config_dir


class IoTNodeConfig(object):
    _config_file = os.path.join(user_config_dir('iotnode'), 'config.ini')
    _sys_config_file = os.path.join('/etc/raspap/custom.ini')

    def __init__(self):
        self._config = ConfigParser()
        self._config.read(self._config_file)
        self._sys_config = ConfigParser()
        self._sys_config.read(self._sys_config_file)
        self._config_apply_init()
        self._temp_dir = None

    def _config_apply_init(self):
        self._apply_display_layer()

    def _write_config(self):
        with open(self._config_file, 'w') as configfile:
            self._config.write(configfile)

    @property
    def temp_dir(self):
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp()
            atexit.register(shutil.rmtree, self._temp_dir)
        return self._temp_dir

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
    def sidebar_width(self):
        return self._config.getfloat('display', 'sidebar_width', fallback=0.3)

    @property
    def show_foundation(self):
        return self._config.getboolean('display-rpi', 'show_foundation', fallback=True)

    @property
    def dispmanx_foundation_layer(self):
        return self._config.getint('display-rpi', 'dispmanx_foundation_layer', fallback=1)

    @property
    def foundation_image(self):
        return self._config.get('display-rpi', 'foundation_image', fallback=None)

    @property
    def background(self):
        return self._config.get('display', 'background', fallback='images/background.png')

    @background.setter
    def background(self, value):
        self._config.set('display', 'background', value)
        self._write_config()

    @property
    def background_external_player(self):
        if self.platform == 'rpi':
            return self._config.getboolean('display-rpi', 'background_external_player', fallback=False)

    @property
    def background_dispmanx_layer(self):
        return self._config.getint('display-rpi', 'background_dispmanx_layer', fallback=2)

    @property
    def app_dispmanx_layer(self):
        if self.platform != 'rpi':
            raise AttributeError("dispmanx layer is an RPI thing")
        return self._config.getint('display-rpi', 'dispmanx_app_layer', fallback=5)

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

    @property
    def http_proxy_host(self):
        return self._sys_config.get('NetworkProxyConfiguration', 'host', fallback=None)

    @property
    def http_proxy_port(self):
        return self._sys_config.getint('NetworkProxyConfiguration', 'port', fallback=0)

    @property
    def http_proxy_user(self):
        return self._sys_config.get('NetworkProxyConfiguration', 'user', fallback=None)

    @property
    def http_proxy_pass(self):
        return self._sys_config.get('NetworkProxyConfiguration', 'pass', fallback=None)

    @property
    def http_proxy_enabled(self):
        return self.http_proxy_host is not None

    @property
    def http_proxy_auth(self):
        if not self.http_proxy_user:
            return None
        if not self.http_proxy_pass:
            return self.http_proxy_user
        return "{0}:{1}".format(self.http_proxy_user, self.http_proxy_pass)

    @property
    def http_proxy_url(self):
        url = self.http_proxy_host
        if self.http_proxy_port:
            url = "{0}:{1}".format(url, self.http_proxy_port)
        if self.http_proxy_auth:
            url = "{0}@{1}".format(self.http_proxy_auth, url)
        return url

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
    def video_external_player(self):
        if self.platform == 'rpi':
            return self._config.getboolean('video-rpi', 'external_player', fallback=False)

    @property
    def video_dispmanx_layer(self):
        if self.platform == 'rpi':
            return self._config.getint('video-rpi', 'dispmanx_video_layer', fallback=4)

    @property
    def video_show_backdrop(self):
        if self.platform == 'rpi':
            return self._config.getboolean('video-rpi', 'show_backdrop', fallback=False)

    @property
    def video_backdrop_dispmanx_layer(self):
        if self.platform == 'rpi':
            return self._config.getint('video-rpi', 'dispmanx_video_layer', fallback=1)

    # Browser
    @property
    def browser_show_default(self):
        return self._config.getboolean('browser', 'show_default', fallback=False)

    @browser_show_default.setter
    def browser_show_default(self, value):
        if value:
            value = 'yes'
        else:
            value = 'no'
        self._config.set('browser', 'show_default', value)
        self._write_config()

    @property
    def browser_default_url(self):
        return self._config.get('browser', 'default_url', fallback='http://www.google.com')

    @browser_default_url.setter
    def browser_default_url(self, value):
        self._config.set('browser', 'default_url', value)
        self._write_config()

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
