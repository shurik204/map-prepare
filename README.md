# map-prepare
Automatically prepare Mineraft map for release.

Current state: `kinda works`

**Make sure you have backups for your world before running this program!**

Things it currently does:
- Delete extra files from world like session.lock, playerdata, stats, advancements, DIM-1, DIM1  folders (Including any other files/folders that shouldn't normally be in the world folder)
- Remove empty chunks from the world. Chunk is considered empty if there are no blocks other than "minecraft:air" and no entities.
- Generate tag fix and no vanilla advancement datapacks for required version. There is also an option to disable vanilla datapack.
- Change DataVersion int to current (or specified in config) value everywhere it can find (all storages, region files, structures).
- Set fancy name for the world, switch gamerules, lock difficulty, enable/disable commands in singleplayer
- Zip all datapacks
- Zip and add resourcepack to the world if provided
- Update pack_format in resourcepack and datapacks

# How to use

To run this you need:
- Python 3.8+ (https://www.python.org/downloads/)
- A few Python libraries

### Download
```
git clone https://github.com/shurik204/map-prepare.git
```
or get ZIP archive
**[\[Here\]](https://github.com/shurik204/map-prepare/archive/refs/heads/master.zip)**

Open `cmd` in folder where you downloaded program

### Install dependencies
```
python -m pip install -r requirements.txt
```
#### Linux:
```
pip3 install -r requirements.txt
```

Before running it make sure you copy your world into the folder with program and change `world` in `config.json` to your world folder name.

## Run:
```sh
python -m map-prepare
```

A file named `[your_world_folder]-map-prepare.json` should've appeared in the folder. Change settings you need and relaunch the program. All settings are explained in `config.json` file.