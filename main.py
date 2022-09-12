from logging import INFO
from logging import StreamHandler
from logging import basicConfig as logging_basicConfig
from logging import getLogger

from discord import Intents
from discord.ext.commands import Bot

from env import TOKEN

logging_basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="{asctime} | {levelname: <8} | {name: <16} | {message}",
    handlers=[
        StreamHandler()],
        # TimedRotatingFileHandler("logs/active_log.txt", utc=True, when="midnight", backupCount=14)],
    level=INFO,
    style="{")
logger = getLogger(__name__)


class MultiClone(Bot):

    def __init__(self):

        super().__init__(
            command_prefix="",
            help_command=None,
            intents=Intents(
                guilds=True))

        self.key_channel = {}
        self.key_guild = {}

        self.user_key = {}
        self.key_user = {}
        self.expiry_key = {}

    async def setup_hook(self) -> None:

        for ext in ("copy", "paste"):
            await self.load_extension(f"bot.{ext}")
        # await self.tree.sync()


multiclone = MultiClone()
multiclone.run(TOKEN, log_handler=None)
