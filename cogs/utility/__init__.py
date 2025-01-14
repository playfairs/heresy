from .utility import Utility
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(Utility(bot))