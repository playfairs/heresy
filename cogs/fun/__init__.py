from .fun import Fun
from discord.ext import commands

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))