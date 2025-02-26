from .developer import Developer
from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Developer(bot))