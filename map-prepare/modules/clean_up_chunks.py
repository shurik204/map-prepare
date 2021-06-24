__priority__ = 99
__group__ = 'regions'

from ..lib import logger, utils
from ..lib.config import config
from nbt import nbt, region
import anvil
import io
import os

def is_empty_section(anvil_chunk, section= nbt.TAG_Compound):
    for x in range(16):
        for y in range(16):
            for z in range(16):
                if anvil_chunk.get_block(x, y, z, section=section).name() != 'minecraft:air':
                    return False
    return True

def palette_exists(section: nbt.TAG_Compound):
    try:
        section['Palette']
        return True
    except KeyError: return False

def main(world_path: str):
    if not config['settings']['remove_empty_chunks']:
        return

    logger.info('Cleaning up empty chunks')

    # Moved region folders search to utils
    region_folders = utils.get_all_region_folders(world_path)

    for region_folder_path in region_folders:
        logger.info(f'Working on folder "{region_folder_path}"')

        for region_name in os.listdir(region_folder_path):
            # Construct path to region file
            region_path = f'{world_path}/region/{region_name}'

            with open(region_path, 'rb') as region_file:
                region_io = io.BytesIO(region_file.read())

            reg = region.RegionFile(fileobj=region_io)
            anv_reg = anvil.Region.from_file(region_path)

            logger.info(f'Processing region "{region_name}" with {reg.chunk_count()} chunk{"s" if reg.chunk_count() != 1 else ""}')
            for x in range(32):
                for z in range(32):
                    # Make sure to clear the previous chunk
                    chunk = None
                    try:
                        chunk = reg.get_nbt(x, z)
                        anv_chunk = anv_reg.get_chunk(x, z)
                    # No chunk: just skip
                    except region.InconceivedChunk: pass
                    # Chunk has length of 0: remove it.
                    except region.ChunkHeaderError: reg.unlink_chunk(x, z)
                    except anvil.chunk.ChunkNotFound: pass

                    if chunk != None:
                        empty_chunk = True

                        # Assume that it can be 1.17, where entities
                        # were moved into another region-like file
                        no_entites = True
                        try: no_entites = chunk['Level']['Entities'].tagID == 0
                        except KeyError: pass

                        no_sections = True
                        try: no_sections = chunk['Level']['Sections'].tagID == 0
                        except KeyError: pass

                        if not no_sections:
                            # Try checking this chunk by looking for tile entities (chests, barrels, command blocks, etc.)
                            try: empty_chunk = chunk['Level']['TileEntities'].tagID == 0
                            except KeyError: pass
                            # Actually heavy check
                            if empty_chunk:
                                # Chunks are stored in 16x16x16 sections from 0 to 15.
                                # For every section that exists in this chunk
                                for section in chunk['Level']['Sections']:
                                    if palette_exists(section):
                                        empty_chunk = is_empty_section(anv_chunk, section)
                                        if not empty_chunk: break
                                        
                        if empty_chunk and no_entites:
                            # Remove empty chunk
                            reg.unlink_chunk(x, z)
            
            # Check if there is anything left
            # If region is empty:
            if reg.chunk_count() == 0:
                logger.debug(f'Deleted empty region file "{region_name}"')
                # Just remove the file
                utils.delete_file(region_path)
            else:
                logger.debug(f'Writing region "{region_name}" with {reg.chunk_count()} chunks')
                # Write changes to file
                with open(region_path, 'wb') as region_file:
                    # Make sure to seek to the beginning of the BytesIO
                    region_io.seek(0)
                    # And then write data to disk
                    region_file.write(region_io.read())