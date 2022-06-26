from multiprocessing import cpu_count, current_process
import commentjson as json
from map_prepare.lib import logger
from sys import exit
import shutil
import sys
import os

try:
    # Load default config
    config = json.load(open('config.json', 'r'))
except (FileNotFoundError):
    logger.warn('No config.json file found. Creating it...')
    # Support for pyinstaller
    if getattr(sys, 'frozen', False):
        default_config_path = os.path.join(sys._MEIPASS, 'map_prepare', 'default-config.json')
    else:
        default_config_path = os.path.join('map_prepare','default-config.json')

    shutil.copy(default_config_path, 'config.json')
    # Read just created config
    config = json.load(open('config.json', 'r'))

try:
    world_config = None
    world_config = list(filter(lambda x: x == f'{config["world"]}-map-prepare.json', os.listdir('.')))[0]
    # Look for config file in the world and update it with
    world_config = list(filter(lambda x: x.endswith('map-prepare.json'), os.listdir(config['world'])))[0] if world_config == None else world_config
    config['settings'] = json.load(open(world_config,'r'))
    logger.info('World contains config file, applying it...')
    # If thread count is invalid, set to # of available CPU cores
    if config['threads'] <= 0: config['threads'] = cpu_count()
# If file is not there
except (FileNotFoundError, IndexError): logger.info('Using default config')
except (ValueError, IsADirectoryError) as e:
    logger.fatal(f'File "{world_config}". Reason: "{e}". Fix or remove it and restart the script.')
    exit(0)