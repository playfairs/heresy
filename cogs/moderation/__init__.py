from .moderation import Moderation
from discord.ext import commands

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))