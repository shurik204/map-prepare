__priority__ = 99
__group__ = 'global'

from map_prepare.lib import utils, logger
import shutil
import os


def main(config: dict):
    world_path = config['world']

    logger.info('Removing extra files from world folder')

    # if 'map-prepare.json' in os.listdir(world_path):
        # logger.info('Moving config file out of the world folder')
        # shutil.move(f'{world_path}/{world_config}', f'./{world_path}-map-prepare.json')

    for file in os.listdir(world_path):
        if not utils.matches_filter(file, config['settings']['allowed_files']['root']):
            # Construct a file path
            file_path = f'{world_path}/{file}'
            # Delete file whatever type it is. (Actially file or folder)
            utils.delete_file(file_path)
    try:
        # Remove non-datapack files and folders
        for file in os.listdir(f'{world_path}/datapacks'):
            # Construct a file path
            file_path = f'{world_path}/datapacks/{file}'
            # If path is not a datapack
            if not utils.is_datapack(file_path):
                # remove it
                utils.delete_file(file_path)

        # Expect datapack folder filter to be empty or being absent completely.
        try:
            for datapack_folder in os.listdir(f'{world_path}/datapacks'):
                # Construct datapack path
                datapack_path = f'{world_path}/datapacks/{datapack_folder}'
                if utils.is_folder(datapack_path):
                    for file in os.listdir(datapack_path):
                        if not utils.matches_filter(file, config['settings']['allowed_files']['datapack_folder']):
                            # Construct file path
                            file_path = f'{datapack_path}/{file}'

                            utils.delete_file(file_path)
        except KeyError: pass

    # If datapacks folder is not present
    except FileNotFoundError:
        logger.warn('Can\'t find datapacks folder.')

    # For all folders that match filter |                 Have filter in config         |     |   Is a folder                    |
    for folder_name in filter(lambda x: (x in config['settings']['allowed_files'].keys()) and utils.is_folder(f'{world_path}/{x}'),  os.listdir(world_path)):
        # Contruct path to folder
        folder = f'{world_path}/{folder_name}'
        # For file in folder
        for filename in os.listdir(folder):
            # Check if this file belongs here
            if not utils.matches_filter(filename, config['settings']['allowed_files'][folder_name]):
                # Contruct path to file
                file = f'{folder}/{filename}'
                # Remove it if it doesn't
                utils.delete_file(file)
    try:
        # Custom dimensions folder
        for namespace in os.listdir(f'{world_path}/dimensions'):
            namespace_path = f'{world_path}/dimensions/{namespace}'
            for dimension in os.listdir(namespace_path):

                dimension_path = f'{namespace_path}/{dimension}'

                for file in os.listdir(dimension_path):
                    if not utils.matches_filter(file, config['settings']['allowed_files']['dimension_folder']):
                        # Construct file path
                        file_path = f'{dimension_path}/{file}'

                        utils.delete_file(file_path)
    except FileNotFoundError: pass

    # Nether
    try:
        for file in os.listdir(f'{world_path}/DIM-1'):
            if not utils.matches_filter(file, config['settings']['allowed_files']['dimension_folder']):
                # Construct file path
                file_path = f'{world_path}/DIM-1/{file}'

                utils.delete_file(file_path)
    except FileNotFoundError: pass

    # End
    try:
        for file in os.listdir(f'{world_path}/DIM1'):
            if not utils.matches_filter(file, config['settings']['allowed_files']['dimension_folder']):
                # Construct file path
                file_path = f'{world_path}/DIM1/{file}'

                utils.delete_file(file_path)
    except FileNotFoundError: pass