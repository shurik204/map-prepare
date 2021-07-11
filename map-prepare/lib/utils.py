from typing import List
from . import nbt_utils
from . import logger
from nbt import nbt
import zipfile
import shutil
import os
import re

def is_folder(path: str) -> bool:
    try: 
        open(path, 'rb')
        return False
    except (IsADirectoryError, FileNotFoundError): return True

def is_datapack(path: str) -> bool:
    # If a folder
    if is_folder(path):
        # Check for pack.mcmeta
        if not is_folder(f'{path}/pack.mcmeta') and is_folder(f'{path}/data'):
            return True
        else: 
            return False
    else:
        # If not, check if file is a zip archive
        if path.endswith('.zip') and zipfile.is_zipfile(path):
            try:
                archive = zipfile.ZipFile(path, mode='r')
                # Look for pack.mcmeta file if it is an archive
                archive.open('pack.mcmeta','r')
                archive.getinfo('data/')
                # If files are present, assume it's a datapack
                return True
            except KeyError: return False
        else: return False

def is_resourcepack(path: str) -> bool:
    # If a folder
    if is_folder(path):
        # Check for pack.mcmeta
        if not is_folder(f'{path}/pack.mcmeta') and is_folder(f'{path}/assets'):
            return True
        else: 
            return False
    else:
        # If not, check if file is a zip archive
        if path.endswith('.zip') and zipfile.is_zipfile(path):
            try:
                archive = zipfile.ZipFile(path, mode='r')
                # Look for pack.mcmeta file if it is an archive
                archive.open('pack.mcmeta','r')
                archive.getinfo('assets/')
                # If files are present, assume it's a resourcepack
                return True
            except KeyError: return False
        else: return False

def allowed_file(filename: str, allowed_files: List[str]) -> bool:
    """Returns True if one of the filters in allowed_files is True"""
    for entry in allowed_files:
        if entry.startswith('re:'):
            #               Properly remove prefix
            if re.fullmatch(entry[3:], filename) != None:
                return True
        if entry == filename:
            return True
    # If no match found, remove this file            
    return False

def delete_file(path: str) -> bool:
    if is_folder(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)

    logger.debug(f'Deleted file {path}')
    
    return True

# def file_exists(filename: str, folder_path: str):
    # if (filename in os.listdir(folder_path)) and not is_folder(f'{folder_path}/{filename}'): return True

def get_gamerules(world_path: str):
    level_dat = nbt.NBTFile(filename=f'{world_path}/level.dat')
    game_rules = {}
    for game_rule in nbt_utils.get_property(nbt_utils.get_property(level_dat, 'Data'), 'GameRules').tags:
        value = game_rule.value
        # Try converting value to int
        try: value = int(value)
        except ValueError: pass
        # Write game rule to others
        game_rules[game_rule.name] = value
    return game_rules

# def generate_config(world_path: str) -> bool:
#     with open(f'{world_path}/map-prepare.json', 'w+', encoding='utf-8') as conf_file:
#         # Copy world prepare config
#         # MAKE SURE TO RECURSIVELY COPY DICT OR IT WILL FUCK ITSELF
#         conf = copy.deepcopy(config['settings'])
#         # Copy gamerules from level.dat
#         conf['level_dat']['gamerules'] = get_gamerules(world_path)
#         # Update them with overrides
#         conf['level_dat']['gamerules'].update(config['settings']['level_dat']['gamerules'])
#         with open(f'{world_path}-map-prepare.json', 'w+', encoding='utf-8') as config_file:
#             config_file.write(ujson.dumps(conf, ensure_ascii=False, indent=2))

def get_all_region_folders(world_path: str) -> List[str]:
    region_folders = []

    region_folder = f'{world_path}/region'
    if os.path.isdir(region_folder):
        region_folders.append(str(region_folder))

    # Don't forget about End and Nether dimensions
    dim1_folder = f'{world_path}/DIM1'
    if os.path.isdir(dim1_folder):
        region_folders.append(str(dim1_folder))

    dim_1_folder = f'{world_path}/DIM-1'
    if os.path.isdir(dim_1_folder):
        region_folders.append(str(dim_1_folder))
        
    try:
        for namespace in filter(lambda x: os.path.isdir(x), os.listdir(f'{world_path}/dimensions')):
            namespace_path = f'{world_path}/dimensions/{namespace}'

            for dimension in filter(lambda x: os.path.isdir(x), os.listdir(namespace_path)):
                dimension_region_path = f'{namespace_path}/{dimension}/region'
                if os.path.isdir(dimension_region_path):
                    region_folders.append(str(dimension_region_path))
    except FileNotFoundError: pass

    return region_folders