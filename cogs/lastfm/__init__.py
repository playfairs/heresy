from .lastfm import LastFM
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(LastFM(bot))