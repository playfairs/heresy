from discord.ext import commands
from aiolimiter import AsyncLimiter
import asyncio
import aiohttp

class RateLimit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.limiter = AsyncLimiter(max_rate=300, time_period=60)
        self.is_paused = False
        self.requests_made = 0

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            if "429" in str(error) or "rate limit" in str(error).lower():
                self.is_paused = True
                await ctx.send("```py\nRateLimit: Bot is cooling down. Commands will resume shortly.```")
                await asyncio.sleep(60)
                self.is_paused = False
                self.requests_made = 0
                return

    @commands.Cog.listener()
    async def on_command(self, ctx):
        if self.is_paused:
            await ctx.send("```py\nRateLimit: Bot is currently cooling down from rate limits. Please wait.```")
            raise commands.CommandError("Rate limit cooldown")
        
        await self.limiter.acquire()
        self.requests_made += 1

    async def check_rate_limit(self):
        """Check if we're approaching rate limit"""
        if self.requests_made >= (self.limiter.max_rate * 0.8):
            return True
        return False

    @commands.command(name="limit")
    async def test_ratelimit(self, ctx):
        """Test the rate limit functionality"""
        try:
            message = await ctx.send("Testing rate limit... Sending 10 rapid requests")
            
            for i in range(10):
                await self.limiter.acquire()
                self.requests_made += 1
                await message.edit(content=f"Request {i+1}/10 completed\nRequests made: {self.requests_made}/{self.limiter.max_rate}")
                await asyncio.sleep(0.1)
            
            is_limited = await self.check_rate_limit()
            
            if is_limited:
                await ctx.send("```py\nWarning: Approaching rate limit. Cooldown may be needed soon.```")
            else:
                await ctx.send(f"```py\nRate limit test completed successfully.\nRequests made: {self.requests_made}/{self.limiter.max_rate} per {self.limiter.time_period}s```")
                
        except Exception as e:
            await ctx.send(f"```py\nError during rate limit test: {type(e).__name__}: {str(e)}```")

