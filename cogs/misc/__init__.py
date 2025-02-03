from main import flesh
from .misc import Misc

async def setup(bot: flesh):
    await bot.add_cog(Misc(bot))