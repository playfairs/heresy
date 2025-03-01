import discord
from discord import ui
from discord.ui import View, Button, interface, Modal

class AntiNukeInterface(View):
    def __init__(self):
        super().__init__(timeout=120)

    @