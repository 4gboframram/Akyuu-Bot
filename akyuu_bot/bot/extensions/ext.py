from interactions import Extension
from ..akyuu import AkyuuBot


class BaseExtension(Extension):
    """
    A base class for an extension. Just has some boilerplate code
    """
    def __init__(self, bot: AkyuuBot):
        self.bot = bot
