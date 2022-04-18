from typing import Type, Optional

import interactions
from interactions.api.models.flags import Intents
import interactions.ext.wait_for as wait_for

from ..config import config, logger, ConfigError, Config
from ..rom_api.rom import Rom
from ..rom_api.stats import get_all_boneka_data, Boneka
from ..rom_api.wild_data import get_all_wild_data, WildLocation
from ..ups_wrapper import UpsPatch

SCOPE = config.bot_data.DEV_SERVERS if config.bot_data.DEV_MODE else None


class AkyuuBot(interactions.Client):
    extensions: list[str] = []
    listener = interactions.api.dispatch.Listener()

    def __init__(self, **kwargs):
        super().__init__(token=config.bot_data.TOKEN, intents=Intents.DEFAULT | Intents.GUILD_MESSAGE_CONTENT, **kwargs)

        self.config: Config = config
        self.boneka_data = self.wild_data = None

        logger.debug("Adding extensions")
        for ext in self.extensions:
            self.load(ext)
            logger.debug(f"Added extension {ext!r}")

        logger.debug("Registering ON_READY listener")
        self.listener.register(self.on_ready, name="ON_READY")
        self.listener.dispatch("ON_READY")
        wait_for.setup(self, True)

    @staticmethod
    def get_patch() -> bytes:
        logger.debug("Getting patch")
        patch_path = config.bot_data.PATCH_PATH
        try:
            with open(patch_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise ConfigError(f"No patch file found at {patch_path!r}. Change PATCH_PATH in the config") from None

    @staticmethod
    def get_rom() -> bytes:
        logger.debug("Getting rom")
        rom_path = config.bot_data.ROM_PATH
        try:
            with open(rom_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise ConfigError(f"No patch file found at {rom_path!r}. Change ROM_PATH in the config") from None

    def write_boneka_data(self):
        boneka_data_path = config.bot_data.BONEKA_DATA_PATH
        logger.debug(f"Writing Boneka data to {boneka_data_path!r}.")

        with open(boneka_data_path, 'w+') as f:
            f.write(
                Boneka.to_json_list(self.boneka_data, indent=4)
            )

    async def update_patch(self, rom: bytes, patch: bytes, *, update_patch_file: bool = True):
        logger.debug("Updating patch data")
        ups_patch = UpsPatch(patch)

        patched_rom = Rom(ups_patch.apply(rom))

        self.boneka_data = await get_all_boneka_data(patched_rom)
        self.wild_data = await get_all_wild_data(patched_rom, self.boneka_data)
        with open('wild.json', 'w+') as f:
            f.write(WildLocation.to_json_list(self.wild_data, indent=4))
        self.write_boneka_data()

        if update_patch_file:
            logger.debug('Updating patch file')
            with open(config.bot_data.PATCH_PATH, 'wb') as f:
                f.write(patch)
        logger.debug("Patch data update was successful!")


    async def on_ready(self):
        logger.info(f"Successfully logged on as {self.me.name}")
        if self.boneka_data is None:
            await self.update_patch(self.get_rom(), self.get_patch(), update_patch_file=False)

    async def wait_for(self, event: Optional[str] = None, *, check=None, timeout: int = 15):
        # overridden by the wait_for setup
        pass

    @property
    def http(self):
        return self._http

    @property
    def lower_boneka_names(self) -> tuple[str, ...]:
        return tuple(boneka.name.lower() for boneka in self.boneka_data)

    async def wait_for_component(self, components, *, check=None, timeout: int = 15):
        # overridden by the wait_for setup
        pass


def akyuu_ext(cls) -> Type:
    logger.debug(f"Found extension {cls.__module__!r}")
    modname = cls.__module__
    AkyuuBot.extensions.append(modname)
    return cls
