import asyncio
from typing import Generator, Optional

from .text_decode import text_decode

from .rom import Pointer, Rom
from .sprite_png import get_sprite_data
from .struct_annotations import *
from .structs import Struct, StructMeta
from ..config import config, data_json


class SpriteData(Struct, metaclass=StructMeta):
    ptr: u32  # not an actual pointer type because the size varies
    uncompressed_len: u16
    index: u16


SpriteDataPtr = Pointer[SpriteData]


async def get_all_sprite_data(rom: Rom) -> tuple[Optional[bytes]]:
    stream = rom.create_stream()
    sprites = [None]

    for i in range(1, config.BONEKA_COUNT):  # exclude decamark because it causes palette issues

        sprite_ptr = SpriteDataPtr(config.offsets.SPRITE_OFFSET) + i
        sprite_dat = rom.deref(sprite_ptr)
        pal_ptr = SpriteDataPtr(config.offsets.PALETTE_OFFSET) + i
        pal_dat = rom.deref(pal_ptr)
        sprites.append(get_sprite_data(stream, sprite_dat.ptr, pal_dat.ptr))

    return tuple(sprites)


class RawBonekaStatData(Struct, metaclass=StructMeta):
    hp: u8
    attack: u8
    defense: u8
    speed: u8
    sp_atk: u8
    sp_def: u8
    type_1: u8
    type_2: u8
    catch_rate: u8
    base_exp: u8
    ev_yield: u16  # Yeah. I'm not working with this
    item_1: u16
    item_2: u16
    gender_ratio: u8
    steps_to_hatch: u8
    base_happiness: u8
    growth_rate: u8
    egg_1: u8
    egg_2: u8
    ability_1: u8
    ability_2: u8
    run_rate: u8
    dex_stuff: u8
    padding: u16


async def get_all_boneka_stats(rom: Rom) -> tuple[RawBonekaStatData, ...]:
    ptr = Pointer[RawBonekaStatData](config.offsets.BONEKA_STAT_OFFSET)
    return tuple(rom.deref(ptr + i) for i in range(config.BONEKA_COUNT))


class RawBonekaName(Struct, metaclass=StructMeta):
    name: byte[11]


async def get_all_boneka_names(rom: Rom) -> tuple[str, ...]:
    ptr = Pointer[RawBonekaName](config.offsets.BONEKA_NAME_OFFSET)
    raw_dat_iter = (rom.deref(ptr + i) for i in range(config.BONEKA_COUNT))
    return tuple(text_decode(i.name) for i in raw_dat_iter)


class RawLevelUpMoveName(Struct, metaclass=StructMeta):
    name: byte[13]


async def get_all_move_names(rom: Rom) -> tuple[str, ...]:
    ptr = Pointer[RawLevelUpMoveName](config.offsets.MOVE_NAME_OFFSET)
    return tuple(text_decode(rom.deref(ptr + i).name) for i in range(config.MOVE_COUNT))


class RawLevelUpMove(Struct, metaclass=StructMeta):
    data: u16


class LevelUpMovePtrStruct(Struct, metaclass=StructMeta):
    ptr: Pointer[RawLevelUpMove]


@data_json
class LevelUpMove:
    move: str
    level: int


def unpack_level_up_move(move_data: int) -> tuple[int, int]:
    move = move_data & 0b00000001_11111111
    level = move_data >> 9
    return move, level


RawMovePtr = Pointer[RawLevelUpMove]


def process_move_array(rom, ptr: RawMovePtr, names: tuple[str]) -> Generator[LevelUpMove, None, None]:
    while (move_data := rom.deref(ptr).data) != 0xFFFF:
        move, level = unpack_level_up_move(move_data)
        ptr += 1
        yield LevelUpMove(move=names[move], level=level)


async def get_all_level_up_moves(rom: Rom, names: tuple[str]) -> tuple[tuple[LevelUpMove], ...]:
    ptr = Pointer[LevelUpMovePtrStruct](config.offsets.LEVEL_UP_MOVE_OFFSET)
    move_array_ptrs = (RawMovePtr(rom.deref(ptr + i).ptr) for i in
                       range(0, config.BONEKA_COUNT))

    return tuple(tuple(process_move_array(rom, ptr, names)) for ptr in move_array_ptrs)


class RawDexText(Struct, metaclass=StructMeta):
    data: byte[128]  # doesn't matter if we overshoot the data. text_decode()
    # will only consider the first valid string by design


