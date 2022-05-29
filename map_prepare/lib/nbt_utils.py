from map_prepare.lib.nbt import nbt

def get_property(tag: nbt.TAG_Compound, property: str):
    return filter(lambda x: x.name == property, tag.tags).__next__()

def get_property_index(tag: nbt.TAG_Compound, property: str) -> int:
    # if get_property(tag, property) != None:
    for index, _tag in enumerate(tag.tags):
        if _tag.name == property:
            return index

def get_value_index(tag: nbt.TAG_Compound, value: str) -> int:
    # if get_property(tag, property) != None:
    for index, _tag in enumerate(tag.tags):
        if _tag.value == value:
            return index

def sections_exist(chunk: nbt.TAG_Compound) -> bool:
    # < 1.17 format
    try:
        chunk['Level']['Sections']
        return True
    except KeyError:
        # 1.18+ format
        try:
            chunk['sections']
            return True
        except KeyError: return False

def palette_exists(section: nbt.TAG_Compound) -> bool:
    # < 1.17 format
    try:
        section['Palette']
        return True
    except KeyError:
        # 1.18+ format
        try:
            section['palette']
            return True
        except KeyError: return False

def blocks_exist(section: nbt.TAG_Compound) -> bool:
    # < 1.17 format
    try:
        section['BlockStates']
        return True
    except KeyError:
        # 1.18+ format
        try:
            section['block_states']
            return True
        except KeyError: return False

def entities_exist(chunk: nbt.TAG_Compound) -> bool:
    entities = False
    try:
        # Pre 1.14 I guess?
        if isinstance(chunk['Level']['Entities'], nbt.TAG_Long_Array):
            entities = chunk['Level']['Entities'].__len__() != 0
        else: entities = chunk['Level']['Entities'].tagID != 0
    except KeyError: pass

    return entities

def block_entities_exist(chunk: nbt.TAG_Compound) -> bool:
    # < 1.17 format
    try:
        chunk['Level']['TileEntities']
        return True
    except KeyError:
        # 1.18+ format
        try:
            chunk['block_entities']
            return True
        except KeyError: return False