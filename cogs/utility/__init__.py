from .utility import Utility
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(Utility(bot))