

import os
from six.moves.configparser import ConfigParser
from appdirs import user_config_dir


config_file = os.path.join(user_config_dir('signagenode'), 'config.ini')

config = ConfigParser()
config.read(config_file)

# Debug

debug = config.getboolean('debug', 'debug', fallback=False)
gui_log_display = config.getboolean('debug', 'gui_log_display', fallback=False)

# Display

fullscreen = config.getboolean('display', 'fullscreen', fallback=True)
overlay_mode = config.getboolean('display', 'overlay_mode', fallback=False)

# ID

node_id_getter = config.get('id', 'getter', fallback='uuid')
node_id_interface = config.get('id', 'interface', fallback=None)

# HTTP

http_client_provider = config.get('http', 'client_provider', fallback='requests')
http_max_concurrent_downloads = config.getint('http', 'max_concurrent_download', fallback=1)

# Cache

cache_max_size = config.getint('cache', 'max_size', fallback='10000000')


class ConfigMixin(object):
    def __init__(self, *args, **kwargs):
        self._config = kwargs.pop('config')
        super(ConfigMixin, self).__init__(*args, **kwargs)

    @property
    def config(self):
        return self._config
