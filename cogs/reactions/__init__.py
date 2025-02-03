from .reactions import Reactions
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(Reactions(bot))