__priority__ = 0
__group__ = 'datapacks'

from map_prepare.lib import utils, logger
import shutil
import os

def main(config: dict):
    world_path = config['world']

    if config['settings']['zip_datapacks']:

        # Fix issue #1
        if not utils.is_folder(f'{world_path}/datapacks'):
            logger.error('No datapacks folder found')
            return

        logger.info('Archiving datapacks')
        #               |              Only select folders             |
        for datapack in filter(lambda x: utils.is_folder(f'{world_path}/datapacks/{x}'), os.listdir(f'{world_path}/datapacks')):
            datapack_path = f'{world_path}/datapacks/{datapack}'
            shutil.make_archive(datapack_path, 'zip', datapack_path)
            utils.delete_file(datapack_path)