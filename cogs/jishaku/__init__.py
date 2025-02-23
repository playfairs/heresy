from .jishaku import Jishaku
from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Jishaku(bot))