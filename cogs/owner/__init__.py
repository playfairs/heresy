from .owner import Owner
from discord.ext import commands

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))