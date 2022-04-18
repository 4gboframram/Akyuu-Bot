import asyncio
from typing import Optional

from .rom import Pointer, Rom
from .stats import Boneka
from .struct_annotations import *
from .structs import Struct, StructMeta
from .text_decode import text_decode
from ..config import config, data_json


class MapHeader(Struct, metaclass=StructMeta):
    map_layout: u32  # const struct MapLayout* (actual contents not needed)
    events: u32  # const struct MapEvents* (not needed)
    map_scripts: u32  # const u8* (not needed)
    connections: u32  # const struct MapConnections* (not needed)
    music: u16
    map_layout_id: u16
    region_map_section_id: u8  # the only important piece of data in the header for now
    cave: u8
    weather: u8
    map_type: u8
    unused: u8  # :tohnk:
    use_label: u8  # I have no idea what this does


class MapHeaderPtr(Struct, metaclass=StructMeta):
    ptr: Pointer[MapHeader]


header_ptr_t = Pointer[MapHeader]


class Bank(Struct, metaclass=StructMeta):  # map bank is an array of pointers to map headers
    ptr: Pointer[MapHeaderPtr]


BankPtr = Pointer[Bank]


async def get_bank_data(rom: Rom, bank: BankPtr) -> list[MapHeader]:
    ptr = Pointer[MapHeaderPtr](rom.deref(bank).ptr)
    headers: list[MapHeader] = []
    while (header_ptr := rom.deref(ptr).ptr) != 0xF7F7F7F7:
        headers.append(
            rom.deref(header_ptr_t(header_ptr))
        )
        ptr += 1

    return headers


class RawMapName(Struct, metaclass=StructMeta):
    name: byte[128]  # better to overshoot than to undershoot


class MapNamePtr(Struct, metaclass=StructMeta):
    ptr: Pointer[RawMapName]


RawMapNameP = Pointer[RawMapName]


async def get_all_map_names(rom: Rom) -> tuple[str, ...]:
    ptr = Pointer[MapNamePtr](config.offsets.MAP_NAMES_OFFSET)
    name_ptrs = (RawMapNameP(rom.deref(ptr + i).ptr) for i in range(config.NUM_MAP_NAMES))
    return tuple(
        text_decode(rom.deref(p).name) for p in name_ptrs
    )


# Actual Wild Data Moment

class RawWildEncounterData(Struct, metaclass=StructMeta):
    low: u8
    high: u8
    boneka: u16


class RawWildEncounterDataPtrData(Struct, metaclass=StructMeta):
    encounter_rate: u32
    ptr: Pointer[RawWildEncounterData]


RawWildPtr = Pointer[RawWildEncounterData]


@data_json
class WildEncounterData:
    boneka: str
    low: int
    high: int


class RawWildLocation(Struct, metaclass=StructMeta):
    bank: u8
    map: u8
    unused: u16
    grass: Pointer[RawWildEncounterDataPtrData]
    surf: Pointer[RawWildEncounterDataPtrData]
    tree: Pointer[RawWildEncounterDataPtrData]
    fish: Pointer[RawWildEncounterDataPtrData]


RawWildEncounterDataPtrDataPtr = Pointer[RawWildEncounterDataPtrData]


@data_json
class WildLocation:
    name: Optional[str]
    grass: Optional[tuple[WildEncounterData]]
    surf: Optional[tuple[WildEncounterData]]
    tree: Optional[tuple[WildEncounterData]]
    fish: Optional[tuple[WildEncounterData]]


async def get_header_from_bank_and_id(rom: Rom, bank: int, map_: int) -> MapHeader:
    ptr = Pointer[Bank](config.offsets.MAP_BANKS_OFFSET) + bank
    header_ptr_ptr = Pointer[MapHeaderPtr](rom.deref(ptr).ptr) + map_
    header_ptr = header_ptr_t(rom.deref(header_ptr_ptr).ptr)
    header = rom.deref(header_ptr)
    return header


