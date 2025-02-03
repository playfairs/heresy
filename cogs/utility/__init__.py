from .utility import Utility
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(Utility(bot))