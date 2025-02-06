from main import heresy
from .misc import Misc

async def setup(bot: heresy):
    await bot.add_cog(Misc(bot))