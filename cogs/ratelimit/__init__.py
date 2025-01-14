from .ratelimit import RateLimit
from aiolimiter import AsyncLimiter

async def setup(bot):
    await bot.add_cog(RateLimit(bot))
