from ..akyuu import akyuu_ext, SCOPE
from .ext import BaseExtension
import interactions


@akyuu_ext
class HelpExt(BaseExtension):

    @interactions.extension_command(name="help", description="Get bot help", scope=SCOPE)
    async def help(self, ctx):
        button = interactions.Button(
            style=interactions.ButtonStyle.LINK,
            label="Github Repository",
            url="https://github.com/4gboframram/Akyuu-Bot"
        )
        embed = interactions.Embed(
            title="Help",
            description="Check out the documentation on Github by clicking this button",
            color=0x518FFF
        )
        await ctx.send(components=[button], embeds=[embed])


def setup(client):
    HelpExt(client)