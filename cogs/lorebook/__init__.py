from .lore import Lore
from discord.ext import commands
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(Lore(bot))