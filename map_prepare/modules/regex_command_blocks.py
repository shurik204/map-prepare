__priority__ = 0
__group__ = 'regions'

from map_prepare.lib import logger, utils
from nbt import nbt, region
import io
import os
import re



def main(config: dict):
    world_path = config['world']

    settings = config['settings']

    try:
        # Check if there are any regex rules
        # Return if none
        if settings['commands_regex_replace'].__len__() == 0: return
        # Return if "commands_regex_replace" is not a list or doesn't exist
    except (AttributeError, KeyError): return

    logger.info('Applying regex rules to command blocks')

    regex_rules = [v for v in filter(lambda x: x['find'] != '', settings['commands_regex_replace'])]

    region_folders = utils.get_all_region_folders(world_path)

    for region_folder_path in region_folders:
        logger.info(f'Working on folder "{region_folder_path}"')

        for region_name in os.listdir(region_folder_path):
            # Construct path to region file
            region_path = f'{world_path}/region/{region_name}'

            with open(region_path, 'rb') as region_file:
                region_io = io.BytesIO(region_file.read())

            reg = region.RegionFile(fileobj=region_io)
            # Flag to indicate if any chunk was changed
            modified_chunk = False
            
            logger.info(f'Looking for command blocks in "{region_name}" with {reg.chunk_count()} chunk{"s" if reg.chunk_count() != 1 else ""}')
            for x in range(32):
                for z in range(32):
                    # Make sure to clear the previous chunk
                    chunk = None

                    try:
                        chunk = reg.get_nbt(x, z)
                        
                    # No chunk: just skip
                    except region.InconceivedChunk: pass
                    # Chunk has length of 0: remove it.
                    except region.ChunkHeaderError: reg.unlink_chunk(x, z)

                    if chunk != None:
                        try:
                            if chunk['Level']['TileEntities'].tags.__len__() != 0:
                                for tile_entity in chunk['Level']['TileEntities'].tags:
                                    for rule in regex_rules:
                                        try:
                                            command = tile_entity['Command'].value
                                            tile_entity['Command'].value = re.sub(rule['find'], rule['replace'], tile_entity['Command'].value)
                                            if not modified_chunk and tile_entity['Command'].value != command:
                                                # Only write chunk if it was modified
                                                modified_chunk = True
                                                reg.write_chunk(x,z, chunk)
                                        except KeyError: pass
                        except KeyError: pass
        
            if modified_chunk:
                logger.debug(f'Writing region "{region_name}" with {reg.chunk_count()} chunks')
                # Write changes to file
                with open(region_path, 'wb') as region_file:
                    # Make sure to seek to the beginning of the BytesIO
                    region_io.seek(0)
                    # And then write data to disk
                    region_file.write(region_io.read())