async def parse_raw_wild_location(rom: Rom, loc: RawWildLocation, loc_names: tuple[str],
                                  boneka: tuple[Boneka]) -> WildLocation:
    header = await get_header_from_bank_and_id(rom, loc.bank, loc.map)
    name_index = header.region_map_section_id - config.MAPSECS_KANTO
    try:
        name = loc_names[name_index]
    except IndexError:
        name = None
    # parse grass, surf, tree, fish data
    grass = await parse_grass_encounter_ptr(rom, RawWildEncounterDataPtrDataPtr(loc.grass), boneka)
    surf = await parse_surf_encounter_ptr(rom, RawWildEncounterDataPtrDataPtr(loc.surf), boneka)
    tree = await parse_tree_encounter_ptr(rom, RawWildEncounterDataPtrDataPtr(loc.tree), boneka)
    fish = await parse_fish_encounter_ptr(rom, RawWildEncounterDataPtrDataPtr(loc.fish), boneka)
    return WildLocation(name, grass, surf, tree, fish)


async def parse_grass_encounter_ptr(rom: Rom, wild_data_ptr_ptr: Pointer[RawWildEncounterDataPtrData],
                                    boneka: tuple[Boneka, ...]) -> Optional[tuple[WildEncounterData, ...]]:
    if not wild_data_ptr_ptr:  # null check
        return None
    ptr = rom.deref(wild_data_ptr_ptr)

    if not ptr.encounter_rate:
        return None

    wild_data_ptr = RawWildPtr(ptr.ptr)
    raw_data_iter = (rom.deref(wild_data_ptr + i) for i in range(config.NUM_GRASS_ENCOUNTER_SLOTS))

    return tuple(WildEncounterData(boneka[raw.boneka].name, raw.low, raw.high) for raw in raw_data_iter)


async def parse_surf_encounter_ptr(rom: Rom, wild_data_ptr_ptr: Pointer[RawWildEncounterDataPtrData],
                                   boneka: tuple[Boneka, ...]) -> Optional[tuple[WildEncounterData, ...]]:
    if not wild_data_ptr_ptr:  # null check
        return None
    wild_data_ptr = RawWildPtr(rom.deref(wild_data_ptr_ptr).ptr)
    raw_data_iter = (rom.deref(wild_data_ptr + i) for i in range(config.NUM_SURF_ENCOUNTER_SLOTS))

    return tuple(WildEncounterData(boneka[raw.boneka].name, raw.low, raw.high) for raw in raw_data_iter)


async def parse_tree_encounter_ptr(rom: Rom, wild_data_ptr_ptr: Pointer[RawWildEncounterDataPtrData],
                                   boneka: tuple[Boneka, ...]) -> Optional[tuple[WildEncounterData, ...]]:
    if not wild_data_ptr_ptr:  # null check
        return None
    wild_data_ptr = RawWildPtr(rom.deref(wild_data_ptr_ptr).ptr)
    raw_data_iter = (rom.deref(wild_data_ptr + i) for i in range(config.NUM_TREE_ENCOUNTER_SLOTS))

    return tuple(WildEncounterData(boneka[raw.boneka].name, raw.low, raw.high) for raw in raw_data_iter)


async def parse_fish_encounter_ptr(rom: Rom, wild_data_ptr_ptr: Pointer[RawWildEncounterDataPtrData],
                                   boneka: tuple[Boneka, ...]) -> Optional[tuple[WildEncounterData, ...]]:
    if not wild_data_ptr_ptr:  # null check
        return None
    wild_data_ptr = RawWildPtr(rom.deref(wild_data_ptr_ptr).ptr)
    raw_data_iter = (rom.deref(wild_data_ptr + i) for i in range(config.NUM_FISH_ENCOUNTER_SLOTS))

    return tuple(WildEncounterData(boneka[raw.boneka].name, raw.low, raw.high) for raw in raw_data_iter)


async def get_all_wild_data(rom: Rom, boneka: tuple[Boneka]) -> tuple[WildLocation, ...]:

    map_names = await get_all_map_names(rom)
    ptr = Pointer[RawWildLocation](config.offsets.WILD_DATA_OFFSET)

    tasks = (parse_raw_wild_location(rom, rom.deref(ptr + i), map_names, boneka) for i in range(config.WILD_DATA_LEN))
    data = await asyncio.gather(*tasks)
    return tuple(i for i in data if i.name is not None and i.name != "Special Area")
