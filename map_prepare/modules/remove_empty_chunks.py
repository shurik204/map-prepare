__priority__ = 97
__group__ = 'regions'

from map_prepare.lib import logger, utils, nbt_utils
from map_prepare.lib.config import config
from multiprocessing import JoinableQueue
from map_prepare.lib import anvil
from nbt import nbt, region
from queue import Empty
import multiprocessing
import time
import io
import os

def is_empty_section(anvil_chunk: anvil.Chunk, section= nbt.TAG_Compound):
    for x in range(16):
        for y in range(16):
            for z in range(16):
                if anvil_chunk.get_block(x, y, z, section=section).name() != 'minecraft:air':
                    return False
    return True



class RegionProcessor(multiprocessing.Process):
    def __init__(self, q: JoinableQueue):
        super().__init__(name=f'RegionProcessor-{utils.counter("emptychunks")}', args=(q, ), target=self.actual_task)
        self.q = q

        self.start()

    def actual_task(self, q):
        while True:
            try:
                # Poll queue every 0.1 second for a new task
                region_path = q.get(timeout=0.1)
            except Empty:
                # If queue is empty, terminate the thread
                # Self-recycle :)
                return
            with open(region_path, 'rb') as region_file:
                region_io = io.BytesIO(region_file.read())

            reg = region.RegionFile(fileobj=region_io)
            anv_reg = anvil.Region.from_file(region_path)

            # Empty region
            new_region_io = io.BytesIO()
            new_reg = region.RegionFile(fileobj=new_region_io)

            logger.info(f'Processing region "{region_path}" with {reg.chunk_count()} chunk{"s" if reg.chunk_count() != 1 else ""}')
            for x in range(32):
                for z in range(32):
                    # Make sure to clear the previous chunk
                    chunk = None
                    anv_chunk = None

                    try:
                        chunk = reg.get_nbt(x, z)
                        anv_chunk = anv_reg.get_chunk(x, z)
                    # No chunk: just skip
                    except region.InconceivedChunk: pass
                    # Chunk has length of 0: remove it.
                    except region.ChunkHeaderError: reg.unlink_chunk(x, z)
                    # Added KeyError to prevent crash because TileEntities is missing (ToG is a weird map)
                    except (anvil.chunk.ChunkNotFound, KeyError): pass

                    if chunk != None and anv_chunk != None:
                        empty_chunk = True

                        # Minecraft 1.18 support
                        try: chunk_sections = chunk["Level"]["Sections"]    # Default
                        except KeyError: chunk_sections = chunk['sections'] # 1.18+
                        
                        # Assume that it can be 1.17, where entities
                        # were moved into another region-like file
                        no_entities = nbt_utils.entities_exist(chunk)

                        no_sections = nbt_utils.sections_exist(chunk)

                        if not no_sections:
                            # Try checking this chunk by looking for tile entities (chests, barrels, command blocks, etc.)
                            try: empty_chunk = nbt_utils.block_entities_exist(chunk)
                            except KeyError: pass
                            # Actually heavy check below
                            if empty_chunk:
                                # Chunks are stored in 16x16x16 sections from 0 to 15.
                                # For every section that exists in this chunk
                                for section in chunk_sections:
                                    if nbt_utils.palette_exists(section):
                                        empty_chunk = is_empty_section(anv_chunk, section)
                                        if not empty_chunk: break

                        if empty_chunk and no_entities:
                            # Remove empty chunk
                            reg.unlink_chunk(x, z)
                        else:
                            new_reg.write_chunk(x, z, chunk)

            # Check if there is anything left
            # If region is empty:
            if new_reg.chunk_count() == 0:
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

            q.task_done()


def main(world_path: str):
    if not config['settings']['remove_empty_chunks']:
        return

    q = JoinableQueue()

    logger.info('Removing empty chunks')

    logger.info('Counting chunks')
    total_chunks = 0
    total_files = 0
    # Moved region folders search to utils
    region_folders = utils.get_all_region_folders(world_path)
    
    for region_folder_path in region_folders:
        # logger.info(f'Processing folder "{region_folder_path}"')

        for region_name in os.listdir(region_folder_path):
            # Filter out bad chunks
            try:
                # Construct path to region file
                region_path = f'{region_folder_path}/{region_name}'
                # Counters
                total_chunks += region.RegionFile(region_path).chunk_count()
                total_files += 1

                q.put(str(region_path))
            except region.MalformedFileError:
                # Just delete that
                utils.delete_file(region_path)

    logger.info(f'Found {total_chunks} chunks in {total_files} region files')

    # multiprocessing.set_start_method('spawn')
    threads = []
    for _ in range(config['threads']):
        threads.append(RegionProcessor(q))
        
    files_left = q.qsize()
    while (q.qsize()):
        if files_left != q.qsize():
            logger.info(f'Processing progress: {total_files - q.qsize()}/{total_files}')
            files_left = q.qsize()

    time.sleep(1)
    logger.info('Waiting for threads to finish')
    q.join()

    del threads