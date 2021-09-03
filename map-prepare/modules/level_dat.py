__priority__ = 0
__group__ = "level_dat"

from ..lib import utils, nbt_utils, logger, cache
from ..lib.config import config
from nbt import nbt
import string
import copy

def add_datapack(datapack_name: str, state: str='Enabled'):
    global level_dat
    try:
        level_dat['DataPacks'][state].append(nbt.TAG_String(value=datapack_name))
        return True
    except (IndexError, TypeError): pass

def remove_datapack(datapack_name: str):
    global level_dat
    try:
        del level_dat['DataPacks']['Enabled'][nbt_utils.get_value_index(level_dat['DataPacks']['Enabled'], datapack_name)]
        return True
    except (IndexError, TypeError): pass

    try: 
        del level_dat['DataPacks']['Disabled'][nbt_utils.get_value_index(level_dat['DataPacks']['Disabled'], datapack_name)]
        return True
    except (IndexError, TypeError): pass
    # If deletion failed or datapack wasn't found
    return False

def main(world_path: str):
    global level_dat

    if not config['settings']['modify_level_dat']:
        return
    
    logger.info('Modifying level.dat file')
    level_dat_file = nbt.NBTFile(filename=f'{world_path}/level.dat')
    # Get actual data
    level_dat = level_dat_file['Data']

    settings = config['settings']
    
    try:
        if settings['level_dat']['remove_player_tags']:
            # Get player
            Player = level_dat['Player']
            # Get player tags
            Player_Tags = Player['Tags']
            # Set tags to empty list
            for v in range(Player_Tags.tags.__len__()): del Player_Tags.tags[0]
    except KeyError: pass

    try:
        level_dat['GameType'].value = settings['level_dat']['game_type']
    except KeyError: pass

    try:
        level_dat['allowCommands'].value = settings['level_dat']['allow_commands']
    except KeyError: pass
    
    try:
        if settings['level_dat']['remove_fabric_datapack']:
            remove_datapack('Fabric Mods')
    except KeyError: pass

    try:
        level_dat['WasModded'].value = settings['level_dat']['was_modded']
    except KeyError: pass

    try:
        # Create a new list of brands
        new_brands = nbt.TAG_List()
        for brand in settings['level_dat']['brands']: new_brands.append(nbt.TAG_String(value=brand))
        # Replace old brands list with a new one
        level_dat['ServerBrands'].tags = new_brands.tags
    except KeyError: pass

    # This can fail either because there are no dimensions settings (Prior to 1.16) or Nether dimension was already deleted
    try:
        if settings['level_dat']['remove_nether']: del level_dat['WorldGenSettings']['dimensions']['minecraft:the_nether']
    except KeyError as e:
        logger.warn(f'Can\'t delete "minecraft:the_nether": {e.__str__()}')

    # This can fail either because there are no dimensions settings (Prior to 1.16) or End dimension was already deleted
    try:
        if settings['level_dat']['remove_end']: del level_dat['WorldGenSettings']['dimensions']['minecraft:the_end']
    except KeyError as e:
        logger.warn(f'Can\'t delete "minecraft:the_end": {e.__str__()}')

    try:
        if settings['level_dat']['disable_vanilla_datapack']:
            remove_datapack('vanilla')
            add_datapack('vanilla', state='Disabled')
    except KeyError: pass

    try:
        if settings['add_tag_fix_pack']:
            add_datapack('tag-fix.zip')
    except KeyError: pass

    # All datapack list modifications should go above this section
    if settings['zip_datapacks']:
        # For all enabled and disabled datapacks
        for list_name in ['Enabled', 'Disabled']:
            for i in range(level_dat['DataPacks'][list_name].tags.__len__()):
                # Get value
                value = level_dat['DataPacks'][list_name][i].value
                # If value start with 'file/' and not ends with '.zip'
                if not value.endswith('.zip') and value.startswith('file/'):
                    # Add '.zip'
                    level_dat['DataPacks'][list_name][i].value += '.zip'

            if level_dat['DataPacks'][list_name].tags.__len__() != 0:
                # If there any elements, they must be string
                level_dat['DataPacks'][list_name].tagID = nbt.TAG_STRING
                
    try:
        level_dat['LastPlayed'].value = settings['level_dat']['last_played']
    except KeyError: pass

    # if settings['update_data_version']:
    #     level_dat['DataVersion'].value = cache.current_version.data_version
    #     level_dat['Version']['Id'].value = cache.current_version.data_version

    try:
        level_dat['Time'].value = settings['level_dat']['time']
    except KeyError: pass
    #%
    try:
        level_dat['WorldGenSettings']['dimensions']['minecraft:overworld']['generator']['settings']['features'].value = settings['level_dat']['generate_features']
    except KeyError: pass
    
    try:
        level_dat['DifficultyLocked'].value = settings['level_dat']['difficulty_locked']
    except KeyError: pass
    # This will fail either because there are no scheduled functions or value is missing in config
    try:
        for event in level_dat['ScheduledEvents'].tags:
            event['TriggerTime'].value = settings['level_dat']['schedules_time']
    except KeyError: pass
    try:
        # Generate new name based on 
        name = string.Template(settings['level_dat']['name']).safe_substitute(settings)
        level_dat['LevelName'].value = name
    except KeyError: pass
    try:
        if level_dat['Version']['Name'] != cache.current_version.version:
            if settings['version_name'] == '':
                level_dat['Version']['Name'].value = cache.current_version.version
    except KeyError: pass

    # Gamerules
    try:
        gamerules = level_dat['GameRules']
        gamerules_list = [x.name for x in level_dat['GameRules'].tags]
        for gamerule, value in settings['level_dat']['gamerules'].items():
            if gamerule in gamerules_list:
                # Convert bools to string
                if isinstance(value, bool):
                    if value == True: value = 'true'
                    if value == False: value = 'false'
                
                # Try to convert to int
                # try: value = str(value)
                # except ValueError: pass
                # Write updated value
                gamerules[gamerule].value = copy.copy(str(value))

    except KeyError: pass

    # try:
    #     # Create list of new gamerules
    #     new_gamerules = nbt.TAG_List()
    #     for gamerule, value in settings['level_dat']['gamerules'].items():
    #         # Type check
    #         if type(value) == str: new_gamerules.append(nbt.TAG_String(value=value, name=gamerule))
    #         elif type(value) == int: new_gamerules.append(nbt.TAG_Int(value=value, name=gamerule))
    #     # Apply new gamerules
    #     level_dat['GameRules'].tags = new_gamerules.tags
    # except KeyError: pass

    # Save changes
    utils.delete_file(f'{config["world"]}/level.dat')
    level_dat_file.write_file(filename=f'{config["world"]}/level.dat')