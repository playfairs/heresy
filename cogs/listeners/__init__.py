from .listeners import Listeners
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(Listeners(bot))