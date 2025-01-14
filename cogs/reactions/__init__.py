from .reactions import Reactions
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(Reactions(bot))