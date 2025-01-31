from .information import Information
from discord.ext import commands

async def setup(bot: commands.Bot):
    await bot.add_cog(Information(bot))