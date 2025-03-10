from .fun import Fun, Porn
from discord.ext import commands

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
    await bot.add_cog(Porn(bot))