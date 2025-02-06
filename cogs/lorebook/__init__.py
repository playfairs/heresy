from .lore import Lore
from discord.ext import commands
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(Lore(bot))