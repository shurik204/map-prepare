__priority__ = 0
__group__ = 'resourcepacks'

from map_prepare.lib import utils, logger
from sys import exit
import zipfile
import shutil
import os

def main(config: dict):
    world_path = config['world']

    if config['settings']['resourcepack'] != '':
        logger.info('Adding resourcepack to world folder')
        # Copy resourcepack to world folder
        if config['settings']['resourcepack'].endswith('.zip'):
            # If it's a folder, zip it
            if os.path.isdir(config['settings']['resourcepack']):
                logger.error('Zip archive can\'t be folder.')
                exit(6)
            
            if not zipfile.is_zipfile(config['settings']['resourcepack']):
                logger.error('Resourcepack is not a valid ZIP archive')
                exit(7)

            shutil.copyfile(config['settings']['resourcepack'], f'{world_path}/resources.zip')
        else:
            # If it's a folder zip it
            if not utils.is_resourcepack(config['settings']['resourcepack']):
                logger.error('Resourcepack folder can\'t be file.')
                exit(6)
            shutil.make_archive(f'{world_path}/resources', 'zip', config['settings']['resourcepack'])