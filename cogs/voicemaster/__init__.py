from .voicemaster import VoiceMaster
from main import heresy

async def setup(bot: heresy):
    await bot.add_cog(VoiceMaster(bot))