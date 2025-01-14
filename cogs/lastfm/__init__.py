from .lastfm import LastFM
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(LastFM(bot))