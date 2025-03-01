import requests
import asyncpg
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, group, tasks, ui
from discord.ui import View, Button, interface, Modal

from .classes import AntiNukeInterface


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @group(name="antinuke", description="Base command for Antinuke", invoke_without_command=True)
    async def antinuke(self, interaction: discord.Interaction):
        await interaction.response.send_message("Antinuke Panel", ephemeral=True)