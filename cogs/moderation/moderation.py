import discord
import aiohttp
import asyncio
import io
import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Optional, Union

from discord.ext import commands, tasks
from discord.ext.commands import command, group, has_permissions, Context, Cog
from discord.ui import Button, View
from discord import Member
from discord.app_commands import command as acommand
from discord import AutoModRuleEventType, AutoModRuleTriggerType, AutoModRuleAction, AutoModAction

from collections import deque

from cogs.moderation.classes import RolesView, BanListView

def generate_random_string(length=8):
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(characters) for _ in range(length))

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.session = aiohttp.ClientSession()
        self.sniped_messages = {}
        self.edited_messages = {}
        self.snipe_reset.start()
        self.sniped_reactions = {}
        self.users_triggered_bot = set()
        self.exempt_channels = set()
        self.case_count = 0
        self.config_folder = "Member-Access-Roles"
        self.backup_folder = "Server Backups"
        os.makedirs(self.config_folder, exist_ok=True)
        os.makedirs(self.backup_folder, exist_ok=True)
        self.file_path = "./json/selfbots.json"

        os.makedirs("./json", exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

        self.unbannable_user_ids = [785042666475225109, 1268333988376739931, 608450597347262472, 598125772754124823, 926665802957066291, 818507782911164487, 1003843669528424468, 757355424621133914, 812606857742647298, 1252011606687350805, 877283649588965416]

    def load_selfbots(self):
        """Loads the selfbots.json file."""
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save_selfbots(self, data):
        """Saves data to the selfbots.json file."""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def save_json(self, data, filename):
        """Saves the provided data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_json(self, filename):
        """Loads data from a JSON file."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    async def give_role(self, ctx, member: discord.Member, role_input: str):
        """Give or remove a role from a member, skipping bot users."""
        if member.bot:
            await ctx.send("Cannot modify roles for bots.")
            return

        # Find the role by name or mention
        role = None
        try:
            role = await commands.RoleConverter().convert(ctx, role_input)
        except commands.RoleNotFound:
            await ctx.send(f"Role '{role_input}' not found.")
            return

        # Check role hierarchy
        if role.position >= ctx.author.top_role.position:
            embed = discord.Embed(description="You cannot manage a role that is higher or equal to your highest role.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        # Check bot's role hierarchy
        if role.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(description="I cannot manage a role that is higher or equal to my highest role.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        try:
            if role in member.roles:
                # Remove role if already has it
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
                embed = discord.Embed(description=f"Removed {role.mention} from {member.mention}.", color=0xADD8E6)
                await ctx.send(embed=embed)
            else:
                # Add role
                await member.add_roles(role, reason=f"Role added by {ctx.author}")
                embed = discord.Embed(description=f"Gave {role.mention} to {member.mention}.", color=0xADD8E6)
                await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to manage this role.")
        except discord.HTTPException:
            await ctx.send("An error occurred while managing the role.")

    async def send_embed(self, ctx, message: str):
        embed = discord.Embed(description=message, color=0xADD8E6)
        await ctx.send(embed=embed)

    @group(name="r", invoke_without_command=True)
    @has_permissions(manage_roles=True)
    async def role_group(self, ctx, member: discord.Member = None, *, role_input: str = None):
        if member and role_input:
            await self.give_role(ctx, member, role_input)
        else:
            await ctx.send("Please provide a subcommand or a valid user and role (e.g., `,r @user role_name`).")

    @role_group.command(name="human", aliases= ["humans"])
    @has_permissions(manage_roles=True)
    async def role_human(self, ctx, role: discord.Role):
        count = len([member for member in ctx.guild.members if not member.bot])
        await self.send_embed(ctx, f"Adding {role.mention} to {count} human members, this may take a moment...")

        for member in ctx.guild.members:
            if not member.bot:
                await member.add_roles(role)

        await self.send_embed(ctx, f"Role {role.mention} has been given to {count} human members.")

    @role_group.command(name="bot", aliases= ["bots"])
    @has_permissions(manage_roles=True)
    async def role_bot(self, ctx, role: discord.Role):
        count = len([member for member in ctx.guild.members if member.bot])
        await self.send_embed(ctx, f"Adding {role.mention} to {count} bot members, this may take a moment...")

        for member in ctx.guild.members:
            if member.bot:
                await member.add_roles(role)

        await self.send_embed(ctx, f"Role {role.mention} has been given to {count} bot members.")

    @role_group.command(name="has")
    @has_permissions(manage_roles=True)
    async def role_has(self, ctx, role: discord.Role, action: str, new_role: discord.Role):
        if action.lower() not in ["give", "remove"]:
            await ctx.send("Invalid action. Use `give` or `remove`.")
            return

        count = len([member for member in ctx.guild.members if role in member.roles])
        await self.send_embed(ctx, f"{'Giving' if action == 'give' else 'Removing'} {new_role.mention} to/from {count} members, this may take a moment...")

        for member in ctx.guild.members:
            if role in member.roles:
                if action.lower() == "give":
                    await member.add_roles(new_role)
                elif action.lower() == "remove":
                    await member.remove_roles(new_role)

        await self.send_embed(ctx, f"Role {new_role.mention} has been {'given' if action == 'give' else 'removed'} to/from {count} members.")

    @role_group.command(name="create")
    @has_permissions(manage_roles=True)
    async def role_create(self, ctx, *, role_name: str):
        guild = ctx.guild
        await guild.create_role(name=role_name)
        await self.send_embed(ctx, f"Role {role_name} created successfully.")

    @role_group.command(name="delete")
    @has_permissions(manage_roles=True)
    async def role_delete(self, ctx, role: discord.Role):
        await role.delete()
        await self.send_embed(ctx, f"Role {role.mention} has been deleted.")

    @role_group.command(name="give")
    @has_permissions(manage_roles=True)
    async def role_give(self, ctx, member: discord.Member, *, role_input: str):
        role = None
        try:
            role = await commands.RoleConverter().convert(ctx, role_input)
        except commands.RoleNotFound:
            await ctx.send(f"Role '{role_input}' not found.")
            return

        if role.position >= ctx.author.top_role.position:
            await ctx.send("You cannot manage a role that is higher or equal to your highest role.")
            return

        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("I cannot manage a role that is higher or equal to my highest role.")
            return

        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
                embed = discord.Embed(description=f"🔴 Role {role.mention} has been removed from {member.mention}", color=0x000000)
                await ctx.send(embed=embed)
            else:
                await member.add_roles(role, reason=f"Role added by {ctx.author}")
                green_check = ctx.guild.get_emoji(1327706977345732680)
                embed = discord.Embed(description=f"{green_check} Role {role.mention} has been given to {member.mention}", color=0x000000)
                await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I do not have permission to manage this role.")
        except discord.HTTPException:
            await ctx.send("An error occurred while managing the role.")

    @role_group.command(name="remove")
    @has_permissions(manage_roles=True)
    async def role_remove(self, ctx, member: discord.Member, *, role_input: str):
        guild = ctx.guild
        role = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            role_id = int(role_input[3:-1])
            role = guild.get_role(role_id)
        elif role_input.isdigit():
            role = guild.get_role(int(role_input))
        else:
            role = discord.utils.find(lambda r: r.name.lower().startswith(role_input.lower()), guild.roles)

        if role:
            await member.remove_roles(role)
            await self.send_embed(ctx, f"Role {role.mention} has been removed from {member.mention}.")
        else:
            await ctx.send(f"Role '{role_input}' not found.")

    @role_group.command(name="rename")
    @has_permissions(manage_roles=True)
    async def role_rename(self, ctx, role: discord.Role, new_name: str):
        await role.edit(name=new_name)
        await self.send_embed(ctx, f"Role {role.mention} has been renamed to '{new_name}'.")

    @role_group.command(name="icon")
    @has_permissions(manage_roles=True)
    async def role_icon(self, ctx, role: discord.Role, emoji: Optional[Union[discord.Emoji, str]] = None):
        if emoji is None:
            await ctx.send("Please provide an emoji.")
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io

            # Create a 128x128 transparent image
            img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Handle Unicode emojis
            if isinstance(emoji, str):
                # Check if it's a valid Unicode emoji
                if len(emoji) > 1:
                    await ctx.send("Please provide a single Unicode emoji.")
                    return
                
                # Use a large font to draw the emoji
                font_size = 100
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

                # Get text size and position to center the emoji
                bbox = draw.textbbox((0, 0), emoji, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (128 - text_width) // 2
                y = (128 - text_height) // 2

                # Draw the emoji
                draw.text((x, y), emoji, font=font, fill=(255, 255, 255, 255))
            
            # Handle custom Discord emojis
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(emoji.url)) as response:
                        if response.status != 200:
                            await ctx.send("Failed to fetch the emoji image. Please check the emoji.")
                            return

                        emoji_bytes = await response.read()
                        emoji_img = Image.open(io.BytesIO(emoji_bytes))
                        
                        # Resize and center the emoji
                        emoji_img.thumbnail((128, 128), Image.LANCZOS)
                        img.paste(emoji_img, ((128 - emoji_img.width) // 2, (128 - emoji_img.height) // 2), emoji_img)
            
            # Save image to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Use Discord's method to set role icon
            await role.edit(display_icon=img_byte_arr)
            await ctx.send(f"Role {role.mention}'s icon has been updated using the emoji {emoji}.")
        
        except discord.HTTPException as e:
            await ctx.send(f"Failed to set role icon: {str(e)}")
        except ImportError:
            await ctx.send("This feature requires the Pillow library. Please install it using 'pip install Pillow'.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {str(e)}")

    @role_group.command(name="hoist")
    @has_permissions(manage_roles=True)
    async def role_hoist(self, ctx, role: discord.Role, hoist: str = None):
        """
        Toggles or sets the hoist status of a role.

        Parameters:
        - role: The role to edit.
        - hoist: True/False to set the hoist explicitly, or omit to toggle.
        """
        if hoist is not None:
            if hoist.lower() in ("true", "yes", "on"):
                hoist_value = True
            elif hoist.lower() in ("false", "no", "off"):
                hoist_value = False
            else:
                await ctx.send("Please specify `true` or `false` for the hoist argument.")
                return
        else:
            hoist_value = not role.hoist

        try:
            await role.edit(hoist=hoist_value, reason=f"Hoist changed by {ctx.author}")
            state = "now displayed" if hoist_value else "no longer displayed"
            await ctx.send(f"Role {role.mention} is {state} separately.")
            await ctx.message.add_reaction("👍")
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit this role.")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while updating the role: {str(e)}")

    @role_group.command(name="color")
    @has_permissions(manage_roles=True)
    async def role_color(self, ctx, role: discord.Role, color_hex: str):
        try:
            color = discord.Color(int(color_hex.lstrip("#"), 16))
            await role.edit(color=color)
            await self.send_embed(ctx, f"Role {role.mention}'s color has been changed to {color_hex}.")
        except ValueError:
            await ctx.send("Invalid color hex code. Please provide a valid hex color (e.g., #00ff00).")

    @command(name="autorole")
    @has_permissions(manage_roles=True)
    async def autorole(self, ctx, role: discord.Role):
        query = "SELECT role_id FROM autorole_humans WHERE guild_id = $1"
        async with self.bot.db.acquire() as conn:
            result = await conn.fetchrow(query, ctx.guild.id)
            if result and result["role_id"] == role.id:
                await self.bot.db.execute("DELETE FROM autorole_humans WHERE guild_id = $1", ctx.guild.id)
                await self.send_embed(ctx, f"Autorole for new human members has been removed for this server.")
            else:
                await self.bot.db.execute("""INSERT INTO autorole_humans (guild_id, role_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET role_id = EXCLUDED.role_id""", ctx.guild.id, role.id)
                await self.send_embed(ctx, f"Autorole for new human members set to {role.mention} for this server.")

    @command(name="autorolebots")
    @has_permissions(manage_roles=True)
    async def autorole_bots(self, ctx: Context, role: discord.Role):
        """Automatically assigns a role to new bot members for this server."""
        query = "SELECT role_id FROM autorole_bots WHERE guild_id = $1"
        async with self.bot.db.acquire() as conn:
            result = await conn.fetchrow(query, ctx.guild.id)
            if result and result["role_id"] == role.id:
                await self.bot.db.execute("DELETE FROM autorole_bots WHERE guild_id = $1", ctx.guild.id)
                await self.send_embed(ctx, f"Autorole for new bot members has been removed for this server.")
            else:
                await self.bot.db.execute("""INSERT INTO autorole_bots (guild_id, role_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET role_id = EXCLUDED.role_id""", ctx.guild.id, role.id)
                await self.send_embed(ctx, f"Autorole for new bot members set to {role.mention} for this server.")

    @command(name="roles")
    @commands.has_permissions(manage_roles=True)
    async def roles(self, ctx):
        roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
        custom_emojis = {
            "left": "<:left:1307448382326968330>",
            "right": "<:right:1307448399624405134>",
            "close": "<:cancel:1307448502913204294>"
        }
        view = RolesView(roles, ctx.author, custom_emojis)
        embed = view.get_embed()
        await ctx.send(embed=embed, view=view)

    @roles.error
    async def roles_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You are missing the `Manage Roles` permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.group(name="inrole", invoke_without_command=True)
    async def inrole(self, ctx, role: discord.Role):
        """Displays all members in a specific role with interactive buttons."""
        members = role.members
        if not members:
            await ctx.send(f"No members found in the role {role.mention}.")
            return

        member_chunks = [members[i:i + 10] for i in range(0, len(members), 10)]
        current_page = 0

        class PaginationView(discord.ui.View):
            def __init__(self, pages):
                super().__init__(timeout=60)
                self.current_page = 0
                self.pages = pages
                self.update_buttons()

            def update_buttons(self):
                self.prev_page.disabled = self.current_page == 0
                self.next_page.disabled = self.current_page == len(self.pages) - 1

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, emoji="◀")
            async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.update_buttons()
                    embed = create_embed(self.current_page)
                    await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="▶")
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                    self.update_buttons()
                    embed = create_embed(self.current_page)
                    await interaction.response.edit_message(embed=embed, view=self)

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)

        def create_embed(page):
            embed = discord.Embed(
                title=f"Members in {role.name} ({len(members)})",
                description="\n".join([f"- {member.mention}" for member in member_chunks[page]]),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {page + 1}/{len(member_chunks)}")
            return embed

        view = PaginationView(member_chunks)
        embed = create_embed(current_page)
        view.message = await ctx.send(embed=embed, view=view)

    @inrole.command(name="ban")
    @has_permissions(ban_members=True)
    async def inrole_ban(self, ctx, role: discord.Role):
        """Bans all members in the mentioned role."""
        for member in role.members:
            try:
                await member.ban(reason=f"Mass ban by {ctx.author} via inrole ban")
                await ctx.send(f"Banned {member.mention}")
            except Exception as e:
                await ctx.send(f"Failed to ban {member.mention}: {e}")

    @inrole.command(name="kick")
    @has_permissions(kick_members=True)
    async def inrole_kick(self, ctx, role: discord.Role):
        """Kicks all members in the mentioned role."""
        for member in role.members:
            try:
                await member.kick(reason=f"Mass kick by {ctx.author} via inrole kick")
                await ctx.send(f"Kicked {member.mention}")
            except Exception as e:
                await ctx.send(f"Failed to kick {member.mention}: {e}")

    @inrole.command(name="timeout")
    @has_permissions(moderate_members=True)
    async def inrole_timeout(self, ctx, role: discord.Role):
        """Timeouts all members in the mentioned role."""
        for member in role.members:
            try:
                await member.timeout_for(duration=600, reason=f"Mass timeout by {ctx.author} via inrole timeout")
                await ctx.send(f"Timed out {member.mention}")
            except Exception as e:
                await ctx.send(f"Failed to timeout {member.mention}: {e}")

    @inrole.command(name="strip")
    @has_permissions(manage_roles=True)
    async def inrole_strip(self, ctx, role: discord.Role):
        """Removes all roles from members in the mentioned role."""
        for member in role.members:
            try:
                await member.edit(roles=[], reason=f"Mass role removal by {ctx.author} via inrole strip")
                await ctx.send(f"Stripped roles from {member.mention}")
            except Exception as e:
                await ctx.send(f"Failed to strip roles from {member.mention}: {e}")

    def can_moderate(self, moderator, target) -> bool:
        """Helper function to check if moderator can moderate target based on role hierarchy"""

        if moderator.id == moderator.guild.owner_id:
            return True
            
        if moderator.id == target.id:
            return False
            
        if moderator.top_role == target.top_role:
            return False
            
        return moderator.top_role > target.top_role

    @command(name='ban', aliases=['fuck', 'rape'], help='Bans a member by mention or User ID.')
    @has_permissions(ban_members=True)
    async def ban(self, ctx, target: Union[discord.Member, int] = None, *, reason: str = None):
        if target is None:
            return await ctx.send("You must specify a user to ban, thats typically how it works.. 😭")

        if isinstance(target, int):
            try:
                target = await ctx.guild.fetch_member(target)
            except discord.NotFound:
                target = discord.Object(id=target)

            if not self.can_moderate(ctx.author, target):
                return await ctx.send("'But it refused' ahh error 😭🙏.")

            if target == self.bot.user:
                await ctx.send("I am not banning myself, that would be stupid.")
                return

            if target.id in self.unbannable_user_ids:
                await ctx.send("no.")
                return

        # Check role hierarchy for Member objects
        if isinstance(target, discord.Member):
            if target.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                embed = discord.Embed(description="You cannot ban a user with a role higher or equal to yours.", color=0xFF0000)
                await ctx.send(embed=embed)
                return

        try:
            # Check if user is already banned
            try:
                ban_entry = await ctx.guild.fetch_ban(target)
                return await ctx.send("They're already banned 😭")
            except discord.NotFound:
                # User is not banned, proceed with banning
                await ctx.guild.ban(target, reason=f"Banned by {ctx.author}" + (f": {reason}" if reason else ""))
                await ctx.send("👍")
        except discord.HTTPException as e:
            await ctx.send(f"Uh oh, fucky wucky was made: {e}")

    @command(name='kick', aliases=['soccer'], help='Kicks a member by mention or User ID.')
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, user_id: int = None):
        """
        Kicks a member from the server.
        """
        # If user_id is provided, try to fetch the member
        if user_id and not member:
            try:
                member = await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                await ctx.send("Bros tryna kick someone who's not even here 😭")
                return
            except discord.HTTPException:
                await ctx.send("An error occurred while fetching the user.")
                return

        # Validate member
        if not member:
            await ctx.send("What, are we kicking ghosts now? What in the ghostbusters are you trying to kick, specify a user..")
            return

        # Check role hierarchy
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="You cannot kick this user due to role hierarchy!", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        try:
            await member.kick(reason=f"Kicked by {ctx.author}")
            await ctx.send(f"👍")

            # Create the embed for the kicked user
            embed = discord.Embed(title="Bye bye", description=f"You were kicked in {ctx.guild.name} by {ctx.author.mention} for no reason", color=0xFF0000)
            # Send the embed as a DM to the kicked member
            await member.send(embed=embed)
        except discord.HTTPException: 
            await ctx.send("FUCK YOU! I could not pm user")

        except discord.Forbidden:
            await ctx.send("I do not have permission to kick this user.")
        except discord.HTTPException:
            await ctx.send("Failed to kick the user.")

    @command(name='unban', aliases=['befree'], help='Unbans a member by User ID.')
    @has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """
        Unbans a user by their User ID.
        """
        try:
            # Directly attempt to unban using the user ID
            await ctx.guild.unban(discord.Object(id=user_id), reason=f"Unbanned by {ctx.author}")
            
            # Send a simple confirmation
            await ctx.send("👍")

        except discord.NotFound:
            # This typically means the user is not in the ban list
            await ctx.send(f"They're not even banned 😭")
        
        except discord.Forbidden:
            # Bot lacks permissions to unban
            await ctx.send("I not have permissions :c")
        
        except discord.HTTPException as e:
            # Catch any HTTP-related errors
            await ctx.send(f"something went wrong 😭 {e}")
        
        except Exception as e:
            # Catch any unexpected errors
            await ctx.send(f"something went wrong 😭 {str(e)}")
            # Log the full error for debugging
            print(f"Unban error: {traceback.format_exc()}")

    @command(name='warn', help='Warns a member by mention or User ID.')
    @has_permissions(manage_messages=True)
    async def warn(self, ctx: Context, member: Member, reason: str = None):
        if not self.can_moderate(ctx.author, member):
            return await ctx.send("You cannot warn this user due to role hierarchy!")

        if not Member:
            return await ctx.send("You must specify a user to warn (mention or User ID).")
        query = "INSERT INTO warnings (guild_id, user_id, author_id, reason) VALUES ($1, $2, $3, $4)"
        async with self.bot.db.acquire() as conn:
            await conn.execute(query, ctx.guild.id, member.id, ctx.author.id, reason or "No reason provided")
        await ctx.send(f"{member.mention} has been warned for {reason or 'No reason provided'}.")

    @command(name='timeout', aliases=['to', 'bdsm', 'ballgag', 'stfu', 'sybau', 'touch', 'smd'], help='Times out a member (e.g. ,to @user 7d, 24h, 60m)')
    @has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member = None, duration: str = "5m"):
        if not member:
            await ctx.send("You must specify a user to timeout.")
            return
            
        if member.bot:
            await ctx.send("no")
            return

        if not self.can_moderate(ctx.author, member):
            return await ctx.send("no")

        try:
            amount = int(duration[:-1])
            unit = duration[-1].lower()
            
            if unit == 'm':
                if not 1 <= amount <= 60:
                    return await ctx.send("Minutes must be between 1 and 60.")
                seconds = amount * 60
            elif unit == 'h':
                if not 1 <= amount <= 24:
                    return await ctx.send("Hours must be between 1 and 24.")
                seconds = amount * 3600
            elif unit == 'd':
                if not 1 <= amount <= 7:
                    return await ctx.send("Days must be between 1 and 7.")
                seconds = amount * 86400
            else:
                return await ctx.send("Invalid duration format. Use `m` for minutes, `h` for hours, or `d` for days (e.g. 30m, 12h, 7d)")
                
        except (ValueError, IndexError):
            return await ctx.send("Invalid duration format. Use `m` for minutes, `h` for hours, or `d` for days (e.g. 30m, 12h, 7d)")

        try:
            await member.timeout(discord.utils.utcnow() + timedelta(seconds=seconds), reason=f"Timed out by {ctx.author}")
            await ctx.send(f"Bad {member.mention}! Go sit in the naughty corner and think about what you did for {duration}! No cookies for you! 😠")
        except discord.Forbidden:
            await ctx.send("I do not have permission to timeout this user.")
        except discord.HTTPException:
            await ctx.send("Failed to timeout the user.")

    @command(name='untimeout', aliases= ['uto', 'getmydickoutyamouth'], help='Removes the timeout from a member by mention or User ID.')
    @has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx, member: discord.Member = None, user_id: int = None):
        target = await self.get_member(ctx, member, user_id)
        
        if not target:
            await ctx.send("You must specify a user to remove timeout (mention or User ID).")
            return

        try:
            await target.timeout(None, reason=f"Timeout removed by {ctx.author}")
            await ctx.send("👍")
        except discord.Forbidden:
            await ctx.send("I do not have permission to remove timeout from this user.")
        except discord.HTTPException:
            await ctx.send("Failed to remove timeout from the user.")

    @command(name='nick')
    @has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, new_nick: str = None):
        """Changes or resets the nickname of the mentioned user."""
        try:
            await member.edit(nick=new_nick)
            if new_nick:
                await ctx.send(f"Nickname for {member.mention} changed to `{new_nick}`.")
            else:
                await ctx.send(f"Nickname for {member.mention} has been reset.")
        except discord.HTTPException:
            await ctx.send("Failed to change the nickname. Please try again.")

    @command(name='forcenick', aliases=['fn'])
    @has_permissions(administrator=True)
    async def forcenick(self, ctx, member: discord.Member = None, *, forced_nick: Optional[str] = None):
        """Forces a nickname on a user that cannot be changed. If no nickname is provided, removes the forced nickname."""
        # Check if only the command was typed
        if member is None:
            await ctx.send("Did you mean ,fm or are you saying fuck nigga.")
            return

        try:
            filename = f"{self.config_folder}/{ctx.guild.name}_forced_nicks.json"
            forced_nicks = self.load_json(filename)
            
            if forced_nick is None:
                if str(member.id) in forced_nicks:
                    del forced_nicks[str(member.id)]
                    self.save_json(forced_nicks, filename)
                    await member.edit(nick=None)
                    await ctx.send(f"Removed forced nickname for {member.mention}.")
                else:
                    await ctx.send(f"{member.mention} doesn't have a forced nickname.")
                return

            forced_nicks[str(member.id)] = forced_nick
            self.save_json(forced_nicks, filename)
            
            await member.edit(nick=forced_nick)
            await ctx.send(f"Forced nickname for {member.mention} set to `{forced_nick}`.")
            
        except discord.HTTPException:
            await ctx.send("Failed to modify the nickname. Please try again.")

    @Cog.listener()
    async def on_member_update(self, before, after):
        """Monitors nickname changes and enforces forced nicknames."""
        if before.nick != after.nick:
            filename = f"{self.config_folder}/{before.guild.id}_forced_nicks.json"
            forced_nicks = self.load_json(filename)
            
            forced_nick = forced_nicks.get(str(before.id))
            if forced_nick and after.nick != forced_nick:
                try:
                    await after.edit(nick=forced_nick)
                except discord.HTTPException:
                    pass

    @commands.group(name="purge", invoke_without_command=True)
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        """Purges a specified number of messages from the channel (1-1000), or filters by user or message ID."""
        if amount and 1 <= amount <= 1000:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        else:
            await ctx.send("Please specify a valid subcommand: `from`, `before`, or `after`.", delete_after=5)

    @purge.command(name="from")
    @has_permissions(manage_messages=True)
    async def purge_from(self, ctx, user: discord.User):
        """Purges the last 50 messages from a mentioned user."""
        messages = [message async for message in ctx.channel.history(limit=50)]
        user_messages = [message for message in messages if message.author == user]

        if user_messages:
            await ctx.channel.delete_messages(user_messages)
            await ctx.send(f"Deleted {len(user_messages)} messages", delete_after=5)
        else:
            await ctx.send(f"No messages found from {user.mention}.", delete_after=5)

    @purge.command(name="before")
    @has_permissions(manage_messages=True)
    async def purge_before(self, ctx, message_id: int):
        """Purges messages before a specified message ID."""
        message = await ctx.channel.fetch_message(message_id)
        deleted = await ctx.channel.purge(limit=1000, before=message, oldest_first=True)
        await ctx.send(f"Deleted {len(deleted)} messages", delete_after=5)

    @purge.command(name="after")
    @has_permissions(manage_messages=True)
    async def purge_after(self, ctx, message_id: int):
        """Purges messages after a specified message ID."""
        message = await ctx.channel.fetch_message(message_id)
        deleted = await ctx.channel.purge(limit=1000, after=message, oldest_first=True)
        await ctx.send(f"Deleted {len(deleted)} messages", delete_after=5)

    @command(name="bc", aliases=['cleanup'], help="Clears recent bot messages and user-triggered bot replies.")
    @has_permissions(manage_messages=True)
    async def bc(self, ctx):
        """Purges the last 50 bot messages and messages that triggered the bot."""
        try:
            messages = [message async for message in ctx.channel.history(limit=50)]
            messages_to_delete = []
            for message in messages:
                if message.author == ctx.bot.user or message.author.id in self.users_triggered_bot:
                    messages_to_delete.append(message)

            if messages_to_delete:
                await ctx.channel.delete_messages(messages_to_delete)
                await ctx.send(f"Deleted {len(messages_to_delete)} messages.", delete_after=5)
            else:
                await ctx.send("No bot-related messages or user-triggered replies found.", delete_after=5)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @command(name="s", aliases=['snipe'], help="Snipes recently deleted messages")
    @has_permissions(send_messages=True)
    async def snipe(self, ctx, number: int = 1):
        """Snipe the specified deleted message number."""
        sniped_messages = self.sniped_messages.get(ctx.channel.id, [])
        
        if not sniped_messages:
            await ctx.send("No deleted messages found in the past 2 hours!")
            return
        
        if number < 1 or number > len(sniped_messages):
            await ctx.send(f"Please specify a number between 1 and {len(sniped_messages)}.")
            return

        sniped_message = sniped_messages[number - 1]

        embed = discord.Embed(
            title=f"Message sniped from {sniped_message.author}",
            description=sniped_message.content,
            color=discord.Color.green()
        )

        if sniped_message.attachments:
            embed.set_image(url=sniped_message.attachments[0].url)

        embed.set_footer(text=f"Message sniped {number}/{len(sniped_messages)}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @command(name="es")
    @has_permissions(send_messages=True)
    async def edit_snipe(self, ctx):
        """Snipe the last edited message."""
        sniped_edit = self.edited_messages.get(ctx.channel.id)
        
        if sniped_edit:
            before, after = sniped_edit
            embed = discord.Embed(
                title=f"Edited message from {before.author}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            embed.set_footer(text=f"Sniped by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("There's no recently edited message to snipe.")

    @command(name="cs")
    @has_permissions(manage_messages=True)
    async def clear_snipe(self, ctx):
        """Clear the snipe history."""
        if ctx.channel.id in self.sniped_messages:
            self.sniped_messages[ctx.channel.id].clear()
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("‼️")

    @command(name="ce")
    @has_permissions(manage_messages=True)
    async def clear_edit_snipe(self, ctx):
        """Clear the edit snipe history."""
        if ctx.channel.id in self.edited_messages:
            del self.edited_messages[ctx.channel.id]
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("‼️")

    @command(name="nuke", aliases=['arab', 'twintowers', 'hiroshima', 'nagasaki', 'japan1945', 'ww2', 'boomboom'])
    @has_permissions(administrator=True)
    async def nuke(self, ctx):
        """Nukes the current channel with confirmation."""
        # Create a confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self, ctx, original_channel):
                super().__init__()
                self.ctx = ctx
                self.original_channel = original_channel

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
            async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Ensure the interaction user is the command invoker
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                    return

                # Get channel properties
                category = self.original_channel.category
                position = self.original_channel.position
                topic = self.original_channel.topic
                nsfw = self.original_channel.is_nsfw()
                overwrites = self.original_channel.overwrites

                # Delete the original channel
                await self.original_channel.delete()

                # Recreate the channel with the same properties
                new_channel = await self.ctx.guild.create_text_channel(
                    name=self.original_channel.name,
                    category=category,
                    position=position,
                    topic=topic,
                    nsfw=nsfw,
                    overwrites=overwrites
                )

                # Create and send an embed in the new channel
                embed = discord.Embed(
                    title="Channel Nuked", 
                    description=f"This channel was nuked by {self.ctx.author.mention}",
                    color=discord.Color.red()
                )
                await new_channel.send(embed=embed)


            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.green)
            async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Ensure the interaction user is the command invoker
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                    return

                await interaction.response.send_message("Nuke cancelled.", ephemeral=True)
                await interaction.message.delete()

        # Send the confirmation message with an embed
        embed = discord.Embed(
            title="Nuke Confirmation", 
            description="Are you sure you want to nuke this channel? This will delete and recreate the channel.",
            color=discord.Color.red()
        )
        
        # Create and send the view with the embed
        view = ConfirmView(ctx, ctx.channel)
        await ctx.send(embed=embed, view=view)

    @command(name="mem-role")
    @has_permissions(administrator=True)
    async def set_member_role(self, ctx, role: discord.Role):
        """Sets the member role for the server and saves it in a unique file for each guild."""
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = {"member_role_id": role.id}
        self.save_json(data, filename)

        embed = discord.Embed(
            title="Member Role Set",
            description=f"Member role for **{ctx.guild.name}** has been set to **{role.name}**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.send(embed=embed)

    @command(name="access-role")
    @has_permissions(administrator=True)
    async def set_access_role(self, ctx, role: discord.Role):
        """Sets the access role for the server and saves it in a unique file for each guild."""
        filename = f"{self.config_folder}/{ctx.guild.name}_access_role.json"
        data = {"access_role_id": role.id}
        self.save_json(data, filename)

        embed = discord.Embed(
            title="Access Role Set",
            description=f"Access role for **{ctx.guild.name}** has been set to **{role.name}**.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.send(embed=embed)

    @command(name="lock")
    @has_permissions(manage_channels=True)
    async def lock_channel(self, ctx, channel: discord.TextChannel = None):
        """Locks a specified or current channel."""
        channel = channel or ctx.channel
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            member_role = ctx.guild.get_role(member_role_id)
            if member_role:
                await channel.set_permissions(member_role, send_messages=False)
            await ctx.send(f"👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="unlock")
    @has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx, channel: discord.TextChannel = None):
        """Unlocks a specified or current channel."""
        channel = channel or ctx.channel
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            member_role = ctx.guild.get_role(member_role_id)
            if member_role:
                await channel.set_permissions(member_role, send_messages=True)
            await ctx.send(f"👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="access")
    @has_permissions(manage_channels=True)
    async def grant_access(self, ctx, channel: discord.TextChannel):
        """Grants access to a channel for the access role."""
        filename = f"{self.config_folder}/{ctx.guild.name}_access_role.json"
        data = self.load_json(filename)
        access_role_id = data.get("access_role_id")

        if access_role_id:
            access_role = ctx.guild.get_role(access_role_id)
            await channel.set_permissions(access_role, view_channel=True, send_messages=True)
            await ctx.send(f"👍")
        else:
            await ctx.send("Access role is not set. Use `access-role` to set it first.")

    @command(name="exempt-user")
    @has_permissions(manage_channels=True)
    async def exempt_user(self, ctx, target: discord.Member):
        """Exempts a user from lockdown."""
        pass

    @command(name="hide")
    @has_permissions(manage_channels=True)
    async def hide_channel(self, ctx, channel: discord.TextChannel = None):
        """Hides the current or specified channel from @everyone and member role."""
        channel = channel or ctx.channel
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            await channel.set_permissions(ctx.guild.default_role, view_channel=False)
            member_role = ctx.guild.get_role(member_role_id)
            if member_role:
                await channel.set_permissions(member_role, view_channel=False)
            await ctx.send(f"👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="hide-all")
    @has_permissions(administrator=True)
    async def hide_all_channels(self, ctx):
        """Hides all channels from @everyone and member role."""
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            member_role = ctx.guild.get_role(member_role_id)
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(ctx.guild.default_role, view_channel=False)
                if member_role:
                    await channel.set_permissions(member_role, view_channel=False)
            await ctx.send("👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="unhide")
    @has_permissions(manage_channels=True)
    async def unhide_channel(self, ctx, channel: discord.TextChannel = None):
        """Unhides the current or specified channel."""
        channel = channel or ctx.channel
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            await channel.set_permissions(ctx.guild.default_role, view_channel=True)
            member_role = ctx.guild.get_role(member_role_id)
            if member_role:
                await channel.set_permissions(member_role, view_channel=True)
            await ctx.send(f"👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="unhide-all")
    @has_permissions(administrator=True)
    async def unhide_all_channels(self, ctx):
        """Unhides all channels from @everyone and member role."""
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            member_role = ctx.guild.get_role(member_role_id)
            for channel in ctx.guild.text_channels:
                await channel.set_permissions(ctx.guild.default_role, view_channel=True)
                if member_role:
                    await channel.set_permissions(member_role, view_channel=True)
            await ctx.send("👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="lockdown")
    @has_permissions(administrator=True)
    async def lockdown_all(self, ctx):
        """Locks and hides all channels in the server."""
        await self.lock_all_channels(ctx)
        await self.hide_all_channels(ctx)
        await ctx.send("👍")

    @command(name="create-backup")
    @has_permissions(administrator=True)
    async def backup(self, ctx):
        """Creates a backup file of the current channel permissions."""
        backup_data = {}
        for channel in ctx.guild.text_channels:
            perms = channel.overwrites_for(ctx.guild.default_role)
            backup_data[channel.id] = {
                "send_messages": perms.send_messages,
                "view_channel": perms.view_channel
            }
        filename = f"{self.backup_folder}/{ctx.guild.name}_backup.json"
        self.save_json(backup_data, filename)
        await ctx.send(f"Backup created for {ctx.guild.name}.")

    @command(name="restore")
    @has_permissions(administrator=True)
    async def restore(self, ctx):
        """Restores channel permissions from a specified backup file (uploaded as a JSON file)."""

        await ctx.send("Please upload the backup file as a JSON attachment in response to this message.")

        def check(m):
            return (
                m.author == ctx.author
                and m.channel == ctx.channel
                and m.attachments
                and m.attachments[0].filename.endswith(".json")
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            backup_file = await msg.attachments[0].read()
            backup_data = self.load_json_from_file(io.BytesIO(backup_file))
            
            if not backup_data:
                await ctx.send("Failed to load backup data. Please ensure it's a valid JSON file.")
                return

            for channel_id, perms in backup_data.items():
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    await channel.set_permissions(
                        ctx.guild.default_role,
                        send_messages=perms.get("send_messages"),
                        view_channel=perms.get("view_channel")
                    )

            await ctx.send(f"Permissions restored for `{ctx.guild.name}` from the uploaded backup file.")

        except asyncio.TimeoutError:
            await ctx.send("No file was uploaded in time. Please try the restore command again.")

    @command(name="lock-all")
    @has_permissions(administrator=True)
    async def lock_all_channels(self, ctx):
        """Locks all channels in the server, skipping exempted channels."""
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            member_role = ctx.guild.get_role(member_role_id)
            for channel in ctx.guild.text_channels:
                if channel.id not in self.exempt_channels:
                    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
                    if member_role:
                        await channel.set_permissions(member_role, send_messages=False)
            await ctx.send("👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="unlock-all")
    @has_permissions(administrator=True)
    async def unlock_all_channels(self, ctx):
        """Unlocks all channels in the server, skipping exempted channels."""
        filename = f"{self.config_folder}/{ctx.guild.name}_member_role.json"
        data = self.load_json(filename)
        member_role_id = data.get("member_role_id")

        if member_role_id:
            member_role = ctx.guild.get_role(member_role_id)
            for channel in ctx.guild.text_channels:
                if channel.id not in self.exempt_channels:
                    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
                    if member_role:
                        await channel.set_permissions(member_role, send_messages=True)
            await ctx.send("👍")
        else:
            await ctx.send("Member role is not set. Use `mem-role` to set it first.")

    @command(name="ignore", aliases= ['exempt'])
    @has_permissions(manage_channels=True)
    async def exempt_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Exempts a channel from being locked or unlocked.
        """
        channel = channel or ctx.channel

        if channel.id in self.exempt_channels:
            self.exempt_channels.remove(channel.id)
            await ctx.send(f"🚫 {channel.mention} is no longer exempted.")
        else:
            self.exempt_channels.add(channel.id)
            await ctx.send(f"✅ {channel.mention} will now be ignored during lockdown.")

    @command(name="jail-setup")
    @has_permissions(administrator=True)
    async def jail_setup(self, ctx):
        """Sets up the jail system with required roles and channels."""
        guild = ctx.guild

        jail_category = discord.utils.get(guild.categories, name="Jail")
        if not jail_category:
            jail_category = await guild.create_category("Jail")
        
        jail_channel = discord.utils.get(guild.text_channels, name="jail")
        if not jail_channel:
            jail_channel = await jail_category.create_text_channel("jail")
        
        jail_logs_channel = discord.utils.get(guild.text_channels, name="jail-logs")
        if not jail_logs_channel:
            jail_logs_channel = await jail_category.create_text_channel("jail-logs")

        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        if not jailed_role:
            jailed_role = await guild.create_role(name="Jailed")

        for channel in guild.channels:
            await channel.set_permissions(jailed_role, read_messages=False, send_messages=False)
        
        await jail_channel.set_permissions(jailed_role, read_messages=True, send_messages=True)

        await ctx.send("Jail setup completed successfully.")

    @command(name="jail")
    @has_permissions(moderate_members=True)
    async def jail(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Jails a user, applying the jailed role and logging the event."""
        if not self.can_moderate(ctx.author, member):
            return await ctx.send("You cannot jail this user due to role hierarchy!")

        guild = ctx.guild
        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        jail_logs_channel = discord.utils.get(guild.text_channels, name="jail-logs")

        if not jailed_role:
            await ctx.send("Jailed role does not exist. Run `,jail setup` first.")
            return
        if not jail_logs_channel:
            await ctx.send("Jail logs channel does not exist. Run `,jail setup` first.")
            return

        await member.add_roles(jailed_role)

        self.case_count += 1

        embed = discord.Embed(title="Jail-Logs Entry", color=discord.Color.green())
        embed.add_field(name="Information", value=(
            f"**Case #{self.case_count} | Jail**\n"
            f"**User:** {member.mention} (`{member.id}`)\n"
            f"**Moderator:** {ctx.author.mention} (`{ctx.author.id}`)\n"
            f"**Reason:** {reason}\n"
            f"{datetime.utcnow().strftime('%m/%d/%y %I:%M %p')} UTC"
        ))
        await jail_logs_channel.send(embed=embed)
        await ctx.send("👍")

    @command(name="unjail")
    @has_permissions(moderate_members=True)
    async def unjail(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Removes the jailed role from a user and logs the event."""
        guild = ctx.guild
        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        jail_logs_channel = discord.utils.get(guild.text_channels, name="jail-logs")

        if not jailed_role:
            await ctx.send("Jailed role does not exist.")
            return
        if not jail_logs_channel:
            await ctx.send("Jail logs channel does not exist.")
            return

        await member.remove_roles(jailed_role)

        self.case_count += 1

        embed = discord.Embed(title="Jail-Logs Entry", color=discord.Color.green())
        embed.add_field(name="Information", value=(
            f"**Case #{self.case_count} | Remove Jail**\n"
            f"**User:** {member.mention} (`{member.id}`)\n"
            f"**Moderator:** {ctx.author.mention} (`{ctx.author.id}`)\n"
            f"**Reason:** {reason}\n"
            f"{datetime.utcnow().strftime('%m/%d/%y %I:%M %p')} UTC"
        ))
        await jail_logs_channel.send(embed=embed)
        await ctx.send("👍")

    @command(name="sb")
    async def sb(self, ctx, member: discord.Member):
        """Adds or removes a user from the selfbot list."""
        selfbots = self.load_selfbots()

        if member.id in selfbots:
            selfbots.remove(member.id)
            action = "removed"
        else:
            selfbots.append(member.id)
            action = "added"

        self.save_selfbots(selfbots)
        await ctx.send(f"{member.mention} has been {action} to the ignorant little fuck list.")

    @command(name="filter")
    @has_permissions(manage_guild=True)
    async def filter(self, ctx, action: str = None, *, keyword: str = None):
        """
        Manage AutoMod keyword filters.
        Usage:
        ,filter add <keyword> - Add a keyword filter
        ,filter remove <keyword> - Remove a keyword filter
        ,filter list - List all current filters
        """
        if not action:
            await ctx.send("Please specify an action: `add`, `remove`, or `list`")
            return

        action = action.lower()

        if action == "add" and keyword:
            try:
                existing_rules = await ctx.guild.fetch_automod_rules()
                hvam_rule = discord.utils.get(existing_rules, name="HVAM")

                if hvam_rule:
                    current_keywords = hvam_rule.trigger_metadata.get("keyword_filter", [])
                    if keyword in current_keywords:
                        await ctx.reply(f"The keyword `{keyword}` is already filtered.")
                        return
                    
                    current_keywords.append(keyword)
                    await hvam_rule.edit(
                        trigger_metadata={"keyword_filter": current_keywords}
                    )
                    await ctx.reply(f"Added `{keyword}` to the filter list.")
                else:
                    await ctx.guild.create_automod_rule(
                        name="HVAM",
                        event_type=AutoModRuleEventType.message_send,
                        trigger=AutoModRuleTriggerType.keyword,
                        metadata={
                            "keyword_filter": [keyword],
                            "regex_patterns": []
                        },
                        actions=[
                            AutoModRuleAction(
                                type=1
                            )
                        ],
                        enabled=True,
                        exempt_roles=[],
                        exempt_channels=[],
                    )
                    await ctx.reply(f"Created new filter with keyword: `{keyword}`")

            except discord.Forbidden:
                await ctx.reply("I don't have permission to manage AutoMod rules.")
            except discord.HTTPException as e:
                await ctx.reply(f"Failed to update filter: {e}")

        elif action == "remove" and keyword:
            try:
                existing_rules = await ctx.guild.fetch_automod_rules()
                hvam_rule = discord.utils.get(existing_rules, name="HVAM")

                if not hvam_rule:
                    await ctx.reply("No filter rules found.")
                    return

                current_keywords = hvam_rule.trigger_metadata.get("keyword_filter", [])
                if keyword not in current_keywords:
                    await ctx.reply(f"The keyword `{keyword}` is not in the filter list.")
                    return

                current_keywords.remove(keyword)
                
                if current_keywords:
                    await hvam_rule.edit(
                        trigger_metadata={"keyword_filter": current_keywords}
                    )
                    await ctx.reply(f"Removed `{keyword}` from the filter list.")
                else:
                    await hvam_rule.delete()
                    await ctx.reply("Removed the last keyword and deleted the filter rule.")

            except discord.Forbidden:
                await ctx.reply("I don't have permission to manage AutoMod rules.")
            except discord.HTTPException as e:
                await ctx.reply(f"Failed to update filter: {e}")

        elif action == "list":
            try:
                existing_rules = await ctx.guild.fetch_automod_rules()
                hvam_rule = discord.utils.get(existing_rules, name="HVAM")

                if not hvam_rule:
                    await ctx.reply("No filter rules found.")
                    return

                keywords = hvam_rule.trigger_metadata.get("keyword_filter", [])
                if not keywords:
                    await ctx.reply("No keywords in the filter list.")
                    return

                embed = discord.Embed(
                    title="Filtered Keywords",
                    color=discord.Color.blue(),
                    description="\n".join(f"• `{keyword}`" for keyword in keywords)
                )
                await ctx.reply(embed=embed)

            except discord.Forbidden:
                await ctx.reply("I don't have permission to view AutoMod rules.")
            except discord.HTTPException as e:
                await ctx.reply(f"Failed to fetch filter list: {e}")

        else:
            await ctx.send("Invalid action. Use `add`, `remove`, or `list`.")

    @command(name="automod")
    async def automod(self, ctx):
        """Create 5 AutoMod rules with random jumbled letters."""
        try:
            for i in range(5):
                random_keyword = generate_random_string()

                await ctx.guild.auto_moderation_rules.create(
                    name=f"Automod Rule {i + 1}",
                    event_type=1,
                    trigger_type=1,
                    trigger_metadata={
                        "keyword_filter": [random_keyword],
                    },
                    actions=[
                        discord.AutoModerationAction(type=1),
                    ],
                    enabled=True,
                    exempt_roles=[],
                    exempt_channels=[],
                )

                print(f"Automod Rule {i + 1} created with keyword: {random_keyword}")
                await asyncio.sleep(3)

            await ctx.reply("5 AutoMod rules have been created with random keywords.")

        except discord.HTTPException as error:
            print(f"Error creating rules: {error}")
            await ctx.reply(f"There was an error creating the AutoMod rules: `{error.response['message']}`")
        except Exception as error:
            print(f"Unexpected error: {error}")
            await ctx.reply(f"There was an unexpected error: `{error}`")

    @command(name="rs", help="Snipes the last removed reaction in the channel.")
    @has_permissions(send_messages=True)
    async def reaction_snipe(self, ctx):
        """Snipes the last removed reaction and sends it in an embed."""
        sniped_reactions = self.sniped_reactions.get(ctx.channel.id, [])
        
        if not sniped_reactions:
            await ctx.send("No reactions have been removed recently in this channel.")
            return
        
        reaction, user = sniped_reactions[-1]

        embed = discord.Embed(
            title=f"Reaction sniped from {user.display_name}",
            description=f"Reaction `{reaction.emoji}` removed by {user.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Sniped by {ctx.author}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)

    @command(name="createinvite")
    @has_permissions(create_instant_invite=True)
    async def create_invite(self, ctx):
        """Creates an invite link with a 7-day expiry and unlimited uses."""
        try:
            invite = await ctx.channel.create_invite(
                max_age=604800,
                max_uses=0
            )
            await ctx.send(f"Here is your invite link: {invite.url}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to create invites in this channel.")
        except discord.HTTPException:
            await ctx.send("There was an error creating the invite link.")

    @command(name='unbanall', aliases=['massunban', 'uba'], description="Unbans all members in the server.")
    @has_permissions(administrator=True)
    async def unban_all(self, ctx):
        """Unban all members from the server."""
        unbanned_count = 0

        try:
            bans = [ban async for ban in ctx.guild.bans()]
            for ban_entry in bans:
                user = ban_entry.user
                try:
                    await ctx.guild.unban(user, reason="Unbanned by " + ctx.author.mention)
                    
                    unbanned_count += 1
                except Exception as e:
                    await ctx.send(f"Failed to unban {user}: {e}")

            await ctx.send(embed=discord.Embed(
                title="Unban All Complete",
                description=f"Unbanned {unbanned_count} users.",
                color=discord.Color.green()
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while fetching the ban list: {e}",
                color=discord.Color.red()
            ))

    @command(name='banlist', aliases=['bans'], description="Displays the server's ban list.")
    @has_permissions(administrator=True)
    async def ban_list(self, ctx):
        """Display the server's ban list in a paginated embed."""
        try:
            bans = [ban async for ban in ctx.guild.bans()]
            if not bans:
                await ctx.send("There are no banned users in this server.")
                return

            view = BanListView(bans, ctx.author)
            embed = view.get_embed()
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while fetching the ban list: {e}",
                color=discord.Color.red()
            ))

    @Cog.listener()
    async def on_member_update(self, before, after):
        """Monitors nickname changes and enforces forced nicknames."""
        if before.nick != after.nick:
            filename = f"{self.config_folder}/{before.guild.id}_forced_nicks.json"
            forced_nicks = self.load_json(filename)
            
            forced_nick = forced_nicks.get(str(before.id))
            if forced_nick and after.nick != forced_nick:
                try:
                    await after.edit(nick=forced_nick)
                except discord.HTTPException:
                    pass

    @commands.command(name="immunity")
    async def immunity(self, ctx, user_id: int = None):
        """
        Manages the list of immune users.
        Only a specific user can use this command.
        """
        # Specify the user ID who can use this command
        AUTHORIZED_USER_ID = 785042666475225109

        # Check if the command invoker is the authorized user
        if ctx.author.id != AUTHORIZED_USER_ID:
            await ctx.send("This command can only be ran by <@785042666475225109>")
            return

        # If no user ID is provided, show the current immune users
        if user_id is None:
            if not hasattr(self.bot, 'immune_users'):
                self.bot.immune_users = set()
            
            if not self.bot.immune_users:
                await ctx.send("No users currently have immunity.")
                return
            
            # Create an embed to display immune users
            embed = discord.Embed(
                title="Immune Users", 
                description=f"Total Immune Users: {len(self.bot.immune_users)}",
                color=discord.Color.green()
            )
            
            # Try to get usernames for each ID
            for uid in list(self.bot.immune_users):
                try:
                    member = await ctx.guild.fetch_member(uid)
                    embed.add_field(
                        name=member.name, 
                        value=f"ID: `{uid}`", 
                        inline=False
                    )
                except:
                    # If user can't be fetched, just show ID
                    embed.add_field(
                        name="Unknown User", 
                        value=f"ID: `{uid}`", 
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            return

        # Ensure immune_users exists
        if not hasattr(self.bot, 'immune_users'):
            self.bot.immune_users = set()

        # Check if the user is already in the list
        if user_id in self.bot.immune_users:
            self.bot.immune_users.remove(user_id)
            await ctx.send(f"User ID {user_id} has been removed from the immunity list.")
        else:
            self.bot.immune_users.add(user_id)
            await ctx.send(f"User ID {user_id} has been added to the immunity list.")

    async def check_ban_prevention(self, guild, user):
        """
        Check if a user should be prevented from being banned.
        """
        # Check if the user ID is in the unbannable list
        if user.id in self.unbannable_user_ids:
            return True
        return False

    @commands.Cog.listener()
    async def on_guild_ban(self, guild, user):
        """
        Listener for guild bans to prevent banning immune users.
        """
        # Check if the ban should be prevented
        if await self.check_ban_prevention(guild, user):
            # Attempt to unban the user
            try:
                await guild.unban(user, reason="User has immunity")
            except Exception as e:
                print(f"Error unbanning immune user: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        role_id = None

        if member.bot:
            query = "SELECT role_id FROM autorole_bots WHERE guild_id = $1"
        else:
            query = "SELECT role_id FROM autorole_humans WHERE guild_id = $1"

        async with self.bot.db.acquire() as conn:
            result = await conn.fetchrow(query, guild_id)
            if result:
                role_id = result["role_id"]

        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)
                print(f"Assigned role {role.name} to {'bot' if member.bot else 'human'} {member.name}.")

    async def send_embed(self, ctx, message: str):
        embed = discord.Embed(description=message, color=0xADD8E6)
        await ctx.send(embed=embed)

    @tasks.loop(minutes=120)
    async def snipe_reset(self):
        """Clears all sniped messages every 2 hours."""
        self.sniped_messages.clear()

    async def cog_load(self):
        """Create necessary database tables when the cog loads."""
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS autorole_humans (
                    guild_id BIGINT PRIMARY KEY,
                    role_id BIGINT NOT NULL
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS autorole_bots (
                    guild_id BIGINT PRIMARY KEY,
                    role_id BIGINT NOT NULL
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    author_id BIGINT NOT NULL,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add this to your database initialization
            CREATE_ANTINUKE_TABLE = """
            CREATE TABLE IF NOT EXISTS antinuke_admins (
                guild_id BIGINT,
                user_id BIGINT,
                PRIMARY KEY (guild_id, user_id)
            );
            """

            # In your setup or init function where you create tables:
            await self.bot.db.execute(CREATE_ANTINUKE_TABLE)

    @commands.hybrid_command(name="staffstrip", description="Strips a user of all their moderation-related roles")
    @commands.has_permissions(administrator=True)
    async def staff_strip(self, ctx, member: discord.Member):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.message.add_reaction("‼️")
        
        mod_permissions = [
            'kick_members',
            'ban_members',
            'manage_channels',
            'manage_guild',
            'manage_messages',
            'manage_roles',
            'manage_webhooks',
            'moderate_members',
            'view_audit_log',
            'administrator'
        ]

        mod_roles = []
        removed_roles = []
        modified_roles = []

        for role in member.roles:
            if role == ctx.guild.default_role:
                continue
                
            role_perms = role.permissions
            for perm in mod_permissions:
                if getattr(role_perms, perm):
                    mod_roles.append(role)
                    break

        if not mod_roles:
            return await ctx.message.add_reaction("‼️")

        for role in mod_roles:
            try:
                if role.is_bot_managed():
                    perms = discord.Permissions()
                    await role.edit(permissions=perms, reason=f"Staff strip by {ctx.author}")
                    modified_roles.append(role)
                else:
                    await member.remove_roles(role, reason=f"Staff strip by {ctx.author}")
                    removed_roles.append(role)
            except (discord.Forbidden, discord.HTTPException):
                continue

        if not (removed_roles or modified_roles):
            return await ctx.message.add_reaction("‼️")

        embed = discord.Embed(
            title="Staff Strip Successful",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Target", value=f"{member.mention} ({member.id})", inline=False)
        
        if removed_roles:
            embed.add_field(
                name="Removed Roles", 
                value="\n".join([f"• {role.mention}" for role in removed_roles]),
                inline=False
            )
        if modified_roles:
            embed.add_field(
                name="Modified Roles (Permissions Removed)", 
                value="\n".join([f"• {role.mention}" for role in modified_roles]),
                inline=False
            )
            
        embed.add_field(name="Stripped by", value=f"{ctx.author.mention} ({ctx.author.id})")

        await ctx.message.add_reaction("✅")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rr", description="Restores roles removed from a user in the last hour")
    @commands.has_permissions(administrator=True)
    async def restore_roles(self, ctx, member: discord.Member):
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.message.add_reaction("‼️")

        one_hour_ago = discord.utils.utcnow() - timedelta(hours=1)
        roles_to_restore = []
        
        try:
            async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=None):
                if entry.created_at < one_hour_ago:
                    break
                    
                if entry.target and entry.target.id == member.id:
                    if entry.changes.before.roles:
                        for role in entry.changes.before.roles:
                            if role not in member.roles and role < ctx.author.top_role:
                                roles_to_restore.append(role)

            if not roles_to_restore:
                return await ctx.message.add_reaction("‼️")

            roles_to_restore = list(dict.fromkeys(roles_to_restore))
            
            try:
                await member.add_roles(*roles_to_restore, reason=f"Role restoration by {ctx.author}")
                
                embed = discord.Embed(
                    title="Roles Restored",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="Target", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(
                    name="Restored Roles",
                    value="\n".join([f"• {role.mention}" for role in roles_to_restore]),
                    inline=False
                )
                embed.add_field(name="Restored by", value=f"{ctx.author.mention} ({ctx.author.id})")
                
                await ctx.message.add_reaction("✅")
                await ctx.send(embed=embed)
                
            except (discord.Forbidden, discord.HTTPException):
                await ctx.message.add_reaction("‼️")
                
        except discord.Forbidden:
            await ctx.message.add_reaction("‼️")

    @commands.group(name="channel", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def channel_group(self, ctx):
        """Channel management command group"""
        embed = discord.Embed(
            title="Channel Management Commands",
            description=(
                "Available commands:\n"
                "- `,channel create <name>` - Create a new text channel\n"
                "- `,channel delete <name>` - Delete a channel\n"
                "- `,channel rename <new_name>` - Rename current channel\n"
                "- `,channel private <name>` - Create a private channel\n"
                "- `,channel topic <new_topic>` - Set channel topic\n"
                "- `,channel clone` - Clone current channel\n"
                "- `,channel sync <category>` - Sync channel permissions with a category"
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @channel_group.command(name="create")
    @commands.has_permissions(manage_channels=True)
    async def channel_create(self, ctx, name: str, category: discord.CategoryChannel = None):
        """Create a new text channel"""
        try:
            # Sanitize channel name
            name = name.lower().replace(' ', '-')
            
            # Create channel
            new_channel = await ctx.guild.create_text_channel(
                name=name, 
                category=category
            )
            
            await ctx.send(f"Created text channel {new_channel.mention}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to create channels.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create channel: {str(e)}")

    @channel_group.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def channel_delete(self, ctx, channel: discord.TextChannel = None):
        """Delete a channel"""
        # Use current channel if no channel specified
        channel = channel or ctx.channel
        
        try:
            await channel.delete()
            if channel != ctx.channel:
                await ctx.send(f"Deleted channel #{channel.name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to delete channel: {str(e)}")

    @channel_group.command(name="rename")
    @commands.has_permissions(manage_channels=True)
    async def channel_rename(self, ctx, *, new_name: str):
        """Rename the current channel"""
        try:
            # Sanitize channel name
            new_name = new_name.lower().replace(' ', '-')
            
            await ctx.channel.edit(name=new_name)
            await ctx.send(f"Channel renamed to #{new_name}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to rename this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to rename channel: {str(e)}")

    @channel_group.command(name="private")
    @commands.has_permissions(manage_channels=True)
    async def channel_private(self, ctx, name: str = None):
        """Create a private channel"""
        try:
            # Use current channel name if no name provided
            name = name or f"{ctx.author.name}-private"
            
            # Sanitize channel name
            name = name.lower().replace(' ', '-')
            
            # Create private channel
            new_channel = await ctx.guild.create_text_channel(
                name=name,
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.author: discord.PermissionOverwrite(read_messages=True, manage_channels=True)
                }
            )
            
            await ctx.send(f"Created private channel {new_channel.mention}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to create private channels.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to create private channel: {str(e)}")

    @channel_group.command(name="topic")
    @commands.has_permissions(manage_channels=True)
    async def channel_topic(self, ctx, *, new_topic: str):
        """Set the topic for the current channel"""
        try:
            await ctx.channel.edit(topic=new_topic)
            await ctx.send(f"Channel topic set to: {new_topic}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to set the channel topic.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to set channel topic: {str(e)}")

    @channel_group.command(name="clone")
    @commands.has_permissions(manage_channels=True)
    async def channel_clone(self, ctx):
        """Clone the current channel"""
        try:
            new_channel = await ctx.channel.clone()
            await ctx.send(f"Cloned channel to {new_channel.mention}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to clone this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to clone channel: {str(e)}")

    @channel_group.command(name="sync")
    @commands.has_permissions(manage_channels=True)
    async def channel_sync(self, ctx, category: str = None):
        """Syncs channel permissions with the specified category or all channels if 'all' is specified."""
        if category is None:
            await ctx.send("Please provide a category or 'all'.")
            return
        
        if category.lower() == 'all':
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel) and channel.category:
                    # Sync permissions with the corresponding category as if pressing the sync button
                    await channel.edit(sync_permissions=True)
            await ctx.send("👍")  # Send thumbs up when done
        else:
            # Fetch the category by name
            category = discord.utils.get(ctx.guild.categories, name=category)
            if category:
                for channel in ctx.guild.channels:
                    if isinstance(channel, discord.TextChannel) and channel.category == category:
                        await channel.edit(sync_permissions=True)
                await ctx.send("👍")  # Send thumbs up when done
            else:
                await ctx.send("Category not found.")

    @Cog.listener()
    async def on_message(self, message):
        """Listen for messages that trigger the bot to reply, so we can track them."""
        if message.author == self.bot.user:
            return
        
        if message.reference and message.reference.message_id:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message.author == self.bot.user:
                self.users_triggered_bot.add(message.author.id)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        """Store the last edited message for snipe."""
        if before.content != after.content:
            self.edited_messages[before.channel.id] = (before, after)
    
    @Cog.listener()
    async def on_message_delete(self, message):
        """Store the last deleted message for sniping."""
        if message.channel.id not in self.sniped_messages:
            self.sniped_messages[message.channel.id] = deque(maxlen=10)
        self.sniped_messages[message.channel.id].appendleft(message)

    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Store the reaction that was removed."""
        if reaction.message.channel.id not in self.sniped_reactions:
            self.sniped_reactions[reaction.message.channel.id] = []
        
        self.sniped_reactions[reaction.message.channel.id].append((reaction, user))

    async def get_member(self, ctx, member: discord.Member = None, user_id: int = None):
        """
        Helper method to get a member either by direct mention or by user ID.
        
        Args:
            ctx (Context): The command context
            member (discord.Member, optional): The member mentioned directly
            user_id (int, optional): The user ID to fetch

        Returns:
            discord.Member or None: The resolved member, or None if not found
        """
        if member:
            return member
        
        if user_id:
            try:
                return await ctx.guild.fetch_member(user_id)
            except discord.NotFound:
                await ctx.send(f"Could not find a member with ID {user_id} in this server.")
                return None
            except discord.HTTPException:
                await ctx.send("Failed to fetch the member.")
                return None
        
        return None