RawDexTextPtr = Pointer[RawDexText]


class DexRaw(Struct, metaclass=StructMeta):
    species: byte[12]
    height: u16
    weight: u16
    description: RawDexTextPtr
    description_2: RawDexTextPtr  # no data usually
    unused: u16
    scale: u16
    offset: u16
    trainer_scale: u16
    trainer_offset: u16
    unused_: u16


@data_json
class BonekaDexData:
    species: str
    dex_entry: str


async def get_all_dex_entries(rom: Rom) -> tuple[BonekaDexData, ...]:
    ptr = Pointer[DexRaw](config.offsets.DEX_DATA_OFFSET)
    raw_iter = (rom.deref(ptr + i) for i in range(config.DEX_LENGTH))

    return tuple(
        BonekaDexData(
            *map(text_decode, (raw.species, rom.deref(RawDexTextPtr(raw.description)).data))
        )
        for raw in raw_iter)


async def get_all_ability_names(rom: Rom) -> tuple[str, ...]:
    ptr = Pointer[RawLevelUpMoveName](config.offsets.ABILITY_NAME_OFFSET)
    return tuple(text_decode(rom.deref(ptr + i).name) for i in range(config.ABILITY_TABLE_LEN))


class TypeName(Struct, metaclass=StructMeta):
    name: byte[7]


async def get_all_type_names(rom: Rom) -> tuple[str, ...]:
    ptr = Pointer[TypeName](config.offsets.TYPE_NAMES_OFFSET)
    return tuple(text_decode(rom.deref(ptr + i).name) for i in range(config.TYPE_TABLE_LEN))


@data_json
class BonekaStatData:
    hp: int
    attack: int
    defense: int
    sp_atk: int
    sp_def: int
    speed: int

    type_1: str
    type_2: str

    ability_1: str
    ability_2: str

    @classmethod
    def from_raw(cls, raw: RawBonekaStatData, type_names: tuple[str, ...], ability_names: tuple[str, ...]):
        return BonekaStatData(hp=raw.hp, attack=raw.attack, defense=raw.defense, sp_atk=raw.sp_atk, sp_def=raw.sp_def,
                              speed=raw.speed,
                              type_1=type_names[raw.type_1], type_2=type_names[raw.type_2],
                              ability_1=ability_names[raw.ability_1], ability_2=ability_names[raw.ability_2])


class DexNumber(Struct, metaclass=StructMeta):
    number: u16


async def get_all_dex_numbers(rom: Rom) -> tuple[int, ...]:
    ptr = Pointer[DexNumber](config.offsets.DEX_NUMBERS_OFFSET)
    return tuple(rom.deref(ptr + i).number for i in range(config.BONEKA_COUNT))


@data_json
class Boneka:
    name: str
    stats: BonekaStatData
    level_up_moves: tuple[LevelUpMove, ...]  # [LevelUpMove]
    sprite: Optional[bytes]
    dex_number: int
    dex_data: Optional[BonekaDexData] = None


def convert_boneka_data(names: tuple[str, ...], stats: tuple[RawBonekaStatData, ...],
                        level_up: tuple[tuple[LevelUpMove], ...],
                        sprites: tuple[bytes, ...], dex_numbers: tuple[int, ...],
                        ability_names: tuple[str, ...], type_names: tuple[str, ...]) -> tuple[Boneka]:
    data = zip(names, (BonekaStatData.from_raw(raw, type_names, ability_names) for raw in stats), level_up,
               sprites, (0, *dex_numbers))

    return tuple(Boneka(*dat) for dat in data)


async def get_all_boneka_data(rom: Rom) -> tuple[Boneka, ...]:
    move_names, ability_names, type_names, dex_data = await asyncio.gather(get_all_move_names(rom),
                                                                           get_all_ability_names(rom),
                                                                           get_all_type_names(rom),
                                                                           get_all_dex_entries(rom))
    results = await asyncio.gather(
        get_all_boneka_names(rom),
        get_all_boneka_stats(rom),
        get_all_level_up_moves(rom, move_names),

        # get_all_dex_entries(rom),
        get_all_sprite_data(rom),
        get_all_dex_numbers(rom)
    )
    dat = convert_boneka_data(*results, ability_names, type_names)
    for boneka in dat:
        try:
            boneka.dex_data = dex_data[boneka.dex_number]
        except IndexError:
            pass
    return dat
