from .music import AppleMusic, Playlist

async def setup(bot):
    await bot.add_cog(AppleMusic(bot))
    await bot.add_cog(Playlist(bot))