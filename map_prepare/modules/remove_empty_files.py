__priority__ = 98
__group__ = 'global'

from map_prepare.lib import utils, logger
import os


def main(config: dict):
    world_path = config['world']

    try:
        if config['settings']['remove_empty_files'].__len__() != 0: logger.info('Removing empty files from world folder')
    except KeyError: return

    for dirpath, _, files in os.walk(world_path):
        for file_name in files:
            if file_name.split('.')[-1] in config['settings']['remove_empty_files']:

                # Join two strings to get actual path
                file_path=os.path.join(dirpath, file_name)

                if os.stat(file_path).st_size == 0: utils.delete_file(file_path)