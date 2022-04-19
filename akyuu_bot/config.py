import logging
from functools import lru_cache
from functools import wraps
from typing import ClassVar, Iterable, Type, TypeVar

from attr import define

try:  # allow optional ujson dependency for faster json (not like it's needed)
    from cattr.preconf.ujson import make_converter, UjsonConverter as JsonConverter

except ImportError:
    from cattr.preconf.json import make_converter, JsonConverter

logger = logging.getLogger(__name__)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s:\t%(levelname)s: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

T = TypeVar('T', bound=Iterable['Jsonable'])


class Jsonable:
    converter: ClassVar[JsonConverter] = make_converter()

    def to_json(self, **kwargs) -> str:
        return self.converter.dumps(self, **kwargs)

    @classmethod
    def to_json_list(cls, obj: Iterable['Jsonable'], **kwargs) -> str:
        return cls.converter.dumps(obj, **kwargs)

    @classmethod
    def from_json(cls, json_str: str, **kwargs) -> 'Jsonable':
        return cls.converter.loads(json_str, cls, **kwargs)

    @classmethod
    def from_json_list(cls, json_str: str, tp: Type[T], **kwargs) -> T:
        return cls.converter.loads(json_str, tp, **kwargs)


def class_wraps(cls, wrapped):
    cls.__name__ = wrapped.__name__
    cls.__qualname__ = wrapped.__qualname__
    cls.__doc__ = wrapped.__doc__
    cls.__annotations__ = wrapped.__annotations__

    return cls


def data_json(cls=None, **kwargs):
    """
    Converts a class to an attrs dataclass, but with an api specialized for json serialization and deserialization
    """

    if cls is None:
        @wraps(data_json)
        def wrapper(cls_):
            class H2(define(**kwargs)(cls_), Jsonable):
                pass

            return class_wraps(H2, cls_)

        return wrapper

    class H(define(cls), Jsonable):
        pass

    return class_wraps(H, cls)


class ConfigError(Exception):
    pass


@data_json(auto_attribs=True)
class Offsets:
    SPRITE_OFFSET: int = 0x082350AC
    PALETTE_OFFSET: int = 0x0823730C
    BONEKA_STAT_OFFSET: int = 0x08254784
    BONEKA_NAME_OFFSET: int = 0x08245EE0
    MOVE_NAME_OFFSET: int = 0x08247094
    LEVEL_UP_MOVE_OFFSET: int = 0x0825D7B4  # HMA: data.pokemon.moves.levelup
    DEX_DATA_OFFSET: int = 0x0844E850  # HMA: data.pokedex.stats
    # Contains the raw dex data with species names and entries
    ABILITY_NAME_OFFSET: int = 0x08879280
    TYPE_NAMES_OFFSET: int = 0x0824F1A0
    DEX_NUMBERS_OFFSET: int = 0x08251FEE  # The national dex ordering. HMA: data.pokedex.national

    MAP_BANKS_OFFSET: int = 0x087F1E8C
    MAP_NAMES_OFFSET: int = 0x083F1CAC

    WILD_DATA_OFFSET: int = 0x087D9000


@data_json(auto_attribs=True)
class BotData:
    TOKEN: str
    ROM_PATH: str = 'firered.gba'
    BONEKA_DATA_PATH: str = 'boneka_data.json'
    PATCH_PATH: str = 'patch.ups'

    IGNORE_PARENT_DIR_IN_ZIP_FILE: bool = True
    
    BONEKA_EMBED_COLOR: int = 0xB4528D
    DEV_SERVERS: list[int] = [855529286953467945]
    DEVELOPERS: list[int] = [692981485975633950, 218853068790300674]
    DEV_MODE = True


@data_json(auto_attribs=True)
class Config:
    bot_data: BotData
    offsets: Offsets = Offsets()
    BONEKA_COUNT: int = 412
    MOVE_COUNT: int = 355
    DEX_LENGTH: int = 386
    ABILITY_TABLE_LEN: int = 90  # ability names table length
    TYPE_TABLE_LEN: int = 18  # The table that stores the names for types

    MAP_BANK_COUNT: int = 46  # 42 in vanilla fire red I believe. HMA does not like how there is more map banks
    MAPSECS_KANTO: int = 0x58  # No clue what this is,
    # but the map_header.section_id - MAPSECS_KANTO = the index into the name array
    NUM_MAP_NAMES: int = 109  # NUM_MAP_NAMES = MAPSEC_SPECIAL_AREA - MAPSECS_KANTO + 1,
    # or in HMA, the length of data.maps.names

    WILD_DATA_LEN: int = 172

    # Maybe a hack could change these. Who knows?
    NUM_GRASS_ENCOUNTER_SLOTS: int = 12
    NUM_SURF_ENCOUNTER_SLOTS: int = 5
    NUM_TREE_ENCOUNTER_SLOTS: int = 5
    NUM_FISH_ENCOUNTER_SLOTS: int = 10


@lru_cache
def get_config():
    try:
        with open('akyuu.json') as f:
            conf_str = f.read()
            conf = Config.from_json(conf_str)
            return conf
    except FileNotFoundError:
        logger.error(
            "Could not find a valid akyuu.json file.")
        with open('akyuu.json', 'w+') as f:
            default_config = Config(bot_data=BotData(TOKEN=""))
            print(default_config.to_json(indent=4), file=f)
        raise ConfigError("No config file. A new config file should have been created. "
                          "Modify the config and start the bot again") from None


config: Config = get_config()  # temporarily until actual config system is implemented
