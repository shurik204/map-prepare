__priority__ = 0
__group__ = 'misc'

from ..lib import cache, utils, logger
from ..lib.config import config
from nbt import nbt, region
import io
import os

def main(world_path: str):
    if not config['settings']['update_data_version']:
        return
    # Use config['settings']['data_version'] if it's not 0. Otherwise provided by 
    dataversion = cache.current_version.data_version if config['settings']['data_version'] == 0 else config['settings']['data_version']

    for dirpath, _, files in os.walk(world_path):
        for nbt_file in files:
            if nbt_file.endswith(".dat") or nbt_file.endswith(".nbt"):
                nbt_file_path = os.path.join(dirpath, nbt_file)

                logger.info(f'Updating DataVersion in NBT file "{nbt_file_path}"')
                # Constuct path to NBT file
                nbt_file = nbt.NBTFile(filename=nbt_file_path)
                # Update DataVersion
                # Most files have it in the root
                try: nbt_file['DataVersion'].value = dataversion
                except KeyError: pass
                # level.dat has it in Data
                try: nbt_file['Data']['DataVersion'].value = dataversion
                except KeyError: pass
                # And id
                try: nbt_file['Data']['Version']['Id'].value = dataversion
                except KeyError: pass
                # Overwrite file
                utils.delete_file(nbt_file_path)
                nbt_file.write_file(nbt_file_path)

            elif nbt_file.endswith('.mca'):
                nbt_file_path = os.path.join(dirpath, nbt_file)

                logger.info(f'Updating DataVersion in region file "{nbt_file_path}"')
                # Open and read file into memory
                with open(nbt_file_path, 'rb') as reg_file:
                    reg_io = io.BytesIO(reg_file.read())

                reg = region.RegionFile(fileobj=reg_io)
                for x in range(32):
                    for z in range(32):             # Make sure to clear the previous chunk
                        chunk = None
                        try:
                            chunk = reg.get_nbt(x, z)
                        # No chunk: just skip
                        except region.InconceivedChunk: pass
                        # Chunk has length of 0: remove it.
                        except region.ChunkHeaderError: reg.unlink_chunk(x, z)

                        if chunk != None:
                            chunk['DataVersion'].value = dataversion
                            # Because this operation writes every time
                            # we need to keep region file in memory
                            reg.write_chunk(x,z, chunk)

                # Open and write file from memory
                with open(nbt_file_path, 'wb') as reg_file:
                    # Seek to the beginning of the file
                    reg_io.seek(0)
                    reg_file.write(reg_io.read())