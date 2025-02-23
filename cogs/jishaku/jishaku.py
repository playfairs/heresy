import discord
from discord.ext import commands
from jishaku import __main__
from jishaku import commands as jishaku_commands

from . import information
from main import heresy

class Jishaku(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def reload(self, ctx, *, extension: str):
        """Reloads an extension."""
        await ctx.send(f"Reloading {extension}...")
        try:
            self.bot.unload_extension(f"cogs.{extension}")
            self.bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Reloaded {extension}.")
        except Exception as e:
            await ctx.send(f"Failed to reload {extension}: {e}")