__priority__ = 1
__group__ = 'datapacks'

from map_prepare.lib import logger, cache, utils
from map_prepare.lib.config import config
import shutil
import time

def main(world_path: str):
    settings = config['settings']

    # Fix issue #1
    if not utils.is_folder(f'{world_path}/datapacks'):
        logger.error('No datapacks folder found')
        return

    if settings['add_tag_fix_pack']:
        logger.info('Copying over "tag-fix" pack to datapacks')
        shutil.copy(f'{cache.current_version.version_cache_path}/tag-fix.zip', f'{world_path}/datapacks/tag-fix.zip')
    
    if settings['add_no_advancements_pack']:
        logger.info('Copying over "no-advancements" pack to datapacks')
        shutil.copy(f'{cache.current_version.version_cache_path}/no-advancements.zip', f'{world_path}/datapacks/no-advancements.zip')

    # Warn
    if settings['level_dat']['disable_vanilla_datapack']:
        if not settings['add_tag_fix_pack']:
            logger.warn('Option "level_dat">"disable_vanilla_datapack" is enabled without "add_tag_fix_pack". Only continue if you know what you\'re doing')
            time.sleep(3)
        # if settings['add_no_advancements_pack']:
        #     logger.warn('You don\'t need "no-advancements" pack with vanilla datapack disabled')
        #     time.sleep(3)