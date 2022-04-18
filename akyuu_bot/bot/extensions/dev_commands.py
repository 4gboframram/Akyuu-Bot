import asyncio
import traceback
from copy import copy
from functools import wraps
from io import BytesIO
from pathlib import Path
from typing import Optional
from zipfile import ZipFile, Path as ZipPath

import interactions
from attrs import fields_dict
from interactions import extension_command, Message, Attachment

from .ext import BaseExtension
from ..akyuu import akyuu_ext, SCOPE
from ...config import config, logger, Config
from ...util.async_mega import AsyncMega, AsyncBase


def report_error(cmd):
    """
    A decorator to provide error tracing in dev commands
    :param cmd:
    :return:
    """

    @wraps(cmd)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            await cmd(self, ctx, *args, **kwargs)
        except Exception as e:
            msg = f"""
            Oops... An error has occurred when executing a command.
            ```
            {''.join(traceback.format_exception(None, e, e.__traceback__)).replace(str(Path.home()), 'USER_DIR')}
            ```
            """

            await ctx.send(msg)
            raise e

    return wrapper


def is_dev(ctx):
    return int(ctx.author.id) in config.bot_data.DEVELOPERS


def dev_only_cmd(cmd):
    @wraps(cmd)
    async def wrapper(self, ctx, *args, **kwargs):
        if not is_dev(ctx):
            return await ctx.send('You do not have permission to do that.', ephemeral=True)
        return await cmd(self, ctx, *args, **kwargs)

    return wrapper


def original_sender(ctx):
    """
    Returns callable that checks if the command
    :param ctx:
    :return:
    """

    async def check(msg):
        return int(msg.author.id) == int(ctx.author.user.id)

    return check


def original_sender_and_has_attachment(ctx):
    async def check(msg):
        return await original_sender(ctx)(msg) and msg.attachments

    return check


@akyuu_ext
class DevExt(BaseExtension):

    @extension_command(
        name="update",
        description="(dev) Update the patched rom the bot uses",
        scope=SCOPE,
        options=[
            interactions.Option(
                type=interactions.OptionType.STRING,
                name="source",
                description="Where to get the patch from",
                required=True,
                choices=[
                    interactions.Choice(
                        name="mega",
                        value="mega"
                    ),
                    interactions.Choice(
                        name="discord",
                        value="discord"
                    )
                ],
            )
        ],
    )
    @report_error
    @dev_only_cmd
    async def update_patch(self, ctx: interactions.CommandContext, source: str):
        patch: Optional[bytes] = None

        if source == 'discord':
            patch = await self.get_patch_from_attachment(ctx)
            rom = self.bot.get_rom()
            await self.bot.update_patch(rom, patch, update_patch_file=True)
            await ctx.send("All data has been updated successfully!")
        elif source == 'mega':
            modal = interactions.Modal(
                title="File",
                custom_id="mega_input",
                components=[
                    interactions.TextInput(
                        style=interactions.TextStyleType.SHORT,
                        label="Mega link for patch. Should be a zip file.",
                        custom_id="config_file_input",
                    ),
                    interactions.TextInput(
                        style=interactions.TextStyleType.SHORT,
                        label="Path to the patch in the zip file.",
                        custom_id="path_in_zip",
                    )
                ],
            )
            await ctx.popup(modal)

    @staticmethod
    async def get_patch_from_zipped_file(patch_file: AsyncBase, patch_path: str):
        logger.debug("Getting patch from file")
        raw = await patch_file.read()

        data = BytesIO(raw)

        with ZipFile(data, 'r') as f:
            path: Optional[ZipPath] = None

            if config.bot_data.IGNORE_PARENT_DIR_IN_ZIP_FILE:
                parent_dir = f.infolist()[0].filename
                parent_folder = ZipPath(f, parent_dir)
                path = (parent_folder / patch_path)
            else:
                path = ZipPath(patch_path)

            return path.read_bytes()

    async def get_attachment_data(self, attachment: Attachment) -> bytes:
        async with self.bot.http.req._session.get(attachment.url) as resp:  # access the bot's underlying http client
            return await resp.read()

    async def get_patch_from_attachment(self, ctx):
        await ctx.send("Send the patch file here.")
        try:
            msg: Message = await self.bot.wait_for("on_message_create",
                                                   check=original_sender_and_has_attachment(ctx), timeout=120)
            attachment = msg.attachments[0]
            return await self.get_attachment_data(attachment)
        except asyncio.TimeoutError:
            return await ctx.send("Took too long.", ephemeral=True)

    @interactions.extension_modal('mega_input')
    async def _mega_download(self, ctx, link: str, path_in_zip: str):
        await ctx.defer()
        logger.debug(f"Getting patch from {link}")
        async with AsyncMega() as mega:
            await mega.async_login_anonymous()
            patch_file = await mega.async_download_public_url(link)
            await patch_file.seek(0)

        patch = await self.get_patch_from_zipped_file(patch_file, path_in_zip)
        rom = self.bot.get_rom()
        await self.bot.update_patch(rom, patch, update_patch_file=True)
        await ctx.send("All data has been updated successfully!")

    async def _config_set(self, ctx: interactions.CommandContext):
        modal = interactions.Modal(
            title="Config",
            custom_id="config_modal",
            components=[interactions.TextInput(
                style=interactions.TextStyleType.PARAGRAPH,
                label="Set bot config?",
                custom_id="config_input",
            )],
        )

        await ctx.popup(modal)

    @extension_command(
        name="config",
        description="(dev) View or set bot configuration",
        scope=SCOPE,
        options=[
            interactions.Option(
                type=interactions.OptionType.STRING,
                name="action",
                description="what to do to the config",
                required=True,
                choices=[
                    interactions.Choice(
                        name="show",
                        value="show"
                    ),
                    interactions.Choice(
                        name="set",
                        value="set"
                    )
                ],
            )
        ],

    )
    @report_error
    @dev_only_cmd
    async def config(self, ctx, action: str):
        if action == 'show':
            tok = config.bot_data.TOKEN
            config.bot_data.TOKEN = 'Go touch grass'

            await ctx.send(
                f"```json\n{config.to_json(indent=4)}```", ephemeral=True
            )
            config.bot_data.TOKEN = tok
        elif action == 'set':
            await self._config_set(ctx)

    @interactions.extension_modal(modal="config_modal")
    @report_error
    @dev_only_cmd
    async def config_resp(self, ctx, response: str):

        old_config = copy(config)
        new_config = Config.from_json(response)
        try:
            for attr in fields_dict(type(config)):
                setattr(config, attr, getattr(new_config, attr))
            config.bot_data.TOKEN = old_config.bot_data.TOKEN
            await self.bot.update_patch(self.bot.get_rom(), self.bot.get_patch(), update_patch_file=False)
            with open('akyuu.json', 'w+') as f:
                f.write(config.to_json(indent=4))
            await ctx.send(f"New config: ```json\n{response}```", ephemeral=True)

        except Exception as e:
            for attr in fields_dict(type(config)):
                setattr(config, attr, getattr(old_config, attr))
            await self.bot.update_patch(self.bot.get_rom(), self.bot.get_patch(), update_patch_file=False)
            await ctx.send("Could not apply new config... Undoing changes...", ephemeral=True)
            raise e


def setup(client):
    DevExt(client)
