__priority__ = 0
__group__ = 'misc'

from ..lib.in_memory_zipfile import InMemoryZipFile
from ..lib import logger, cache, utils
from ..lib.config import config
import zipfile
import ujson
import os


def repack_archive(file_to_replace: str, new_contents: str, zip_file: zipfile.ZipFile) -> InMemoryZipFile:
    new_zip_file = InMemoryZipFile()

    for file in zip_file.infolist():
        # If we found what we're looking for, replace it
        if file.filename == file_to_replace:
            new_zip_file.append(file.filename, new_contents)
        else:
            new_zip_file.append(file.filename, zip_file.read(file.filename))

    return new_zip_file


def main(world_path: str):
    settings = config['settings']

    if not settings['update_pack_mcmeta']:
        return
    
    logger.info(f'Updating pack.mcmeta')

    pack_format_data = cache.current_version.pack_version['data'] if settings['pack_format_data'] == 0 else settings['pack_format_data']
    pack_format_resource = cache.current_version.pack_version['resource'] if settings['pack_format_resource'] == 0 else settings['pack_format_resource']

    for dirpath, _, files in os.walk(world_path):
        for file in files:

            file_path = os.path.join(dirpath, file)

            if file.endswith(".zip") and zipfile.is_zipfile(file_path):
                
                if utils.is_resourcepack(file_path) or utils.is_datapack(file_path):
                    with zipfile.ZipFile(file_path, mode='r') as zip_file:
                            pack_mcmeta = None
                        # try:
                            # If spliced together, raises ValueError. WTF?
                            pack_mcmeta_bytes = zip_file.read('pack.mcmeta')
                            pack_mcmeta_string = pack_mcmeta_bytes.decode('utf-8').replace('\ufeff', '')

                            pack_mcmeta = ujson.loads(pack_mcmeta_string)

                            if utils.is_resourcepack(file_path):
                                logger.info(f'Updating pack.mcemeta in resourcepack "{file_path}"')
                                pack_mcmeta['pack']['pack_format'] = pack_format_resource
                            elif utils.is_datapack(file_path):
                                logger.info(f'Updating pack.mcemeta in datapack "{file_path}"')
                                pack_mcmeta['pack']['pack_format'] = pack_format_data
                            new_zip_file = repack_archive('pack.mcmeta', ujson.dumps(pack_mcmeta, indent=2), zip_file)
                        # except ValueError as e:
                            # logger.error(f'Failed to update pack.mcmeta in "{file_path}": {e.__str__()}')

                    utils.delete_file(file_path)
                    new_zip_file.write_to_file(file_path)
                # new_zip_data.seek(0)
                # with open(file_path, 'wb') as fp:
                #     fp.write(new_zip_data.read())