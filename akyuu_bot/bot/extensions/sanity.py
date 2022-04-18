from .ext import BaseExtension
from ..akyuu import akyuu_ext, SCOPE
from interactions import extension_command


@akyuu_ext
class SanityCheck(BaseExtension):

    @extension_command(name="ping", description="Pong?", scope=SCOPE)
    async def ping(self, ctx):
        await ctx.send(f'Pong? ({self.bot.latency:.2f}ms)')


def setup(client):
    SanityCheck(client)
