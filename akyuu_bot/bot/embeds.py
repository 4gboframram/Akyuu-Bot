from io import BytesIO
from typing import Sequence

from interactions.api.models.message import Embed, EmbedImageStruct, EmbedAuthor, EmbedField, Attachment

from ..rom_api.stats import Boneka, BonekaDexData
from ..config import config
from ..rom_api.wild_data import WildLocation


class BaseEmbed(Embed):
    _fields: list[EmbedField]

    def add_field(self, name: str, value: str, inline: bool):
        self._fields.append(EmbedField(name=name, value=value, inline=inline))


class BonekaStatEmbed(BaseEmbed):
    """
    Creates an embed that represents boneka data. When sending, remember to send the file too!
    """

    def __init__(self, boneka: Boneka):
        self._fields = []

        author = EmbedAuthor(name="")
        if boneka.dex_data is not None:
            self.description = boneka.dex_data.dex_entry
            author = EmbedAuthor(name=boneka.dex_data.species + " Boneka")
        else:
            self.description = "OUT OF DEX"

        sprite_file_name = f'{boneka.name.lower()}_sprite.png'

        # self.file = Attachment(fp=BytesIO(boneka.sprite), filename=sprite_file_name)
        # im = EmbedImageStruct(url=f"attachment:/{sprite_name}")

        # Type Field

        types = ' / '.join({boneka.stats.type_1, boneka.stats.type_2})
        self.add_field("Typing", types, False)

        # Abilities field

        abilities = ', '.join({boneka.stats.ability_1, boneka.stats.ability_2})
        think_about_singular = "Ability" if len(abilities) <= 1 else "Abilities"
        self.add_field(name=think_about_singular, value=abilities, inline=False)

        # Stats Fields
        self.add_field("Base Stats", "\u200b", False)
        self.add_stat("HP", boneka.stats.hp)
        self.add_stat("Atk", boneka.stats.attack)
        self.add_stat("Def", boneka.stats.defense)
        self.add_stat("Sp. Atk", boneka.stats.sp_atk)
        self.add_stat("Sp. Def", boneka.stats.sp_def)
        self.add_stat("Spd", boneka.stats.speed)

        # Init super

        super().__init__(title=boneka.name, color=config.bot_data.BONEKA_EMBED_COLOR, author=author, fields=self._fields,
                         description=self.description  # image=im
                         )

    def add_stat(self, name, value: int):
        self.add_field(name=name, value=str(value), inline=True)


class BonekaLevelupMoveEmbed(BaseEmbed):

    def __init__(self, boneka: Boneka):
        self._fields = []
        self.boneka = boneka

        author = EmbedAuthor(name="")
        if boneka.dex_data is not None:
            self.description = boneka.dex_data.dex_entry
            author = EmbedAuthor(name=boneka.dex_data.species + " Boneka")
        else:
            self.description = "OUT OF DEX"

        sprite_file_name = f'{boneka.name.lower()}_sprite.png'

        # self.file = Attachment(fp=BytesIO(boneka.sprite), filename=sprite_file_name)
        # im = EmbedImageStruct(url=f"attachment:/{sprite_name}")

        self.add_field("Levelup Moves", "\u200b", False)  # abuse zero-width space
        self.add_level_up_moves()

        super().__init__(title=boneka.name, color=config.bot_data.BONEKA_EMBED_COLOR, author=author, fields=self._fields,
                         description=self.description  # image=im
                         )

    def add_level_up_moves(self):
        for move in self.boneka.level_up_moves:
            self.add_field(move.move, str(move.level), True)


class BonekaWildLocationsEmbed(BaseEmbed):
    def __init__(self, boneka: Boneka, grass: Sequence[WildLocation], surf: Sequence[WildLocation],
                 tree: Sequence[WildLocation], fish: Sequence[WildLocation]):
        self._fields = []
        author = EmbedAuthor(name="")
        if boneka.dex_data is not None:
            self.description = boneka.dex_data.dex_entry
            author = EmbedAuthor(name=boneka.dex_data.species + " Boneka")
        else:
            self.description = "OUT OF DEX"

        self.add_field('Grass Locations', ', '.join(g.name for g in grass), False) if grass else None
        self.add_field('Surf Locations', ', '.join(g.name for g in surf), False) if surf else None
        self.add_field('Tree Locations', ', '.join(g.name for g in tree), False) if tree else None
        self.add_field('Fishing Locations', ', '.join(g.name for g in fish), False) if fish else None

        super().__init__(fields=self._fields, description=self.description,
                         author=author, color=config.bot_data.BONEKA_EMBED_COLOR, title=boneka.name)



