__priority__ = 99
__group__ = 'regions'

from ..lib import logger, utils, nbt_utils
from ..lib.config import config
from nbt import nbt, region
import threading
import queue
import io
import os

def blocks_exist(section: nbt.TAG_Compound):
    try:
        section['BlockStates']
        return True
    except KeyError: return False

class RegionProcessor(threading.Thread):
    def __init__(self, queue: queue.Queue):
        super().__init__(name=f'RegionProcessor-{threading.active_count()-1}')
        self.queue = queue

        self.start()

    def run(self):
        try:
            while True:
                # Poll queue every second for a new task
                self.actual_task(self.queue.get(timeout=1))
        except queue.Empty:
            # If queue is empty, terminate the thread
            # Self-recycle :)
            del self

    def actual_task(self, region_path):
        with open(region_path, 'rb') as region_file:
            region_io = io.BytesIO(region_file.read())

        reg = region.RegionFile(fileobj=region_io)

        # Empty region
        new_region_io = io.BytesIO()
        new_reg = region.RegionFile(fileobj=new_region_io)

        logger.info(f'Processing region "{region_path}" with {reg.chunk_count()} chunk{"s" if reg.chunk_count() != 1 else ""}')
        for x in range(32):
            for z in range(32):
                # Make sure to clear the previous chunk
                chunk = None
                chunk_modified = False
                
                try:
                    chunk = reg.get_nbt(x, z)
                # No chunk: just skip
                except region.InconceivedChunk: pass
                # Chunk has length of 0: remove it.
                except region.ChunkHeaderError: reg.unlink_chunk(x, z)
                # Added KeyError to prevent crash because TileEntities is missing (ToG is a weird map)
                except KeyError: pass

                if chunk != None:
                    if nbt_utils.sections_exist(chunk):
                        # Chunks are stored in 16x16x16 sections from 0 to 15.
                        # Go in reverse so I can modify the list
                        # i'm iterating through
                        for section_index in range(chunk['Level']['Sections'].__len__()-1,0,-1):
                            # If there is no BlockStates tag
                            if not blocks_exist(chunk['Level']['Sections'][section_index]):
                                logger.debug(f'Removed section {chunk["Level"]["Sections"][section_index]["Y"]} from chunk ({x}, {z})')
                                # Remove ir
                                del chunk["Level"]["Sections"][section_index]
                                chunk_modified = True

                        if chunk['Level']['Sections'].__len__() == 0:
                            # Remove empty chunk
                            reg.unlink_chunk(x, z)
                        elif chunk_modified:
                            new_reg.write_chunk(x,z,chunk)

        # Check if there is anything left
        # If region is empty:
        if reg.chunk_count() == 0:
            logger.debug(f'Deleted empty region file "{region_path}"')
            # Just remove the file
            utils.delete_file(region_path)
        else:
            logger.debug(f'Writing region "{region_path}" with {new_reg.chunk_count()} chunks')
            # Write changes to file
            with open(region_path, 'wb') as region_file:
                # Make sure to seek to the beginning of the BytesIO
                new_region_io.seek(0)
                # And then write data to disk
                region_file.write(new_region_io.read())

        self.queue.task_done()


def main(world_path: str):
    if not config['settings']['remove_empty_sections']:
        return

    q = queue.Queue()

    logger.info('Removing empty sections')

    # Moved region folders search to utils
    region_folders = utils.get_all_region_folders(world_path)
    
    for region_folder_path in region_folders:
        # logger.info(f'Processing folder "{region_folder_path}"')

        for region_name in os.listdir(region_folder_path):
            # Construct path to region file
            region_path = f'{region_folder_path}/{region_name}'

            q.put(str(region_path))
            
    threads = []
    for _ in range(config['threads']):
        threads.append(RegionProcessor(q))
    
    q.join()

    del threads