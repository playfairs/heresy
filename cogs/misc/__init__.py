from main import Heresy
from .misc import Misc

async def setup(bot: Heresy):
    await bot.add_cog(Misc(bot))