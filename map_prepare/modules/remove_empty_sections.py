__priority__ = 98
__group__ = 'regions'

from map_prepare.lib import logger, utils, nbt_utils
from multiprocessing import JoinableQueue
from nbt import nbt, region
from queue import Empty
import multiprocessing
import time
import io
import os

class RegionProcessor():
    def __init__(self, q: JoinableQueue):
        self.q = q
    
    def start(self):
        self.process = multiprocessing.Process(name=f'RegionProcessor-{utils.counter("emptychunks")}', args=(self.q, ), target=self.actual_task)
        self.process.start()

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

            # Empty region
            new_region_io = io.BytesIO()
            try:
                new_reg = region.RegionFile(fileobj=new_region_io)
            except region.RegionFileFormatError:
                logger.warn(f'Skipped region file "{region_path}"')
                q.task_done()
                continue

            logger.info(f'Processing region "{region_path}" with {reg.chunk_count()} chunk{"s" if reg.chunk_count() != 1 else ""}')
            for x in range(32):
                for z in range(32):
                    # Make sure to clear the previous chunk
                    chunk = None
                    # chunk_modified = False
                    
                    try:
                        chunk = reg.get_nbt(x, z)
                    # No chunk: just skip
                    except region.InconceivedChunk: pass
                    # Chunk has length of 0: remove it.
                    except region.ChunkHeaderError: reg.unlink_chunk(x, z)
                    # Added KeyError to prevent crash because TileEntities is missing (ToG is a weird map)
                    except KeyError: pass
                    except region.MalformedFileError: logger.warn(f'Skipped malformed chunk ({x},{z})')
                    
                    if chunk != None:
                        if nbt_utils.sections_exist(chunk):

                            # Minecraft 1.18 support
                            try: chunk_sections = chunk["Level"]["Sections"]    # Default
                            except KeyError: chunk_sections = chunk['sections'] # 1.18+

                            # Chunks are stored in 16x16x16 sections from 0 to 15.
                            # Go in reverse so I can modify the list
                            # i'm iterating through
                            for section_index in range(chunk_sections.__len__()-1,0,-1):
                                # If there is no BlockStates tag
                                if not nbt_utils.blocks_exist(chunk_sections[section_index]):
                                    logger.debug(f'''Removed section {chunk_sections[section_index]['Y']} from chunk ({x}, {z})''')
                                    # Remove it
                                    del chunk_sections[section_index]
                                    # chunk_modified = True

                            if chunk_sections.__len__() == 0 and not nbt_utils.entities_exist(chunk):
                                # Remove empty chunk
                                reg.unlink_chunk(x, z)
                            else:
                                new_reg.write_chunk(x,z,chunk)

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
    # Move import here to avoid Bad Things
    from map_prepare.lib.config import config

    if not config['settings']['remove_empty_sections']:
        return

    q = JoinableQueue()

    logger.info('Removing empty sections')

    logger.info('Counting chunks')
    total_chunks = 0
    total_files = 0
    # Moved region folders search to utils
    region_folders = utils.get_all_region_folders(world_path)
    
    for region_folder_path in region_folders:
        # logger.info(f'Processing folder "{region_folder_path}"')

        for region_name in os.listdir(region_folder_path):
            # Filter out bad region files
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
        thread = RegionProcessor(q)
        threads.append(thread)
        thread.start()
        
    files_left = q.qsize()
    while (q.qsize()):
        if files_left != q.qsize():
            logger.info(f'Processing progress: {total_files - q.qsize()}/{total_files}')
            files_left = q.qsize()

    time.sleep(1)
    logger.info('Waiting for threads to finish')
    q.join()

    del threads