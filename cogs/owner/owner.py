import discord
import os
from discord.ext import commands, tasks
from discord.ext.commands import Cog, command, Context
from discord import Member
from cogs.config.classes import ServersView
from main import Heresy
import subprocess
import pyperclip
import pyperclip
import os
import tempfile
from PIL import ImageGrab, Image

class Owner(
    Cog,
    command_attrs=dict(hidden=True)
):
    def __init__(self, bot: Heresy):
        self.bot = bot
        self.reports_dir = './Reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        self.blacklisted_guilds = set()

    async def cog_check(self, ctx: Context) -> bool:
        return ctx.author.id in self.bot.owner_ids

    @command(name="servers")
    async def servers(self, ctx: Context):
        servers = self.bot.guilds
        custom_emojis = {
            "left": "<:left:1307448382326968330>",
            "right": "<:right:1307448399624405134>",
            "close": "<:cancel:1307448502913204294>"
        }
        view = ServersView(servers, ctx.author, custom_emojis)
        embed = view.get_embed()
        await ctx.send(embed=embed, view=view)

    @command(name="getinvite")
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

    @command()
    async def status(self, ctx: Context, *, status: str):
        """Set the bot's custom status (activity)."""
        try:
            custom_activity = discord.CustomActivity(name=status)
            await self.bot.change_presence(activity=custom_activity)
            await ctx.send(f"Custom status set to: `{status}`")
        except Exception as e:
            await ctx.send(f"Failed to set status: {str(e)}")

    @command()
    async def clearstatus(self, ctx: Context):
        """Clear the custom status."""
        try:
            await self.bot.change_presence(activity=None)
            await ctx.send("Custom status cleared.")
        except Exception as e:
            await ctx.send(f"Failed to clear status: {str(e)}")

    @command()
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

    @command()
    async def blacklist(self, ctx: Context, guild_id: int):
        """
        Blacklists a server by its ID.
        If the bot is already in the server, it leaves immediately.
        """
        self.blacklisted_guilds.add(guild_id)

        guild = self.bot.get_guild(guild_id)
        if guild:
            await ctx.send(f"Guild `{guild.name}` ({guild.id}) has been blacklisted and will be left immediately.")
            await guild.leave()
        else:
            await ctx.send(f"Guild with ID `{guild_id}` has been blacklisted. The bot will leave if it is added.")

    @command(name="sname")
    async def change_server_name(self, ctx, *args):
        """Change the name of a server.
        
        Usage:
        - In a server: ,sname <new_name>
        - For a specific server: ,sname <guild_id> <new_name>
        """
        # Check number of arguments
        if len(args) < 1:
            return await ctx.send("Please provide a new server name.")
        
        # Determine if guild_id is provided
        if len(args) >= 2:
            try:
                guild_id = int(args[0])
                new_name = " ".join(args[1:])
                guild = self.bot.get_guild(guild_id)
            except ValueError:
                # If first argument is not a valid integer, assume current server
                new_name = " ".join(args)
                guild = ctx.guild
        else:
            # Single argument mode (current server)
            new_name = args[0]
            guild = ctx.guild
        
        # Validate guild
        if not guild:
            return await ctx.send(f"Could not find a server with ID {guild_id}.")
        
        # Check bot's permissions
        if not guild.me.guild_permissions.manage_guild:
            return await ctx.send("I do not have permission to change the server name.")
        
        try:
            # Change server name
            await guild.edit(name=new_name)
            
            # Confirm the change
            embed = discord.Embed(
                title="Server Name Changed",
                description=f"Server name for **{guild.name}** has been changed to **{new_name}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        except discord.Forbidden:
            await ctx.send("I do not have permission to change the server name.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to change server name. Error: {e}")

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

    @command(name="rollback", aliases=["rlbck"])
    async def rollback_cog(self, ctx, cog: str = None):
        """
        Rollback a cog to its last committed state or all cogs if no specific cog is provided.
        
        Usage:
        ,jsk rollback - Rollback all cogs
        ,jsk rollback cogs.example - Rollback a specific cog
        """
        # Ensure only the bot owner can use this command
        if ctx.author.id != self.bot.owner_id:
            return await ctx.send("Only the bot owner can use this command.")
        
        try:
            import subprocess
            import os
            
            # Change to the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            os.chdir(project_root)
            
            # If no specific cog is provided, rollback all changes
            if not cog:
                cmd = "git reset --hard HEAD"
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                
                # Send output
                if result.returncode == 0:
                    await ctx.send(f"```\nSuccessfully rolled back all changes:\n{result.stdout}```")
                else:
                    await ctx.send(f"```\nError rolling back:\n{result.stderr}```")
                return
            
            # Rollback a specific cog
            # Normalize cog path
            cog_path = cog.replace('.', '/')
            full_cog_path = os.path.join(project_root, cog_path + '.py')
            
            # Check if cog file exists
            if not os.path.exists(full_cog_path):
                return await ctx.send(f"Cog file not found: {full_cog_path}")
            
            # Checkout the specific file
            cmd = f"git checkout HEAD -- {full_cog_path}"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            
            # Send output
            if result.returncode == 0:
                await ctx.send(f"```\nSuccessfully rolled back {cog}:\n{result.stdout}```")
            else:
                await ctx.send(f"```\nError rolling back {cog}:\n{result.stderr}```")
        
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @command(name="clipboard", aliases=["cb"])
    async def show_clipboard(self, ctx):
        """Show the current contents of the clipboard."""
        try:
            # Delete the user's message
            try:
                await ctx.message.delete()
            except discord.errors.NotFound:
                # Message already deleted
                pass
            except discord.errors.Forbidden:
                # Bot doesn't have permission to delete messages
                pass

            # Try to get image from clipboard
            image = ImageGrab.grabclipboard()
            
            if image:
                # Create a temporary file to save the image
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    image.save(temp_file.name, 'PNG')
                    
                # Send the image
                await ctx.send(file=discord.File(temp_file.name))
                
                # Remove the temporary file
                os.unlink(temp_file.name)
                return

            # If not an image, try text content
            clipboard_content = pyperclip.paste()
            
            # If clipboard is empty
            if not clipboard_content:
                await ctx.send("📋 Clipboard is empty.")
                return
            
            # Determine the type of content
            if len(clipboard_content) > 2000:
                # For long content, send as a file
                with open('clipboard_content.txt', 'w', encoding='utf-8') as f:
                    f.write(clipboard_content)
                
                await ctx.send(file=discord.File('clipboard_content.txt'))
                os.remove('clipboard_content.txt')
            else:
                # Check if content looks like code (contains code block markers or multiple lines with indentation)
                is_code = (
                    '```' in clipboard_content or 
                    '\n    ' in clipboard_content or 
                    '\n\t' in clipboard_content
                )
                
                if is_code:
                    # Send as code block
                    await ctx.send(f"```\n{clipboard_content}\n```")
                else:
                    # Send as normal message
                    await ctx.send(clipboard_content)
        
        except Exception as e:
            await ctx.send(f"Error retrieving clipboard: {str(e)}")

    @command(name="rpc")
    @commands.is_owner()
    async def set_rpc(self, ctx, *, name: str = None):
        """Set the bot's custom Rich Presence status."""
        if name is None:
            # Remove stored RPC
            if hasattr(self.bot, 'stored_rpc'):
                delattr(self.bot, 'stored_rpc')
            
            # Clear to no activity
            await self.bot.change_presence(activity=None)
            await ctx.send("Cleared bot's Rich Presence.")
            return

        # Create a custom activity with the provided name
        activity = discord.Activity(
            type=discord.ActivityType.streaming, 
            name=name,
            url="https://twitch.tv/creepfully"
        )

        try:
            # Store RPC setting on the bot object
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

    @Cog.listener()
    async def on_ready(self):
        # Check if there's a stored RPC setting
        rpc_setting = getattr(self.bot, 'stored_rpc', None)
        
        if rpc_setting:
            # If RPC is stored, set streaming presence
            activity = discord.Activity(
                type=discord.ActivityType.streaming, 
                name=rpc_setting,
                url="https://twitch.tv/creepfully"
            )
            await self.bot.change_presence(activity=activity, status=discord.Status.dnd)
        else:
            # Default to no activity
            await self.bot.change_presence(activity=None, status=discord.Status.dnd)
