from .bot.akyuu import AkyuuBot
from .config import logger
from .bot.extensions import sanity, boneka, dev_commands, help
# run all the extensions to add them to the bot


if __name__ == '__main__':
    logger.info("Starting Akyuu Bot")
    bot = AkyuuBot()
    bot.start()
