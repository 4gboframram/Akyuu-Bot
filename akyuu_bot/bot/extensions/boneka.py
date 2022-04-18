import asyncio

import interactions
from interactions import extension_command, Option, OptionType

from .ext import BaseExtension
from ..akyuu import SCOPE, akyuu_ext
from ..embeds import BonekaStatEmbed, BonekaLevelupMoveEmbed, BonekaWildLocationsEmbed
from ...rom_api.stats import Boneka
from ...rom_api.wild_data import WildLocation


async def delete_if_possible(msg):
    try:
        await msg.delete()
    except TypeError:
        pass


@akyuu_ext
class BonekaExt(BaseExtension):
    _boneka_command_options = [
        interactions.SelectOption(
            label="Stats",
            value="stats",
            description="Get this boneka's stats"
        ),
        interactions.SelectOption(
            label="Levelup moves",
            value="moves",
            description="Get information of what moves a this boneka learns"
        ),
        interactions.SelectOption(
            label="Locations",
            value="locate",
            description="Get information on where you can find this boneka in the wild"
        ),

    ]

    def get_boneka_data(self, name: str) -> list[Boneka]:  # no cache because data could update while the bot is running
        return [dat for dat in self.bot.boneka_data if dat.name.lower() == name.lower()]

    def get_wild_locations(self, name: str) -> tuple[list[WildLocation], list[WildLocation],
                                                     list[WildLocation], list[WildLocation]]:
        grass = []
        surf = []
        tree = []
        fish = []
        name = name.lower()
        for loc in self.bot.wild_data:
            try:
                if name in (i.boneka.lower() for i in loc.grass):
                    grass.append(loc)
            except TypeError:
                pass
            try:
                if name in (i.boneka for i in loc.surf):
                    surf.append(loc)
            except TypeError:
                pass
            try:
                if name in (i.boneka.lower() for i in loc.tree):
                    tree.append(loc)
            except TypeError:
                pass
            try:
                if name in (i.boneka.lower() for i in loc.fish):
                    fish.append(loc)
            except TypeError:
                pass

        return grass, surf, tree, fish

    @extension_command(name="stats", description="Get base stats and abilities for a boneka.", scope=SCOPE,
                       options=[
                           Option(
                               name="boneka",
                               description="The boneka to get stats for",
                               type=OptionType.STRING,
                               required=True,
                           )
                       ])
    async def stats(self, ctx, boneka: str, *, ephemeral: bool = False):
        boneka_dat = self.get_boneka_data(boneka)
        if not boneka_dat:
            await ctx.send(f"{boneka.title()!r} does not exist!", ephemeral=ephemeral)
            return

        b, = boneka_dat

        embed = BonekaStatEmbed(b)

        # files not implemented yet
        await ctx.send(embeds=[embed],  # , files=[embed.file]
                       ephemeral=ephemeral)

    @extension_command(name="levelup", description="Get levelup moves for a boneka", scope=SCOPE,
                       options=[
                           Option(
                               name="boneka",
                               description="The boneka to get stats for",
                               type=OptionType.STRING,
                               required=True,
                           )
                       ])
    async def levelup(self, ctx, boneka: str, *, ephemeral: bool = False):
        boneka_dat = self.get_boneka_data(boneka)
        if not boneka_dat:
            await ctx.send(f"{boneka.title()!r} does not exist!", ephemeral=True)
            return

        b, = boneka_dat

        embed = BonekaLevelupMoveEmbed(b)
        await ctx.send(embeds=[embed], ephemeral=ephemeral  # , files=[embed.file]
                       )

    @extension_command(name="locate", description="Find AWR locations for a boneka", scope=SCOPE,
                       options=[
                           Option(
                               name="boneka",
                               description="The boneka to get stats for",
                               type=OptionType.STRING,
                               required=True,
                           )
                       ])
    async def locate(self, ctx, boneka: str, *, ephemeral: bool = False):
        boneka_dat = self.get_boneka_data(boneka)
        if not boneka_dat:
            await ctx.send(f"{boneka.title()!r} does not exist!", ephemeral=True)
            return
        b, = boneka_dat
        boneka_locs = self.get_wild_locations(boneka)
        embed = BonekaWildLocationsEmbed(b, *boneka_locs)
        await ctx.send(embeds=[embed], ephemeral=ephemeral)

    @extension_command(
        type=interactions.ApplicationCommandType.MESSAGE,
        name="Get Boneka Data",
        scope=SCOPE
    )
    async def get_info(self, ctx):
        words = ctx.target.content.lower().split()

        boneka_in_message = [i for i in self.bot.boneka_data if i.name.lower() in words]
        if not boneka_in_message:
            await ctx.send("No boneka found", ephemeral=True)
            return

        options = [
            interactions.SelectOption(
                label=boneka.name,
                value=boneka.name,
                description=boneka.dex_data.dex_entry[:100] if boneka.dex_data is not None else 'OUT OF DEX'
            ) for boneka in boneka_in_message
        ]
        menu = interactions.SelectMenu(
            options=options,
            placeholder='Which boneka should I tell you about?',
            custom_id='boneka_find_menu'
        )
        row = interactions.ActionRow(
            components=[menu]
        )
        msg = await ctx.send(components=row, ephemeral=True)

        try:

            menu_ctx = await self.bot.wait_for_component(
                components=options, timeout=15
            )

            boneka_name = menu_ctx.data.values[0]
            command_menu = interactions.SelectMenu(
                options=self._boneka_command_options,
                placeholder=f"What I should I tell you about {boneka_name}?",
                custom_id='command_menu'
            )
            command_row = interactions.ActionRow(
                components=[command_menu]
            )
            await menu_ctx.edit(components=command_row)
            try:

                command_menu_ctx = await self.bot.wait_for_component(
                    components=self._boneka_command_options, timeout=15
                )
                selected_command = command_menu_ctx.data.values[0]

                if selected_command == 'stats':
                    await self.stats(command_menu_ctx, boneka_name, ephemeral=True)
                elif selected_command == 'moves':
                    await self.levelup(command_menu_ctx, boneka_name, ephemeral=True)
                elif selected_command == 'locate':
                    await self.locate(command_menu_ctx, boneka_name, ephemeral=True)

                await delete_if_possible(msg)
            except asyncio.TimeoutError:
                await delete_if_possible(msg)
        except asyncio.TimeoutError:
            await delete_if_possible(msg)


def setup(client):
    BonekaExt(client)
