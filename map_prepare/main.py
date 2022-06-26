# Logger first
from map_prepare.lib import logger, nbt_utils, cache
from map_prepare.lib.config import config, world_config
from sys import argv, exit
from nbt import nbt
import multiprocessing
import importlib
import zipfile
import shutil
import time
import sys
import os

if sys.platform.startswith('win'):
    # On Windows calling this function is necessary.
    multiprocessing.freeze_support()

##########
# DEBUG
# if not ('map-prepare.json' in os.listdir(config['world'])):
#     shutil.rmtree(config['world'], ignore_errors=True)
#     shutil.unpack_archive('world.zip')
############
if argv.count('--debug'): 
    logger.info('Forcefully enabled debug output. Spam incoming...')
    config['debug'] = True

if argv.count('--use-spawn'): 
    logger.info('Using start method "spawn" for multiprocessing')
    multiprocessing.set_start_method('spawn')

if argv.count('--extract-world'):
    if zipfile.is_zipfile('./world.zip'):
        logger.info('Extracting test world')
        try: shutil.rmtree('./world')
        except FileNotFoundError: pass
        zipfile.ZipFile('./world.zip').extractall()
    else: 
        logger.info('Test world must be a valid archive named "world.zip"')

if argv.count('--directory'):
    i = argv.index('--directory')
    try:
        work_dir = argv[i + 1]
        os.chdir(work_dir)
    except IndexError: 
        logger.error('No argument supplied for "--directory"')
        exit(6)
    except FileNotFoundError:
        logger.error('Provided directory doesn\'t exist')
        exit(7)


if argv.count('--one-thread'): 
    logger.info('Using one thread')
    config['threads'] = 1

if config['debug'] == True: logger.app_log.setLevel(logger.logging.DEBUG)

if not (config['world'] in os.listdir('.')):
    logger.fatal(f'Can\'t find folder "{config["world"]}"')
    exit(4)

if world_config == None:
    logger.info('No configuration file found in the current directory for this world. Creating it...')

    # Support for pyinstaller
    if getattr(sys, 'frozen', False):
        default_settings = os.path.join(sys._MEIPASS, 'map_prepare/global-settings.json')
    else:
        default_settings = f'{__file__[:-8]}/global-settings.json'

    shutil.copy(default_settings, f'{config["world"]}-map-prepare.json')
    logger.info(f'Review settings in "{config["world"]}-map-prepare.json" and launch this program again.')
    exit(0)

version_name = config['settings']['version']
if version_name == '':
    level_dat = nbt.NBTFile(filename=f'{config["world"]}/level.dat')
    version_name = str(nbt_utils.get_property(nbt_utils.get_property(nbt_utils.get_property(level_dat, 'Data'), 'Version'), 'Name').value)
    # :(
    version_name = version_name.replace(' Release Candidate ', '-rc')
    version_name = version_name.replace(' Pre-release ', '-pre')
    logger.info(f'Auto-determined version id "{version_name}"')
else:
    logger.info(f'Using version "{version_name}", specified in config file')
# Make warnings noticable, if any
time.sleep(2)

cache.MinecraftVersion(version_name)

# Only load modules if there is a config file
modules = []

# Support for pyinstaller
if getattr(sys, 'frozen', False):
    modules_folder = os.path.join(sys._MEIPASS, 'map_prepare/modules')
else:
    modules_folder = f'{__file__[:-8]}/modules'
# from time import sleep
# sleep(1000)
# Split modules into groups
for module in filter(lambda x: x.endswith('.py'), os.listdir(modules_folder)):
    module = '.'.join(module.split('.')[:-1])
    modules.append(importlib.import_module(f'.modules.{module}', 'map_prepare'))
    # Check for group info
    try: modules[-1].__group__
    except AttributeError: 
        setattr(modules[-1], '__group__', 'misc')
        logger.warn(f'Module {modules[-1].__name__} doesn\'t specify it\'s group')

    if not (modules[-1].__group__ in config['groups']):
        logger.warn(f'Module {modules[-1].__name__} specified nonexistent group "{modules[-1].__group__}"')

    # Check for priority info
    try: modules[-1].__priority__
    except AttributeError: 
        setattr(modules[-1], '__priority__', 0)
        logger.warn(f'Module {modules[-1].__name__} doesn\'t specify it\'s priority')

logger.info(f'Loaded {modules.__len__()} modules')

for group in config['groups']:
    #                      |               Filter by group               |  |    Sort by priority       |
    group_modules = sorted(filter(lambda x: x.__group__ == group, modules), key=lambda x: x.__priority__, reverse=True)
    for module in group_modules:
        # Check if there is an object "main" and if it's a function or not
        if hasattr(module, 'main') and callable(module.main):
            module.main(config)
        else:
            logger.error(f'Module {module.__file__} doesn\'t contain main() function! Skipping it.')