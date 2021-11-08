from nbt import nbt

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

def sections_exist(chunk: nbt.TAG_Compound):
    try:
        chunk['Level']['Sections']
        return True
    except (KeyError, AttributeError): pass

    return False