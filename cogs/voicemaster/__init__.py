from .voicemaster import VoiceMaster
from main import flesh

async def setup(bot: flesh):
    await bot.add_cog(VoiceMaster(bot))