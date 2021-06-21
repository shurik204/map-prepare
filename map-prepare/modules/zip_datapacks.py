__priority__ = 0
__group__ = 'datapacks'

from ..lib.config import config
from ..lib import utils, logger
import shutil
import os

def main(world_path):
    if config['settings']['zip_datapacks']:
        logger.info('Archiving datapacks')
        #               |              Only select folders             |
        for datapack in filter(lambda x: utils.is_folder(f'{world_path}/datapacks/{x}'), os.listdir(f'{world_path}/datapacks')):
            datapack_path = f'{world_path}/datapacks/{datapack}'
            shutil.make_archive(datapack_path, 'zip', datapack_path)
            utils.delete_file(datapack_path)