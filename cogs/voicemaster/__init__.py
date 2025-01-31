from .voicemaster import VoiceMaster
from main import Heresy

async def setup(bot: Heresy):
    await bot.add_cog(VoiceMaster(bot))