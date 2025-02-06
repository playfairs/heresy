from main import heresy
from .configuration import Config

async def setup(bot: heresy):
    await bot.add_cog(Config(bot))