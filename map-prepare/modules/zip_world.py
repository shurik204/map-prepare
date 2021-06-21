__priority__ = 0
__group__ = 'final'

from ..lib.in_memory_zipfile import InMemoryZipFile
from ..lib.config import config
from ..lib import logger
import string
import os

def main(world_path: str):
    settings = config['settings']

    if not settings['zip_world']:
        return
    
    world_archive_name = string.Template(settings['archive_name'] + ('.zip' if not settings['archive_name'].endswith('.zip') else '')).safe_substitute(settings)
    world_archive_file = InMemoryZipFile()

    in_archive_name = string.Template(settings['in_archive_name']).safe_substitute(settings)

    logger.info(f'Archiving world folder into "{world_archive_name}"')

    for dirpath, _, files in os.walk(world_path):
        for file in files:
            file_path = os.path.join(dirpath, file)
            in_archive_path = os.path.join(in_archive_name,dirpath[world_path.__len__() + 1:], file)

            if not os.path.isdir(file_path):
                with open(file_path, 'rb') as f:
                    world_archive_file.append(in_archive_path, f.read())
    
    world_archive_file.write_to_file(world_archive_name)