from .automod import Automod

async def setup(bot):
    await bot.add_cog(Automod(bot))