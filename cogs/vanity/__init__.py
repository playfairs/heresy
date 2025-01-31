from .vanity import Vanity
from discord.ext.commands import Bot

async def setup(bot: Bot):
    await bot.add_cog(Vanity(bot))