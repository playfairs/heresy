from main import Heresy
from .configuration import Config

async def setup(bot: Heresy):
    await bot.add_cog(Config(bot))