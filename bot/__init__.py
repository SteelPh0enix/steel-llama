from discord.ext import commands
from bot.configuration import Config


class Bot(commands.Bot):
    def __init__(self, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.config = config
