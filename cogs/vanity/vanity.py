import os
import discord
import json
import asyncio

from discord.ext import commands,tasks
from discord.ext.commands import Cog, Bot, group, has_permissions

CONFIG_FILE = "config.json"

class Vanity(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()

    def load_config(self):
        default_config = {
            "servers": {}
        }
        
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config
            
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

                if "servers" not in config:
                    config["servers"] = {}
                return config
        except json.JSONDecodeError:
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    @group(name="vanity", invoke_without_command=True)
    async def vanity_group(self, ctx):
        """Group of commands to manage vanity settings."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @vanity_group.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_vanity(self, ctx, *, vanity: str):
        """Set the vanity keyword for the server."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config["servers"]:
            self.config["servers"][guild_id] = {}

        self.config["servers"][guild_id]["vanity"] = vanity
        self.save_config()
        await ctx.send(f"Vanity keyword set to `{vanity}` for this server.")

    @vanity_group.command(name="role")
    @commands.has_permissions(administrator=True)
    async def set_pic_role(self, ctx, role: discord.Role):
        """Set the pic permissions role for the server."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config["servers"]:
            self.config["servers"][guild_id] = {}

        self.config["servers"][guild_id]["pic_role"] = role.id
        self.save_config()
        await ctx.send(f"Pic permissions role set to `{role.name}`.")

    @vanity_group.command(name="logs")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Set the log channel for vanity updates."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config["servers"]:
            self.config["servers"][guild_id] = {}

        self.config["servers"][guild_id]["log_channel"] = channel.id
        self.save_config()
        await ctx.send(f"Log channel set to `{channel.name}`.")

    @tasks.loop(seconds=2)
    async def check_vanity_statuses(self):
        """Check all members' custom statuses every 2 seconds."""
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            if guild_id not in self.config["servers"]:
                continue

            settings = self.config["servers"][guild_id]
            vanity = settings.get("vanity", "/vanity")
            pic_role_id = settings.get("pic_role")
            log_channel_id = settings.get("log_channel")

            if not pic_role_id or not log_channel_id:
                continue

            role = guild.get_role(pic_role_id)
            log_channel = self.bot.get_channel(log_channel_id)

            if not role or not log_channel:
                continue

            for member in guild.members:
                if member.bot:
                    continue

                has_vanity = any(
                    isinstance(activity, discord.CustomActivity) and 
                    vanity in str(activity.name or "")
                    for activity in member.activities
                )

                try:
                    if has_vanity and role not in member.roles:
                        await member.add_roles(role)
                        embed = discord.Embed(
                            title="Vanity Update",
                            description=f"Gave pic perms to {member.mention}, user has `{vanity}` in status.",
                            color=discord.Color.green(),
                        )
                        await log_channel.send(embed=embed)

                    elif not has_vanity and role in member.roles:
                        await member.remove_roles(role)
                        embed = discord.Embed(
                            title="Vanity Update", 
                            description=f"Removed pic perms from {member.mention}, user no longer has `{vanity}` in status.",
                            color=discord.Color.red(),
                        )
                        await log_channel.send(embed=embed)

                except Exception as e:
                    print(f"Error in vanity status check for {member.name}: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the vanity status checking loop when the bot is ready."""
        self.check_vanity_statuses.start()

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for 'pic' messages and respond with vanity instructions."""
        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            return

        if "pic" in message.content.lower():
            guild_id = str(message.guild.id)
            
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                
                server_config = config.get("servers", {}).get(guild_id, {})
                vanity = server_config.get("vanity", "/vanity")
                
                await message.channel.send(f"rep `{vanity}` 4 pic perms")
            except Exception as e:
                print(f"Error getting vanity for guild {guild_id}: {e}")

    @vanity_group.command(name="check")
    @commands.has_permissions(administrator=True)
    async def check_all_members(self, ctx):
        """Manually check all members' statuses and update roles."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config["servers"]:
            await ctx.send("Vanity not configured for this server.")
            return

        settings = self.config["servers"][guild_id]
        vanity = settings.get("vanity", "/vanity")
        pic_role_id = settings.get("pic_role")

        if not pic_role_id:
            await ctx.send("Pic role not configured.")
            return

        role = ctx.guild.get_role(pic_role_id)
        if not role:
            await ctx.send("Configured pic role not found.")
            return

        count = 0
        async with ctx.typing():
            for member in ctx.guild.members:
                if member.bot:
                    continue

                has_vanity = any(
                    vanity in str(activity.state or activity.name or "")
                    for activity in member.activities
                    if activity is not None
                )

                if has_vanity and role not in member.roles:
                    await member.add_roles(role)
                    count += 1
                elif not has_vanity and role in member.roles:
                    await member.remove_roles(role)
                    count += 1

        await ctx.send(f"Updated roles for `{count}` members.")

async def setup(bot):
    await bot.add_cog(Vanity(bot))