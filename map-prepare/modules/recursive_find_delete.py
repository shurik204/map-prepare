__priority__ = 0
__group__ = 'global'

from ..lib.config import config
from ..lib import logger, utils
import os
import re

def main(world_path: str):
    if config['settings']['global_unwanted_files'].__len__() == 0:
        return
    
    files_to_find = config['settings']['global_unwanted_files']

    logger.info(f'Recursively looking for files with {files_to_find.__len__()} filename{"s" if files_to_find.__len__() != 1 else ""} to delete')

    deleted_files = 0

    for dirpath, _, files in os.walk(world_path):
        for file in files:
            # Use a util method to look for match in filter
            # I know, doesn't make a lot of sense, but it does, really.
            if utils.matches_filter(file, files_to_find):
                # Construct path to file
                file_path = f'{dirpath}/{file}'

                utils.delete_file(file_path)
                deleted_files += 1

    logger.info(f'Found and deleted {deleted_files} file{"s" if files_to_find.__len__() != 1 else ""}')