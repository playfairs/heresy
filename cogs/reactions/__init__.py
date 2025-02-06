from .reactions import Reactions
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(Reactions(bot))