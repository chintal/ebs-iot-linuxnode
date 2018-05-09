

import os
from six.moves.configparser import ConfigParser
from appdirs import user_config_dir


config_file = os.path.join(user_config_dir('signagenode'), 'config.ini')

config = ConfigParser()
config.read(config_file)

