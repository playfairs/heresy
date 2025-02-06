from .listeners import Listeners
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(Listeners(bot))