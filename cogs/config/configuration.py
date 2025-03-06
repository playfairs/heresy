import discord
import json
import os
import base64

from discord.ext.commands import Cog, command, has_permissions, Context, group
from discord import app_commands

from main import heresy

class Config(Cog, description="View commands in Config."):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.join_log_file = 'join_log_settings.json'
        self.join_log_settings = self.load_join_log_settings()
        self.log_channels = {}
        self.load_log_channels()
        self.ad_path = "cogs/config/ad.txt"

    def get_ad_message(self):
        """
        Reads the ad message from ad.txt.
        """
        try:
            with open(self.ad_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            return f"Ad file not found at {self.ad_path}. Please ensure the file exists."
        except Exception as e:
            return f"Error reading ad file: {e}"

    def load_log_channels(self):
        if os.path.isfile("mod_log_channels.json"):
            with open("mod_log_channels.json", "r") as file:
                self.log_channels = json.load(file)

    def save_log_channels(self):
        with open("mod_log_channels.json", "w") as file:
            json.dump(self.log_channels, file, indent=4)

    async def send_log(self, guild_id, embed):
        log_channel_id = self.log_channels.get(str(guild_id))
        if log_channel_id:
            log_channel = self.bot.get_channel(int(log_channel_id))
            if log_channel:
                await log_channel.send(embed=embed)

    def load_join_log_settings(self):
        if os.path.exists(self.join_log_file):
            with open(self.join_log_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_join_log_settings(self):
        with open(self.join_log_file, 'w') as f:
            json.dump(self.join_log_settings, f, indent=4)

    @group(name="gate", invoke_without_command=True)
    async def gate(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @gate.command(name="set", aliases= ["logs"])
    @has_permissions(administrator=True)
    async def set_join_logs(self, ctx: Context, channel: discord.TextChannel = None):
        """Sets the join log channel for the current server."""
        if channel is None:
            await ctx.send(f"Current gate is set to <#{self.join_log_settings[str(ctx.guild.id)].get('channel_id')}>.")
            return
        if channel.id == self.join_log_settings[str(ctx.guild.id)].get('channel_id'):
            await ctx.send(f"Gate is already set to <#{channel.id}>.")
            return
        server_id = str(ctx.guild.id)
        if server_id not in self.join_log_settings:
            self.join_log_settings[server_id] = {}
        
        self.join_log_settings[server_id]["channel_id"] = channel.id
        self.save_join_log_settings()
        await ctx.send(f"Join logs have been set to {channel.mention} for this server.")

    @gate.command(name="join", aliases= ["joinmsg", "welcmsg", "joinmessage", "welcomemessage", "welcmessage", "welc"])
    @has_permissions(administrator=True)
    async def set_join_message(self, ctx: Context, *, message: str):
        """Sets a custom welcome message for the server and displays it in an embed."""
        server_id = str(ctx.guild.id)
        if server_id not in self.join_log_settings:
            self.join_log_settings[server_id] = {}
        
        self.join_log_settings[server_id]["welcome_message"] = message
        self.save_join_log_settings()

        message = message.replace("{user.mention}", "")
        embed = discord.Embed(
            title="Welcome Message Set",
            description=message,
            color=discord.Color.green()
        )
        await ctx.send("Custom welcome message has been set.", embed=embed)

    @gate.command(name="leave", aliases= ["leavemsg"])
    @has_permissions(administrator=True)
    async def set_leave_message(self, ctx: Context, *, message: str):
        """Sets a custom leave message for the server and displays it in an embed."""
        server_id = str(ctx.guild.id)
        if server_id not in self.join_log_settings:
            self.join_log_settings[server_id] = {}
        
        self.join_log_settings[server_id]["leave_message"] = message
        self.save_join_log_settings()

        message = message.replace("{user.mention}", "")
        embed = discord.Embed(
            title="Leave Message Set",
            description=message,
            color=discord.Color.red()
        )
        await ctx.send("Custom leave message has been set.", embed=embed)
    @Cog.listener()
    async def on_member_join(self, member):
        server_id = str(member.guild.id)
        if server_id in self.join_log_settings:
            channel_id = self.join_log_settings[server_id].get("channel_id")
            welcome_message = self.join_log_settings[server_id].get(
                "welcome_message",
                f"hi",
            )
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                await channel.send((welcome_message.replace("{user.mention}", f"{member.mention}") if "{user.mention}" in welcome_message else welcome_message))

    @Cog.listener()
    async def on_member_remove(self, member):
        server_id = str(member.guild.id)
        if server_id in self.join_log_settings:
            channel_id = self.join_log_settings[server_id].get("channel_id")
            leave_message = self.join_log_settings[server_id].get(
                "leave_message",
                f"damn, they prolly wont be back",
            )
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                await channel.send((leave_message.replace("{user.mention}", f"{member.mention}") if "{user.mention}" in leave_message else leave_message))

    @gate.command(name="testmsg")
    @has_permissions(administrator=True)
    @app_commands.choices(
        message_type=[
            app_commands.Choice(name="join", value="join"),
            app_commands.Choice(name="leave", value="leave"),
        ]
    )
    async def test_message(self, interaction: discord.Interaction, message_type: app_commands.Choice[str]):
        """Tests the join or leave message using the command author as the member."""
        server_id = str(interaction.guild_id)
        if server_id not in self.join_log_settings:
            await interaction.response.send_message("Join log settings are not configured for this server.", ephemeral=True)
            return

        channel_id = self.join_log_settings[server_id].get("channel_id")
        channel = self.bot.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("The join log channel is not set or accessible.", ephemeral=True)
            return

        if message_type.value == "join":
            welcome_message = self.join_log_settings[server_id].get(
                "welcome_message",
                "hi",
            )
            await channel.send(f"{welcome_message} {interaction.user.mention}")
            await interaction.response.send_message("Join message tested.", ephemeral=True)
        elif message_type.value == "leave":
            leave_message = self.join_log_settings[server_id].get(
                "leave_message",
                "bye",
            )
            await channel.send(f"{leave_message} {interaction.user.mention}")
            await interaction.response.send_message("Leave message tested.", ephemeral=True)

    @command(name="modlogs")
    @has_permissions(administrator=True)
    async def set_modlog_channel(self, ctx: Context, channel: discord.TextChannel):
        self.log_channels[str(ctx.guild.id)] = channel.id
        self.save_log_channels()
        await ctx.send(f"Mod logs channel has been set to {channel.mention}")

    @Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            embed = discord.Embed(title="**Member Update**", color=discord.Color.blue())
            embed.add_field(name="**Responsible:**", value=f"{after.guild.me.mention} ({after.guild.me.id})")
            embed.add_field(name="**Target:**", value=f"{after.mention} ({after.id})")
            embed.add_field(name="*Time:*", value="*{0}*".format(after.joined_at.strftime('%A, %b %d, %Y %I:%M %p')))
            embed.add_field(name="**Changes**", value=f"> **Nick:** \n> {before.nick or 'None'} --> {after.nick or 'None'}", inline=False)
            await self.send_log(after.guild.id, embed)

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles or removed_roles:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        responsible_user = entry.user
                        break
                else:
                    responsible_user = after.guild.me

                embed = discord.Embed(title="**Member Role Update**", color=discord.Color.green())
                embed.add_field(name="**Responsible:**", value=f"{responsible_user.mention} ({responsible_user.id})", inline=True)
                embed.add_field(name="**Target:**", value=f"{after.mention} ({after.id})", inline=True)
                embed.add_field(name="", value=f"*{discord.utils.utcnow().strftime('%A, %B %d, %Y at %I:%M %p')}*", inline=False)
                
                changes = ""
                if added_roles:
                    changes += "**Additions:**\n" + "\n".join([f"<:right:1307448399624405134> {role.mention}" for role in added_roles])
                if removed_roles:
                    if added_roles:
                        changes += "\n\n"
                    changes += "**Removals:**\n" + "\n".join([f"<:right:1307448399624405134> {role.mention}" for role in removed_roles])
                
                embed.add_field(name="Changes", value=changes, inline=False)
                await self.send_log(after.guild.id, embed)

    @Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        embed = discord.Embed(title="**Message Deleted**", color=discord.Color.red())
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        embed.add_field(name="Message sent by", value=message.author.mention)
        embed.add_field(name="Deleted in", value=message.channel.mention)
        embed.add_field(
            name="Content", 
            value=f"```diff\n- {message.content}\n```" if message.content else "No content available", 
            inline=False
        )
        embed.add_field(name="Author ID", value=f"{message.author.id} | Message ID: {message.id}")
        await self.send_log(message.guild.id, embed)

    @Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if len(messages) == 0:
            return
        channel = messages[0].channel
        embed = discord.Embed(title="**Bulk Delete**", color=discord.Color.red())
        embed.add_field(name="Bulk Delete in", value=f"{channel.mention}, {len(messages)} messages deleted")
        embed.add_field(name="*Time:*", value="*{0}*".format(discord.utils.utcnow().strftime('%A, %b %d, %Y %I:%M %p')))
        await self.send_log(channel.guild.id, embed)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content != after.content:
            embed = discord.Embed(title="**Message Edited**", color=discord.Color.orange())
            embed.set_author(name=before.author.display_name, icon_url=before.author.avatar.url)
            embed.add_field(name="Message Edited in", value=f"{before.channel.mention} [Jump to Message]({before.jump_url})")
            embed.add_field(name="**Before:**", value=f"*{before.content}*", inline=False)
            embed.add_field(name="**After:**", value=f"*{after.content}*", inline=False)
            embed.add_field(name="User ID", value=f"{before.author.id}")
            await self.send_log(before.guild.id, embed)

    @Cog.listener()
    async def on_member_ban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                responsible_user = entry.user
                reason = entry.reason or "No reason provided"
                break
        else:
            responsible_user = guild.me
            reason = "No reason found"

        embed = discord.Embed(title="**Member Ban Add**", color=discord.Color.red())
        embed.add_field(name="**Responsible:**", value=f"{responsible_user.mention} ({responsible_user.id})")
        embed.add_field(name="**Target:**", value=f"{user.mention} ({user.id})")
        embed.add_field(name="*Time:*", value="*{0}*".format(discord.utils.utcnow().strftime('%A, %b %d, %Y %I:%M %p')))
        embed.add_field(name="**Reason:**", value=reason, inline=False)
        await self.send_log(guild.id, embed)

    @Cog.listener()
    async def on_guild_role_create(self, role):
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                responsible_user = entry.user
                break
        else:
            responsible_user = role.guild.me

        embed = discord.Embed(title="**Role Created**", color=discord.Color.green())
        embed.add_field(name="**Responsible:**", value=f"{responsible_user.mention} ({responsible_user.id})")
        embed.add_field(name="**Role Name:**", value=role.mention)
        embed.add_field(name="*Time:*", value="*{0}*".format(discord.utils.utcnow().strftime('%A, %b %d, %Y %I:%M %p')))
        
        permissions = []
        for perm, value in role.permissions:
            if value:
                permissions.append(f"{perm.replace('_', ' ').title()}")
        
        role_details = (
            f"**Color:** {role.color}\n"
            f"**Hoisted:** {'Yes' if role.hoist else 'No'}\n"
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}\n"
            f"**Position:** {role.position}\n"
            f"**ID:** {role.id}"
        )
        
        embed.add_field(name="**Role Details**", value=role_details, inline=False)
        
        if permissions:
            perm_chunks = [permissions[i:i + 15] for i in range(0, len(permissions), 15)]
            for i, chunk in enumerate(perm_chunks):
                embed.add_field(
                    name=f"**Permissions {i+1}**" if i > 0 else "**Permissions**",
                    value="\n".join(chunk),
                    inline=False
                )

        await self.send_log(role.guild.id, embed)

    @Cog.listener()
    async def on_guild_update(self, before, after):
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            responsible_user = entry.user
            break
        else:
            responsible_user = after.me

        embed = discord.Embed(title="**Guild Update**", color=discord.Color.blue())
        embed.add_field(name="**Responsible:**", value=f"{responsible_user.mention} ({responsible_user.id})")
        embed.add_field(name="*Time:*", value="*{0}*".format(discord.utils.utcnow().strftime('%A, %b %d, %Y %I:%M %p')))

        changes = []
        
        if before.name != after.name:
            changes.append(f"**Name:** {before.name} → {after.name}")
        
        if before.icon != after.icon:
            if after.icon:
                icon_data = await after.icon.read()
                icon_b64 = base64.b64encode(icon_data).decode('utf-8')
                changes.append(f"**Server Icon:** ```bash\n[Prev → [{icon_b64[:32]}...]```")
            else:
                changes.append(f"**Server Icon:** ```bash\n[Prev] → [Reset]```")
        
        if before.banner != after.banner:
            if after.banner:
                banner_data = await after.banner.read()
                banner_hash = hash(banner_data)
                changes.append(f"**Server Banner:** ```bash\n[Prevr] → [{banner_hash}]```")
            else:
                changes.append(f"**Server Banner:** ```bash\n[Prev] → [Reset]```")
        
        if before.afk_channel != after.afk_channel:
            changes.append(f"**AFK Channel:** {before.afk_channel} → {after.afk_channel}")

        if before.afk_timeout != after.afk_timeout:
            changes.append(f"**AFK Timeout:** {before.afk_timeout}s → {after.afk_timeout}s")

        if before.verification_level != after.verification_level:
            changes.append(f"**Verification Level:** {before.verification_level} → {after.verification_level}")

        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(f"**Content Filter:** {before.explicit_content_filter} → {after.explicit_content_filter}")

        if before.system_channel != after.system_channel:
            changes.append(f"**System Channel:** {before.system_channel} → {after.system_channel}")

        if changes:
            embed.add_field(name="**Changes**", value="\n".join(changes), inline=False)
            await self.send_log(after.id, embed)
