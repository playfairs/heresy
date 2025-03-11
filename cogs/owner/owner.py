import discord
import os
from discord.ext import commands, tasks
from discord.ext.commands import Cog, command, Context
from discord import Member
from cogs.config.classes import ServersView
from main import heresy
import asyncio
import subprocess
import pyperclip
import os
import tempfile
from PIL import ImageGrab, Image
import platform
import asyncio
import shutil
import random
import string
import json
import time

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from io import BytesIO

class Owner(
    Cog,
    command_attrs=dict(hidden=True)
):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.owner_id = 785042666475225109
        self.reports_dir = './Reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.author.id in self.bot.owner_ids

    @command()
    async def changeavatar(self, ctx: Context, url: str):
        """
        Change the bot's avatar to the provided URL.
        """
        async with ctx.typing():
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        avatar_data = await response.read()
                        await self.bot.user.edit(avatar=avatar_data)
                        await ctx.send("Successfully updated the bot's avatar.", delete_after=5)
                    else:
                        await ctx.send("Failed to fetch the image from the provided URL.", delete_after=5)
            except Exception as e:
                await ctx.send(f"An error occurred: {e}", delete_after=5)

    @command()
    async def changebanner(self, ctx: Context, url: str):
        """
        Change the bot's banner to the provided URL.
        """
        async with ctx.typing():
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        banner_data = await response.read()
                        await self.bot.user.edit(banner=banner_data)
                        await ctx.send("Successfully updated the bot's banner.", delete_after=5)
                    else:
                        await ctx.send("Failed to fetch the image from the provided URL.", delete_after=5)
            except Exception as e:
                await ctx.send(f"An error occurred: {e}", delete_after=5)

    @command()
    async def enslave(self, ctx: Context, member: Member):
        """
        Assigns the 'heresy's Victims' role to the mentioned user if the user has manage_roles permissions.
        """
        if not ctx.author.guild_permissions.manage_roles:
            embed = discord.Embed(
                description="You need the **Manage Roles** permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=5)
            return

        role_name = "heresy's Victims"

        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            try:
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color.red(),
                    reason="Created for heresy's Victims command"
                )
                embed = discord.Embed(
                    description=f"Created the role **'{role_name}'** and assigned it to {member.mention}.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    description="I don't have permission to create the role.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, delete_after=5)
                return
            except discord.HTTPException as e:
                embed = discord.Embed(
                    description=f"An error occurred while creating the role: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, delete_after=5)
                return

        try:
            await member.add_roles(role, reason="Enslaved by the bot for testing purposes")
            embed = discord.Embed(
                description=f"{member.mention} has been successfully assigned the role **'{role_name}'**!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                description="I don't have permission to assign roles.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.HTTPException as e:
            embed = discord.Embed(
                description=f"An error occurred while assigning the role: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=5)

    @command()
    async def patched(self, ctx: Context, case_number: str = None):
        """
        Marks an issue as resolved and removes it from the reports.
        """
        if not case_number:
            await ctx.send("Please provide the case number of the issue to patch. For example: `,patched #2`.")
            return

        issue_file = os.path.join(self.reports_dir, f"Issue {case_number}.txt")
        if not os.path.exists(issue_file):
            await ctx.send(f"Issue `{case_number}` does not exist.")
            return

        os.remove(issue_file)
        await ctx.send(f"Issue `{case_number}` has been patched and removed from the reports.")

    @command(name="prefix")
    async def change_prefix(self, ctx: Context, new_prefix: str):
        """Changes the bot's global prefix."""
        if len(new_prefix) > 5:
            await ctx.send("Prefix must be 5 characters or less.")
            return

        config_path = 'config.py'
        try:
            await ctx.send(f"Attempting to change prefix to: {new_prefix}")
            
            with open(config_path, 'r') as f:
                lines = f.readlines()

            prefix_found = False
            for i, line in enumerate(lines):
                if 'PREFIX: str =' in line:
                    old_prefix = line.split('=')[1].strip().strip('"').strip("'")
                    lines[i] = f'    PREFIX: str = "{new_prefix}"\n'
                    prefix_found = True
                    await ctx.send(f"Found prefix line at line {i}: {line.strip()}")
                    break

            if not prefix_found:
                await ctx.send("Could not find PREFIX line in config file!")
                return

            with open(config_path, 'w') as f:
                f.writelines(lines)

            self.bot.command_prefix = new_prefix
            
            embed = discord.Embed(
                title="Prefix Updated",
                description=f"Prefix changed from `{old_prefix}` to `{new_prefix}`\nPlease restart the bot for changes to take effect.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update prefix: {str(e)}\nPath: {config_path}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

            import traceback
            print(f"Prefix change error: {traceback.format_exc()}")

    @command(name="clipboard", aliases=["cb"])
    async def show_clipboard(self, ctx):
        """Show the current contents of the clipboard."""
        try:
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                pass
            except discord.errors.Forbidden:
                pass

            image = ImageGrab.grabclipboard()
            
            if image:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    image.save(temp_file.name, 'PNG')
                    
                await ctx.send(file=discord.File(temp_file.name))
                
                os.unlink(temp_file.name)
                return

            clipboard_content = pyperclip.paste()
            
            if not clipboard_content:
                await ctx.send("Clipboard is empty.")
                return
            
            if len(clipboard_content) > 2000:
                with open('clipboard_content.txt', 'w', encoding='utf-8') as f:
                    f.write(clipboard_content)
                
                await ctx.send(file=discord.File('clipboard_content.txt'))
                os.remove('clipboard_content.txt')
            else:
                is_code = (
                    '```' in clipboard_content or 
                    '\n    ' in clipboard_content or 
                    '\n\t' in clipboard_content
                )
                
                if is_code:
                    await ctx.send(f"```\n{clipboard_content}\n```")
                else:
                    await ctx.send(clipboard_content)
        
        except Exception as e:
            await ctx.send(f"Error retrieving clipboard: {str(e)}")

    @command(name="rpc")
    @commands.is_owner()
    async def set_rpc(self, ctx, *, name: str = None):
        """Set the bot's custom Rich Presence status."""
        if name is None:
            if hasattr(self.bot, 'stored_rpc'):
                delattr(self.bot, 'stored_rpc')
            
            await self.bot.change_presence(activity=None)
            await ctx.send("Cleared bot's Rich Presence.")
            return

        activity = discord.Activity(
            type=discord.ActivityType.streaming, 
            name=name,
            url="https://twitch.tv/creepfully"
        )

        try:
            self.bot.stored_rpc = name
            
            await self.bot.change_presence(activity=activity)
            embed = discord.Embed(
                title=" Bot Rich Presence Updated",
                description=f"Set RPC to: `{name}`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Failed to set RPC: {str(e)}")

    @commands.command(name='echo')
    async def echo(self, ctx, *, message: str):
        """Echoes the provided message. Only the owner can use this command."""
        if ctx.author.id != self.owner_id:
            await ctx.send("You do not have permission to use this command.")
            return
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(name='root')
    @commands.is_owner()
    async def root(self, ctx):
        """Displays system and user information related to the bot."""
        system_info = f"**System Information:**\n- OS: {platform.system()} {platform.release()}\n- Python Version: {platform.python_version()}\n- Architecture: {platform.architecture()}\n\n" 
        
        user_info = "**User Management:**\n"
        admin_users = [user.name for user in ctx.guild.members if user.guild_permissions.administrator]
        user_info += f"- Admin Users: {', '.join(admin_users)}\n"

        process_info = "**Process Information:**\n- Running Processes: [Example Process]\n"

        access_info = system_info + user_info + process_info

        embed = discord.Embed(title="Root Info", description=access_info, color=0x000000)
        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_ready(self):
        rpc_setting = getattr(self.bot, 'stored_rpc', None)
        
        if rpc_setting:
            activity = discord.Activity(
                type=discord.ActivityType.streaming, 
                name=rpc_setting,
                url="https://twitch.tv/creepfully"
            )
            await self.bot.change_presence(activity=activity, status=discord.Status.dnd)
        else:
            await self.bot.change_presence(activity=None, status=discord.Status.dnd)

    @commands.command(name='pingrandom')
    async def pingrandom(self, ctx):
        """Ping a random user in the server who is not online."""
        members = ctx.guild.members
        
        offline_members = [member for member in members if member.status != discord.Status.online and not member.bot]
        
        if offline_members:
            random_member = random.choice(offline_members)
            await ctx.send(f"{random_member.mention}")
        else:
            await ctx.send("no ones offline")

    @commands.group(name="status", invoke_without_command=True)
    async def status(self, ctx, *, status: str = None):
        """Change the bot's status."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @status.command()
    async def set(self, ctx: Context, *, status: str):
        """Set the custom status."""
        try:
            custom_activity = discord.CustomActivity(name=status)
            await self.bot.change_presence(activity=custom_activity)
            await ctx.send(f"Custom status set to: `{status}`")
        except Exception as e:
            await ctx.send(f"Failed to set status: {str(e)}")

    @status.command(name='rotate')
    async def status_rotate(self, ctx: Context, *, args: str):
        """Rotate the custom status.
        
        Usage:
        ,status rotate example, example 2, example 3 --seconds 5
        """
        try:
            parts = args.split('--seconds')
            statuses = [arg.strip() for arg in parts[0].split(',')]
            
            seconds = 30
            
            if len(parts) > 1:
                seconds_str = parts[1].strip()
                if seconds_str.isdigit():
                    seconds = int(seconds_str)
                else:
                    await ctx.send("Invalid seconds value provided. Using default value of 5 seconds.")
            
            if len(statuses) == 0:
                await ctx.send("No statuses provided.")
                return
            
            self.status_rotation_task = self.bot.loop.create_task(self.rotate_status(ctx, statuses, seconds))
            await ctx.send(f"Set custom status to rotate every {seconds} seconds.")
        except Exception as e:
            await ctx.send(f"Failed to set status: {str(e)}")

    async def rotate_status(self, ctx: Context, statuses: list, seconds: int):
        while True:
            for status in statuses:
                custom_activity = discord.CustomActivity(name=status)
                await self.bot.change_presence(activity=custom_activity)
                await asyncio.sleep(seconds)

    @status.command(name='clear')
    async def status_clear(self, ctx: Context):
        """Clear the custom status."""
        try:
            if hasattr(self, 'status_rotation_task') and self.status_rotation_task is not None:
                self.status_rotation_task.cancel()
                self.status_rotation_task = None
                await ctx.send("Status rotation has been cleared.")
            else:
                await ctx.send("No status rotation is currently active.")
        except Exception as e:
            await ctx.send(f"Failed to clear status: {str(e)}")

    @commands.group(name="servers", aliases=["server"], invoke_without_command=True)
    async def servers(self, ctx):
        """Server management and Blacklist"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @servers.command(name="list")
    async def list_servers(self, ctx: Context):
        servers = self.bot.guilds
        custom_emojis = {
            "left": "<:left:1307448382326968330>",
            "right": "<:right:1307448399624405134>",
            "close": "<:cancel:1307448502913204294>"
        }
        view = ServersView(servers, ctx.author, custom_emojis)
        embed = view.get_embed()
        await ctx.send(embed=embed, view=view)

    @servers.command(name="invite")
    async def invite(self, ctx: Context, guild_id: int):
        """
        Generates an invite link for the specified guild (server).
        Usage: ,invite <guild_id>
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            await ctx.reply("I could not find the server with the given ID, which means I'm probably not in there.", mention_author=True)
            return
        try:
            invite = await guild.text_channels[0].create_invite(max_uses=1, unique=True, temporary=True)
            invite_url = invite.url
            await ctx.reply(f"{invite_url}")
        except Exception as e:
            await ctx.reply(f"Could not generate an invite for **{guild.name}**. Error: {e}")

    @servers.command()
    async def revoke(self, ctx: Context, guild_id: int = None):
        """
        Makes the bot leave a server.
        - If no guild ID is provided, it leaves the current server.
        - If a guild ID is provided, it leaves the specified server.
        """
        if guild_id is None:
            guild = ctx.guild
            await ctx.send(f"Leaving the current server: `{guild.name}` ({guild.id}).")
            await guild.leave()
        else:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await ctx.send(f"Leaving server: `{guild.name}` ({guild.id}).")
                await guild.leave()
            else:
                await ctx.send(f"No server found with ID `{guild_id}`.")

    @servers.command()
    async def blacklist(self, ctx: Context, guild_id: int = None):
        """
        Adds a server to the blacklist.
        Usage: ,blacklist <guild_id>
        """
        if guild_id is None:
            guild = ctx.guild
            await ctx.send(f"Blacklisting the current server: `{guild.name}` ({guild.id}).")
            data = self.load_json(self.blacklist_file)
            data["blacklisted_servers"].append(guild.id)
            self.save_json(data, self.blacklist_file)
            await guild.leave()
        else:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await ctx.send(f"Blacklisting server: `{guild.name}` ({guild.id}).")
                data = self.load_json(self.blacklist_file)
                data["blacklisted_servers"].append(guild.id)
                self.save_json(data, self.blacklist_file)
                if guild in self.bot.guilds:
                    await guild.leave()
            else:
                await ctx.send(f"No server found with ID `{guild_id}`.")

    @servers.command()
    async def whitelist(self, ctx: Context, guild_id: int = None):
        """
        Removes a server from the blacklist.
        Usage: ,whitelist <guild_id>
        """
        if guild_id is None:
            guild = ctx.guild
            await ctx.send(f"Whitelisting the current server: `{guild.name}` ({guild.id}).")
            data = self.load_json(self.blacklist_file)
            data["blacklisted_servers"].remove(guild.id)
            self.save_json(data, self.blacklist_file)
        else:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await ctx.send(f"Whitelisting server: `{guild.name}` ({guild.id}).")
                data = self.load_json(self.blacklist_file)
                data["blacklisted_servers"].remove(guild.id)
                self.save_json(data, self.blacklist_file)
            else:
                await ctx.send(f"No server found with ID `{guild_id}`.")

    @commands.group(name="bp", invoke_without_command=True)
    async def bp(self, ctx):
        """Base command for purging only the bots messages."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @bp.command()
    async def after(self, ctx: Context, message_id: int):
        """Purges only messages sent after the specified message."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            if message.author == self.bot.user:
                    await message.delete()
            await ctx.send("Deleted messages after the given ID.", delete_after=5)
        except discord.NotFound:
            await ctx.send("Message not found.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete my own messages.. man what happened to free will.", delete_after=5)

    @bp.command()
    async def before(self, ctx: Context, message_id: int):
        """Purges only messages sent before the specified message."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            if message.author == self.bot.user:
                    await message.delete()
            await ctx.send("Deleted messages before the given ID.", delete_after=5)
        except discord.NotFound:
            await ctx.send("Message not found.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete my own messages.. man what happened to free will.", delete_after=5)

    @bp.command(name="amnt", aliases=["amount", "number"])
    async def amnt(self, ctx: Context, amount: int):
        """Purges a specified amount of messages from the channel."""
        deleted = 0
        async for message in ctx.channel.history(limit=amount):
            if message.author == self.bot.user:
                await message.delete()
                deleted += 1

        await ctx.send(f"Deleted {deleted} messages.", delete_after=5)

    @bp.command()
    async def specific(self, ctx: Context, message_id: int):
        """Purges only the specified message."""
        try:
            message = await ctx.channel.fetch_message(message_id)
            if message.author == self.bot.user:
                await message.delete()
                await ctx.send("Deleted the specified message.", delete_after=5)
            else:
                await ctx.send("The specified message was not sent by the bot.", delete_after=5)
        except discord.NotFound:
            await ctx.send("Message not found.", delete_after=5)
        except discord.Forbidden:
            await ctx.send("I do not have permission to delete my own messages.. man what happened to free will.", delete_after=5)

    @commands.command(name="nvim", aliases=["neovim", "nvm", "vim"])
    async def nvim(self, ctx: Context):
        """Opens Neovim in a new terminal"""
        await ctx.send("Opening Neovim in a new terminal.")
        os.system("open -g -a goneovim")

    @commands.command(name="terminal", aliases=["term", "cmd", "kitty"])
    async def terminal(self, ctx: Context):
        """Opens Kitty Terminal"""
        await ctx.send("I like playing with my kitty.. ngh~ >_<")
        os.system("open -na kitty")

    @commands.command(name="open", aliases=["openapp"])
    async def open(self, ctx: Context, app: str):
        """Opens the specified application."""
        await ctx.send(f"Opening {app}.")
        os.system(f"open -g -a {app}")

    @commands.command(name="ball")
    async def ball(self, ctx: Context):
        """Opens the Ball application."""
        await ctx.send(f"I like playing with my balls..")
        os.system(f"open -g -a Ball")

    @commands.group(name="sudo", invoke_without_command=True)
    async def sudo(self, ctx: Context, command: str):
        """Runs the specified command as the bot's owner."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            return

    @sudo.command(name="dm")
    async def dm(self, ctx: Context, user: discord.Member, *, message: str):
        """Sends a direct message to a specified user."""
        if user.bot:
            await ctx.send("I cannot send messages to bots.")
            return
        if user.id == ctx.author.id:
            await ctx.send("Are you that lonely?")
            return
        await ctx.send(f"👍")
        await user.send(message)
        await ctx.message.delete()

    @commands.command(name="screenshot", aliases=["ss"])
    async def screenshot(self, ctx: commands.Context, *, args: str):
        """Takes a screenshot of the specified URL and sends it."""
        url = None
        delay = 0

        arg_list = args.split()
        for arg in arg_list:
            if arg.startswith("--delay"):
                try:
                    delay = int(arg.split("=")[1])
                except (IndexError, ValueError):
                    await ctx.send("Please provide a valid integer for delay.")
                    return
            else:
                if url is None:
                    url = arg

        if url is None:
            await ctx.send("Please provide a URL.")
            return

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.set_window_size(1920, 1080)

        driver.get(url)
        if delay > 0:
            await asyncio.sleep(delay)
        screenshot = driver.get_screenshot_as_png()
        driver.quit()

        file = discord.File(BytesIO(screenshot), filename="screenshot.png")
        await ctx.send(file=file)
