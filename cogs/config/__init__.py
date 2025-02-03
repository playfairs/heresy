from main import flesh
from .configuration import Config

async def setup(bot: flesh):
    await bot.add_cog(Config(bot))