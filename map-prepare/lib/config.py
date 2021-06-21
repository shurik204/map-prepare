from jsoncomment import JsonComment
from typing import List
from . import logger
import os

# Load default config
config = JsonComment().load(open('config.json', 'r'))

try:
    world_config = None
    world_config = list(filter(lambda x: x == f'{config["world"]}-map-prepare.json', os.listdir('.')))[0]
    # Look for config file in the world and update it with
    world_config = list(filter(lambda x: x.endswith('map-prepare.json'), os.listdir(config['world'])))[0] if world_config == None else world_config
    config['settings'].update(JsonComment().load(open(world_config,'r')))
    logger.info('World contains config file, applying it...')
    # If file is not there
except (FileNotFoundError, IndexError): logger.info('Using default config')
except (ValueError, IsADirectoryError):
    logger.fatal(f'File "{world_config}" is corrupt. Fix or remove it and restart script.')
    exit(0)

# Remove all unnessesary things
del List, logger, JsonComment, os