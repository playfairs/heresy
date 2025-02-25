# use this files to add developer commands

import discord
from discord.ext import commands
import os
import jishaku
import random
import string

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.version = "v5.1.0"
        self.discord_version = discord.__version__
        self.jishaku_version = jishaku.__version__

    @commands.command(name="patch")
    @commands.has_permissions(manage_guild=True)
    async def patch(self, ctx):
        """Sends the patch update from the patch.txt file with role mention."""
        patch_file_path = os.path.join("cogs", "developer", "patch", "patch.md")

        if not os.path.exists(patch_file_path):
            await ctx.send("No patch notes are available at the moment.")
            await ctx.message.delete()
            return

        with open(patch_file_path, "r") as file:
            patch_notes = file.read()

        role = discord.utils.get(ctx.guild.roles, name="Heresy Updates")
        if role is None:
            await ctx.send("Role not found.")
            await ctx.message.delete()
            return

        embed = discord.Embed(
            title=f"**{self.version} Patch Update**",
            description=patch_notes,
            color=0xffffff
        )
        embed.set_footer(
            text=f"heresy {self.version} • discord.py {self.discord_version} • Jishaku {self.jishaku_version}"
        )
        embed.set_thumbnail(url="https://playfairs.cc/heresy.png")

        await ctx.send(content=role.mention, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        await ctx.message.delete()

    @commands.command(name="hotfix")
    @commands.has_permissions(manage_guild=True)
    async def hotfix(self, ctx):
        """Sends the hotfix update from the hotfix.txt file with role mention."""
        hotfix_file_path = os.path.join("cogs", "developer", "patch", "hotfix.md")

        if not os.path.exists(hotfix_file_path):
            await ctx.send("No hotfix notes are available at the moment.")
            await ctx.message.delete()
            return

        try:
            with open(hotfix_file_path, "r", encoding="utf-8") as file:
                patch_notes = file.read()
        except UnicodeDecodeError as e:
            await ctx.send(f"Failed to read the hotfix file due to encoding issues: {str(e)}")
            await ctx.message.delete()
            return

        role = discord.utils.get(ctx.guild.roles, name="Heresy Updates")
        if role is None:
            await ctx.send("Role not found.")
            await ctx.message.delete()
            return

        embed = discord.Embed(
            title=f"**{self.version} Hotfix**",
            description=patch_notes,
            color=0x3498db
        )
        embed.set_footer(
            text=f"heresy {self.version} • discord.py {self.discord_version} • Jishaku {self.jishaku_version}"
        )
        embed.set_thumbnail(url="https://playfairs.cc/heresy.png")

        await ctx.send(content=role.mention, embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        await ctx.message.delete()

    @commands.command(name='self_destruct')
    async def self_destruct(self, ctx):
        embed = discord.Embed(title="Warning!", description="Running this command is extremely dangerous, as this will delete all the bots cogs, and archive the repository, are you sure you want to continue?", color=0xff0000)
        yes_button = discord.ui.Button(label="Yes", style=discord.ButtonStyle.green)
        no_button = discord.ui.Button(label="No", style=discord.ButtonStyle.red)

        async def yes_callback(interaction: discord.Interaction):
            await interaction.message.delete()
            await interaction.channel.send("nigga really thought I would delete myself")

        async def no_callback(interaction: discord.Interaction):
            await interaction.message.delete()
            await interaction.channel.send("Good boy")

        yes_button.callback = yes_callback
        no_button.callback = no_callback

        await ctx.send(embed=embed, view=discord.ui.View().add_item(yes_button).add_item(no_button))

    @commands.command(name='nitro')
    async def nitro(self, ctx):
        troll_link = "https://discord.gift/" + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        await ctx.send(f"Here is your Nitro gift link: {troll_link}")


async def setup(bot):
    await bot.add_cog(Developer(bot))
