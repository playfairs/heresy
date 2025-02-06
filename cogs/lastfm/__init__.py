from .lastfm import LastFM
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(LastFM(bot))