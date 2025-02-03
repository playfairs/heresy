from .lore import Lore
from discord.ext import commands
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(Lore(bot))