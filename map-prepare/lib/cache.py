from requests.models import HTTPError
from . import logger
import requests
import zipfile
import shutil
import ujson
import os

global current_version
current_version = None

class MinecraftVersion(object):
    """Represents minecraft version"""
    def __init__(self, version: str):
        logger.info(f'Preparing cache for version "{version}"')

        # Get version list
        launcher_manifest = ujson.loads(requests.get('http://launchermeta.mojang.com/mc/game/version_manifest_v2.json').text)

        # Get required version string
        if version in ['latest','snapshot']:
            if version == 'latest':
                # Latest release
                self.version = launcher_manifest['latest']['release']
            else:
                # Latest snapshot
                self.version = launcher_manifest['latest']['snapshot']
        else:
            # Specific version
            self.version = version

        self.version_data = None
        # From all versions, grab the version we need
        for x in launcher_manifest['versions']: 
            if x['id'] == self.version:
                # Load it's data
                self.version_data = ujson.loads(requests.get(x['url']).text)
                break

        self.version_cache_path = f'./cache/{self.version}'

        # Exit if given version does not exist
        if self.version_data == None:
            logger.fatal(f'Can\'t find version {self.version}. Exitting...')
            exit(1)

        if not (self.version in os.listdir('./cache')):
            logger.info(f'Generating cache for version {self.version}')
            os.mkdir(self.version_cache_path)

        self.cached_client_path = f'{self.version_cache_path}/client.jar'

        # Save client jar
        self.download_client_jar()

        # Check if file is an archive
        if not zipfile.is_zipfile(self.cached_client_path):
            logger.fatal(f'{self.cached_client_path} is not a valid archive. Removing it... Please, try restarting this program.')
            os.unlink(self.cached_client_path)
            exit(2)

        self.set_language_list()

        # Get default language dictionary
        try:
            self.default_lang = None
            # Get default lang
            default_lang_str = zipfile.ZipFile(self.cached_client_path).read('assets/minecraft/lang/en_us.json').decode('utf-8')
            self.default_lang = ujson.loads(default_lang_str)
        except KeyError:
            logger.error('Unable to get en_us translation from client.jar')

        # Set pack format
        self.set_pack_version()
        
        self.set_data_version()

        self.generate_pack('no-advancements')

        self.generate_pack('tag-fix')


        global current_version
        current_version = self
        

    def download_client_jar(self):
        if not ('client.jar' in os.listdir(self.version_cache_path)):
            logger.info('Downloading client.jar')
            # Download client.jar
            with requests.get(self.version_data['downloads']['client']['url'], stream=True) as stream:
                try:
                    # Raise error if any
                    stream.raise_for_status()
                except requests.HTTPError:
                    logger.fatal('Failed to download minecraft client.jar file')
                with open(self.cached_client_path,'wb+') as client_file:
                    shutil.copyfileobj(stream.raw, client_file)

    def set_language_list(self):
        logger.info('Updating language list')
        
        assets_objects = ujson.loads(requests.get(self.version_data['assetIndex']['url']).text)['objects']
        self.lang_list = [asset_path[15:] for asset_path in filter(lambda x: x.startswith("minecraft/lang/"), assets_objects.keys())]
        logger.info(f'Found {self.lang_list.__len__()} languages')

    def set_pack_version(self):
        self.pack_version = {"resource": 1, "data": 1}

        def pack_mcmeta_method() -> int:
            # First get the assets hash list
            assets_objects = ujson.loads(requests.get(self.version_data['assetIndex']['url']).text)['objects']
            # Then get hash of the default pack.mcmeta
            pack_mcmeta_hash = assets_objects['pack.mcmeta']['hash']
            # Download pack.mcmeta
            pack_mcmeta = ujson.loads(requests.get(f'http://resources.download.minecraft.net/{pack_mcmeta_hash[:2]}/{pack_mcmeta_hash}').text)
            # Extract pack_format
            return [int(pack_mcmeta['pack']['pack_format'])] * 2
        
        def version_json_method():
            # Open version.json
            version_json = ujson.loads(zipfile.ZipFile(self.cached_client_path, mode='r').open('version.json').read().decode('utf-8'))
            try:
               # Check if it's split into data and resources version (1.17+)
               return [int(version_json['pack_version'])] * 2
            except TypeError:
                # Return this if it's split up
                return [version_json['pack_version']['resource'], version_json['pack_version']['data']]

        try:
            logger.info('Updating pack format using version.json method')
            self.pack_version['data'], self.pack_version['resource'] = version_json_method()
            logger.info(f'Pack format for datapacks is {self.pack_version["data"]}, resourcepacks - {self.pack_version["resource"]}')
        # Expect version.json not being in the jar
        except KeyError:
            logger.warn('No version.json file found!')
            try:
                logger.info('Updating pack format using pack.mcmeta method')
                self.pack_version['data'], self.pack_version['resource'] = pack_mcmeta_method()
                logger.info(f'Pack format is {self.pack_version["data"]}')
            except KeyError:
                logger.error('Can\'t get default resource pack format number. pack_format will be set to 1')

    def set_data_version(self):
        self.data_version = 0
        
        def version_json_method():
            version_json = ujson.loads(zipfile.ZipFile(self.cached_client_path, mode='r').open('version.json').read().decode('utf-8'))
            return int(version_json['world_version'])

        # Thanks CM for letting me know about version.json file :)
        try:
            logger.info('Updating data version using version.json method')
            self.data_version = version_json_method()
            logger.info(f'Data version is {self.data_version}')
        except KeyError:
            logger.warn('No version.json file found! DataVersion is set to 0')
            
    def extract_data(self, force=False):
        if force: shutil.rmtree('data')
        # Extract files from jar
        if not ('data' in os.listdir(self.version_cache_path)):
            logger.info('Extracting data from jar')
            # Open jar file
            zip_data = zipfile.ZipFile(self.cached_client_path, mode='r')
            # Get a list of all files we need
            data_files = filter(lambda x: x.startswith('data/minecraft/'), zip_data.namelist())
            # and extract them
            for file_path in data_files: zip_data.extract(file_path, f'{self.version_cache_path}/data')
            try:
                zip_data.extract('version.json', f'{self.version_cache_path}')
            except KeyError: pass

    def extract_resource(self, resource):
        # Open jar file
        zip_data = zipfile.ZipFile(self.cached_client_path, mode='r')

        # Get a list of all files we need
        data_files = list(filter(lambda x: x.startswith(f'data/minecraft/{resource}'), zip_data.namelist()))
        
        if (data_files.__len__() == 0): raise ValueError(f'Can\'t find resource named "{resource}"')
        
        # and extract them
        for file_path in data_files: zip_data.extract(file_path, f'{self.version_cache_path}/pack')

    def generate_pack(self, pack: str, force: bool=False):
        values = ['tag-fix', 'no-advancements']
        if not (pack in values):
            raise ValueError(f'''Argument "pack" only accepts "{'", "'.join(values)}". Got "{pack}."''')

        if force: os.unlink(f'{pack}.zip')

        if (pack == 'no-advancements') and not ('no-advancements.zip' in os.listdir(self.version_cache_path)):
            
            logger.info('Creating "No advancements pack"...')
            # Make sure to remove old folder if there is anything left
            shutil.rmtree(f'{self.version_cache_path}/pack', ignore_errors=True)

            self.extract_resource('advancements')

            for dirpath, subdirs, files in os.walk(f'{self.version_cache_path}/pack/data/minecraft/advancements'):
                for adv_filename in files:
                    if adv_filename.endswith(".json") and dirpath.find('/advancements')!=-1:
                        # Join two strings to get actual path
                        adv_filename=os.path.join(dirpath, adv_filename)
                        # Read the advancement from file
                        with open(adv_filename,'w+',encoding='utf-8') as adv_file:
                            adv_file.write('{"criteria":{"s":{"trigger":"minecraft:impossible"}}}')

            with open(f'{self.version_cache_path}/pack/pack.mcmeta', 'w+', encoding='utf-8') as mcmeta:
                mcmeta.write(f'''{{"pack": {{"pack_format": {self.pack_version['data']},"description": "No advancements ({self.version}) | Map-prepare by shurik204 (https://github.com/shurik204/map-prepare)"}}}}''')

            shutil.make_archive(f'{self.version_cache_path}/no-advancements', 'zip', f'{self.version_cache_path}/pack')

            logger.info('Generation complete! Cleaning up...')
            shutil.rmtree(f'{self.version_cache_path}/pack', ignore_errors=True)

        if (pack == 'tag-fix') and not ('tag-fix.zip' in os.listdir(self.version_cache_path)):
            
            logger.info('Creating "Tag fix" pack')
            # Make sure to remove old folder if there is anything left
            shutil.rmtree(f'{self.version_cache_path}/pack', ignore_errors=True)

            self.extract_resource('tags')

            with open(f'{self.version_cache_path}/pack/pack.mcmeta', 'w+', encoding='utf-8') as mcmeta:
                mcmeta.write(f'''{{"pack": {{"pack_format": {self.pack_version['data']},"description": "Tag fix ({self.version}) | Map-prepare by shurik204 (https://github.com/shurik204/map-prepare)"}}}}''')

            shutil.make_archive(f'{self.version_cache_path}/tag-fix', 'zip', f'{self.version_cache_path}/pack')

            logger.info('Generation complete! Cleaning up...')
            shutil.rmtree(f'{self.version_cache_path}/pack', ignore_errors=True)

if not ('cache' in os.listdir('.')):
    # utils.
    logger.info('Creating cache folder')
    os.mkdir('cache')