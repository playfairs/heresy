from .listeners import Listeners
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(Listeners(bot))