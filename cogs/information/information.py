import discord
from discord.ext import commands
from discord.ext.commands import Cog, command, Context
import difflib
import asyncio
import platform
import os
import psutil
import subprocess

from datetime import datetime, timezone
from discord import Embed, Color
from discord import app_commands
from main import heresy
from typing import Union


class Information(Cog):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.developer_id = 785042666475225109
        self.bot_id = 593921296224747521
        self.start_time = datetime.now(timezone.utc)

    @app_commands.command(name='about', description="Displays information about Playfair or heresy.")
    @app_commands.describe(option="Select either Playfair or heresy")
    @app_commands.choices(
        option=[
            app_commands.Choice(name="Playfair", value="playfair"),
            app_commands.Choice(name="heresy", value="heresy"),
        ]
    )
    async def about(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        """Displays information about Playfair or heresy in an embed."""
        option_value = option.value.lower()
        if option_value == 'playfair':
            embed = discord.Embed(
                title="About Playfair",
                description="Developer of heresy and other Discord Bots.",
                color=discord.Color.pink()
            )
            embed.add_field(name="Description", value="Playfairs, or Playfair, is the Bot Developer of this and many other bots, also being the owner of /heresy, that is all.", inline=False)
            embed.add_field(name="Useful Links", value="[Website](https://playfairs.cc)", inline=False)
            embed.set_footer(text="Requested by: {}".format(interaction.user.name))

        elif option_value == 'heresy':
            embed = discord.Embed(
                title="About heresy",
                description="An all-in-one Discord Bot meant to enhance your Discord Server. Developed and Maintained by <@785042666475225109>.",
                color=discord.Color.green()
            )
            embed.add_field(name="Developer", value="<@785042666475225109>", inline=False)
            embed.add_field(name="Description", value="heresy, originally heresy, is a all-in-one Discord Bot created by <@785042666475225109>, built for versatility", inline=False)
            embed.add_field(name="Useful Links", value="[Server](https://discord.gg/heresy) | [Website](https://playfairs.cc) | [Invite](https://discord.com/oauth2/authorize?client_id=1284037026672279635&permissions=8&integration_type=0&scope=bot)", inline=False)
            embed.set_footer(text="For more information, DM @playfairs, or check ,help for more info.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="links", description="Displays useful links.")
    async def links(self, interaction: discord.Interaction):
        """Displays useful links in an embed."""
        embed = discord.Embed(
            title="Useful Links",
            description="Hi",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Guns.lol", value="[playfair](https://guns.lol/playfair)", inline=False)
        embed.add_field(name="Wanted.lol", value="[suicideboys](https://wanted.lol/suicideboys)", inline=False)
        embed.add_field(name="About.me", value="[creepfully](https://about.me/creepfully)", inline=False)
        embed.add_field(name="TikTok", value="[playfairs](https://tiktok.com/playfairs)", inline=False)
        embed.set_footer(text="More details can be found in the about.me")
        await interaction.response.send_message(embed=embed)

    @commands.command(name="abt", hidden=True)
    async def about_bot(self, ctx):
        """Displays information about the bot."""
        embed = discord.Embed(
            title="About This Bot",
            description="heresy is a Discord Bot packed with a whole bunch of commands, designed for versatility (NOT HOSTED 24/7)",
            color=0x3498db
        )
        embed.add_field(name="Developer", value="@playfairs", inline=False)
        embed.add_field(name="Language", value="Python", inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Purpose", value="Meant for managing and adding a bit of fun to your server(s)!", inline=False)
        embed.set_footer(text="Thanks for using heresy, if you have any questions about the bot then hit up the developer and ask your questions!")
        await ctx.send(embed=embed)

    @app_commands.command(name="userinfo", description="Get information about a user")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Displays basic information about the specified user or the interaction user if no member is specified."""
        member = member or interaction.user
        embed = discord.Embed(title=f"{member}'s Info", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Name", value=member.name, inline=False)
        embed.add_field(name="Created At", value=member.created_at.strftime("%m/%d/%Y, %H:%M:%S"), inline=False)
        embed.set_thumbnail(url=member.avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="av", aliases= ['pfp', 'avatar'], description="Show your avatar.")
    async def avatar(self, ctx, member: discord.Member = None):
        """Displays the avatar of the specified user or yourself if no one is mentioned."""
        member = member or ctx.author

        if not member.avatar:
            await ctx.send(f"{member.mention} doesn't have an avatar, man, who runs around discord without an avatar.")
            return
        
        embed = discord.Embed(title=f"{member.name}'s Avatar", color=discord.Color.blue())
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else self.bot.user.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="banner", description="Show your banner.")
    async def banner(self, ctx, member: discord.Member = None):
        """Displays the banner of the specified user or yourself if no one is mentioned."""
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)

        if user.banner:
            embed = discord.Embed(title=f"{user.name}'s Banner", color=discord.Color.blue())
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{member.mention} does not have a banner.")

    @commands.command(name="sav", description="Show your server avatar.")
    async def sav(self, ctx, member: discord.Member = None):
        """Displays the server avatar of the specified user or yourself if no one is mentioned."""
        member = member or ctx.author

        if member.guild_avatar:
            embed = discord.Embed(title=f"{member.name}'s Server Avatar", color=discord.Color.blue())
            embed.set_image(url=member.guild_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{member.mention} does not have a server avatar.")

    @commands.command(name="whoid", help="Show basic information about a user not in a server by ID.")
    async def whoid(self, ctx: Context, user_id: int = None):
        """
        Displays basic user information: username, avatar, and ID.
        """
        try:
            if not user_id:
                await ctx.send("Please provide a User ID, You fucking moron, it's literally called whoID for a reason")
                return

            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                await ctx.send(f"User with ID `{user_id}` was not found.")
                return
            except discord.Forbidden:
                await ctx.send("I do not have permission to access this user.")
                return
            except discord.HTTPException:
                await ctx.send("An error occurred while fetching the user.")
                return

            created_at = user.created_at.strftime("%B %d, %Y")
            embed = discord.Embed(
                title=f"{user.name}#{user.discriminator}",
                description=f"**User ID:** `{user.id}`\n**Created At:** {created_at}",
                color=discord.Color.blue()
            )
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send("**Error**: Something went wrong.")
            raise e
    
    @commands.command(name="whois", aliases=['userinfo', 'ui', 'info', 'whoami'], help="Show detailed information about a user.")
    async def whois(self, ctx, member: discord.Member = None):
        """
        Displays detailed user information with badges, activity, and roles.
        """
        try:
            member = member or ctx.author
            if member.id == self.bot_id:
                await ctx.send("no")
                return
            developer_title = " - Developer" if member.id == self.developer_id else ""

            badges = []
            # Discord Staff Badge
            if member.public_flags.staff:
                badges.append("<:staff:1297931763229917246>")
            
            # Partner Badge
            if member.public_flags.partner:
                badges.append("<:partner:1297931370357723198>")
            
            # Hypesquad Events Badge
            if member.public_flags.hypesquad:
                badges.append("<:hypesquad:1297930974633398293>")
            
            # Bug Hunter Badges
            if member.public_flags.bug_hunter_level_2:
                badges.append("<:bug_hunter_level_2:1297931831521312850>")
            elif member.public_flags.bug_hunter:
                badges.append("<:bug_hunter:1297931813121036321>")
            
            # Early Supporter Badge
            if member.public_flags.early_supporter:
                badges.append("<:early_supporter:1297931252158042283>")
            
            # Verified Bot Developer Badge
            if member.public_flags.verified_bot_developer:
                badges.append("<:verified_bot_developer:1297931270139150338>")
            
            # Discord Certified Moderator Badge
            if member.public_flags.discord_certified_moderator:
                badges.append("<:certified_moderator:1297932110514098290>")
            
            # Active Developer Badge
            if member.public_flags.active_developer:
                badges.append("<:active_developer:1297930880987431035>")
            
            # HypeSquad House Badges
            if member.public_flags.hypesquad_balance:
                badges.append("<:hypesquad_balance:1297930998864019509>")
            if member.public_flags.hypesquad_bravery:
                badges.append("<:hypesquad_bravery:1297931035421708358>")
            if member.public_flags.hypesquad_brilliance:
                badges.append("<:hypesquad_brilliance:1297931072503418890>")
            
            # Server Booster Badge
            if member.premium_since:
                badges.append("<:boost:1297931223972450488>")
            
            # Server Owner Badge
            if member == member.guild.owner:
                badges.append("<:server_owner:1297930836368167015>")
            
            # Bot Badge and Slash Commands
            if member.bot:
                badges.append("<a:bot2:1323899876924198976>")

            custom_emojis = " ".join(badges) if badges else "No badges"

            activities = member.activities
            listening = None
            playing = None

            for activity in activities:
                if isinstance(activity, discord.Spotify):
                    track_url = f"https://open.spotify.com/track/{activity.track_id}"
                    listening = f"🎧 [{activity.title} by {activity.artist}]({track_url})"
                elif isinstance(activity, discord.Game):
                    playing = f"🎮 {activity.name}"

            created_at = member.created_at.strftime("%B %d, %Y")
            joined_at = member.joined_at.strftime("%B %d, %Y")
            created_days_ago = (datetime.now(timezone.utc) - member.created_at).days
            joined_days_ago = (datetime.now(timezone.utc) - member.joined_at).days

            created_ago = f"{created_days_ago // 365} year{'s' if (created_days_ago // 365) > 1 else ''} ago" if created_days_ago >= 365 else f"{created_days_ago} day{'s' if created_days_ago > 1 else ''} ago"
            joined_ago = f"{joined_days_ago // 365} year{'s' if (joined_days_ago // 365) > 1 else ''} ago" if joined_days_ago >= 365 else f"{joined_days_ago} day{'s' if joined_days_ago > 1 else ''} ago"

            # Sort roles by position (highest to lowest) and take top 5
            roles = sorted([role for role in member.roles[1:]], key=lambda x: x.position, reverse=True)
            top_roles = roles[:5]
            roles_string = " ".join(role.mention for role in top_roles) if top_roles else "No roles"
            if len(roles) > 5:
                roles_string += f" (+{len(roles) - 5} more)"

            if member.avatar:
                avatar_url = member.avatar.url
            else:
                avatar_url = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url

            if ctx.author.avatar:
                footer_avatar_url = ctx.author.avatar.url
            else:
                footer_avatar_url = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url

            embed = discord.Embed(color=discord.Color.dark_purple(), timestamp=datetime.utcnow())
            embed.set_author(name=f"{member.display_name}{developer_title}", icon_url=avatar_url)
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="User ID", value=f"`{member.id}`", inline=False)
            embed.add_field(name="Badges", value=custom_emojis, inline=False)
            if listening:
                embed.add_field(name="Listening", value=listening, inline=False)
            if playing:
                embed.add_field(name="Playing", value=playing, inline=False)

            embed.add_field(name="Created", value=f"{created_at}\n{created_ago}", inline=True)
            embed.add_field(name="Joined", value=f"{joined_at}\n{joined_ago}", inline=True)

            embed.add_field(name="Roles", value=roles_string, inline=False)

            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=footer_avatar_url)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"**Error**: Something went wrong - (No, nothing went wrong, I just don't like the person you're looking for)")
            raise e

    @commands.command(name="si", help="Show the server info.")
    async def server_info(self, ctx):
        """Shows the server information in a red embed."""
        
        if not ctx.guild.me.guild_permissions.embed_links:
            await ctx.send("I don't have permission to send embeds!")
            return

        guild = ctx.guild
        owner = guild.owner
        verification_level = guild.verification_level
        boosts = guild.premium_subscription_count
        
        total_members = guild.member_count
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots
        admins = sum(1 for member in guild.members 
                    if not member.bot and member.guild_permissions.administrator)

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles = len(guild.roles) - 1

        vanity_url_code = guild.vanity_url_code
        vanity_url = f"/{vanity_url_code}" if vanity_url_code else "None"

        server_description = guild.description or "No description available"
        creation_time = guild.created_at.strftime("%B %d, %Y %I:%M %p")

        now = datetime.now(timezone.utc)
        created_at = guild.created_at
        delta = now - created_at
        years = delta.days // 365
        time_since_creation = f"{years} year{'s' if years != 1 else ''} ago" if years >= 1 else f"{delta.days} day{'s' if delta.days > 1 else ''} ago"

        server_icon_url = guild.icon.url if guild.icon else None

        embed = discord.Embed(
            description=f"{creation_time} ({time_since_creation})",
            color=discord.Color.red()
        )

        if server_icon_url:
            embed.set_thumbnail(url=server_icon_url)

        embed.title = f"{guild.name} \n{server_description}"

        embed.add_field(
            name="**Server**",
            value=(f"> Owner: {owner.mention}\n"
                  f"> Verification: {verification_level}\n"
                  f"> Boosts: {boosts}\n"
                  f"> Vanity: {vanity_url}"),
            inline=True
        )

        embed.add_field(
            name="**Members**",
            value=(f"> Total: {total_members:,}\n"
                  f"> Humans: {humans:,}\n"
                  f"> Bots: {bots:,}\n"
                  f"> Admins: {admins:,}"),
            inline=True
        )

        embed.add_field(
            name="**Structure**",
            value=(f"> Channels: {text_channels:,}\n"
                  f"> Voice: {voice_channels:,}\n"
                  f"> Categories: {categories:,}\n"
                  f"> Roles: {roles:,}"),
            inline=True
        )

        current_time = datetime.now().strftime("%I:%M %p")
        embed.set_footer(text=f"Guild ID: {guild.id} | Today at {current_time}")

        await ctx.send(embed=embed)


    @commands.command(name="mc")
    async def member_count(self, ctx):
        guild = ctx.guild
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        total = guild.member_count

        embed = discord.Embed(
            title=f"Member Count for {guild}",
            description=f"> **Humans**: {humans}\n> **Bots**: {bots}\n> **Total**: {total}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="serverbanner")
    async def server_banner(self, ctx):
        """Shows the server banner in an embed."""
        if ctx.guild.banner:
            embed = discord.Embed(title=f"{ctx.guild.name} Server Banner", color=discord.Color.blurple())
            embed.set_image(url=ctx.guild.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This server does not have a banner set.")

    @commands.command(name="sicon")
    async def server_icon(self, ctx):
        """Shows the server icon in an embed."""
        if ctx.guild.icon:
            embed = discord.Embed(title=f"{ctx.guild.name} Server Icon", color=discord.Color.blurple())
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This server does not have an icon set.")

    @commands.command(name="splash")
    async def server_splash(self, ctx):
        """Shows the server splash (invite banner) in an embed."""
        if ctx.guild.splash:
            embed = discord.Embed(title=f"{ctx.guild.name} Server Splash", color=discord.Color.blurple())
            embed.set_image(url=ctx.guild.splash.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This server does not have a splash image set.")

    @commands.command(name="whereis")
    async def whereis(self, ctx, command_name: str):
        """
        Finds the file path of the cog where a specified command is defined.
        Usage: ,whereis <command>
        """
        command = self.bot.get_command(command_name)
        if not command:
            await ctx.send(f"Command `{command_name}` not found.")
            return

        cog = command.cog
        if cog:
            cog_name = cog.__class__.__name__
            file_path = cog.__module__.replace(".", "/") + ".py"
            await ctx.send(f"Command `{command_name}` is defined in the `{cog_name}` cog located at `{file_path}`.")
        else:
            await ctx.send(f"Command `{command_name}` is not part of a cog or is defined inline.")

    @commands.command()
    async def owners(self, ctx: Context):
        """
        Displays an embed of the owners of heresy.
        """
        embed = Embed(
        title="Owners of heresy",
        description=(
            f"<@785042666475225109> | 785042666475225109\n"
            f"<@1268333988376739931> | 1268333988376739931\n"
            f"<@608450597347262472> | 608450597347262472\n"
            f"<@488590546873483276> | 488590546873483276\n"
            f"<@598125772754124823> | 598125772754124823\n"),
        color=Color.purple())
        await ctx.send(embed=embed)

    @commands.command(name="ri", aliases=["roleinfo"])
    async def role_info(self, ctx, *, role: discord.Role = None):
        """Display detailed information about a role."""
        # If no role is specified, try to get the highest role of the author
        if not role:
            role = ctx.author.top_role

        # Validate role
        if not isinstance(role, discord.Role):
            try:
                # Try to find role by name or mention
                role = discord.utils.get(ctx.guild.roles, name=role) or \
                       discord.utils.get(ctx.guild.roles, mention=role)
                if not role:
                    return await ctx.send("Role not found. Please specify a valid role.")
            except:
                return await ctx.send("Role not found. Please specify a valid role.")

        # Count members with this role
        members_with_role = len([member for member in ctx.guild.members if role in member.roles])

        # Determine role type (admin, mod, staff, or regular)
        role_type = "Regular"
        permissions = role.permissions
        if permissions.administrator:
            role_type = "Administrator"
        elif permissions.manage_guild or permissions.manage_channels or permissions.kick_members or permissions.ban_members:
            role_type = "Staff"
        elif permissions.moderate_members:
            role_type = "Moderator"

        # Create embed with role color
        embed = discord.Embed(
            title=role.name,
            color=role.color
        )

        # Add bot's avatar to the top right
        if ctx.bot.user.avatar:
            embed.set_thumbnail(url=ctx.bot.user.avatar.url)

        # Display Information
        display_info = f"**Color:** {str(role.color)}\n**Hoisted:** {'Yes' if role.hoist else 'No'}"
        embed.add_field(name="Display", value=display_info, inline=True)

        # Base Information
        base_info = f"**Role ID:** {role.id}\n**Highest Permission:** {role_type}"
        embed.add_field(name="Base", value=base_info, inline=True)

        # Other Information
        other_info = (
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}\n"
            f"**Hierarchy Position:** {role.position}/{len(ctx.guild.roles)}\n"
            f"**Created At:** {role.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"**Members:** {members_with_role}"
        )
        embed.add_field(name="Other", value=other_info, inline=True)

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, CommandNotFound):
            misspelled_command = ctx.message.content.split()[0].lstrip(ctx.prefix)
            all_commands = [cmd.name for cmd in self.bot.commands]
            for cmd in self.bot.commands:
                all_commands.extend(cmd.aliases)
            close_matches = difflib.get_close_matches(misspelled_command, all_commands, n=1, cutoff=0.6)

            if close_matches:
                suggestion = close_matches[0]
                suggestion_message = await ctx.reply(
                    f"{ctx.author.mention},`{misspelled_command}` is not a command. Did you mean `{ctx.prefix}{suggestion}`?",
                    mention_author=True
                )
                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel

                try:
                    response = await self.bot.wait_for('message', check=check, timeout=30.0)
                    if response.content.lower() == "yes":
                        await ctx.invoke(self.bot.get_command(suggestion))
                    elif response.content.lower() == "no":
                        await response.reply("Oh ok")

                except asyncio.TimeoutError:
                    await ctx.reply("You did not respond in time. No command was executed.")

            else:
                await ctx.reply(f"{ctx.author.mention}, `{misspelled_command}` is not a command. Use `{ctx.prefix}help` to see all available commands.", mention_author=True)

    @commands.command(name="bi", aliases=['botinfo'], help="Shows detailed information about the bot.")
    async def show_bot_info(self, ctx):
        """Displays detailed information about the bot including stats and system info."""
        bot = self.bot
        
        total_members = sum(guild.member_count for guild in bot.guilds)
        total_guilds = len(bot.guilds)
        total_commands = len(bot.commands)
        total_cogs = len(bot.cogs)

        if platform.system() == "Darwin":
            host = "MacOS " + platform.mac_ver()[0]
        else:
            host = platform.system() + " " + platform.release()

        jishaku = self.bot.get_cog('Jishaku')
        if jishaku:
            uptime = datetime.now(timezone.utc) - jishaku.load_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Unable to calculate"

        total_lines = 0
        total_files = 0
        total_imports = 0
        total_functions = 0
        
        for root, _, files in os.walk("cogs"):
            for file in files:
                if file.endswith('.py'):
                    total_files += 1
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    total_lines += len(content.splitlines())
                    total_imports += len([line for line in content.splitlines() if line.strip().startswith(('import ', 'from '))])
                    total_functions += len([line for line in content.splitlines() if line.strip().startswith(('def ', 'async def '))])

        embed = discord.Embed(
            description=f"Developed and maintained by <@{self.developer_id}>\n`{total_commands}` commands | `{total_cogs}` cogs",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )

        # Basic Stats
        embed.add_field(
            name="**Basic**",
            value=f"**Users**: `{total_members:,}`\n**Servers**: `{total_guilds:,}`\n**Created**: `{bot.user.created_at.strftime('%B %d, %Y')}`",
            inline=True
        )
        
        # Runtime Stats
        embed.add_field(
            name="**Runtime**",
            value=f"**OS**: `{host}`\n**CPU**: `{psutil.cpu_percent()}%`\n**Memory**: `{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB`\n**Uptime**: `{uptime_str}`",
            inline=True
        )
        
        # Code Stats
        embed.add_field(
            name="**Code**",
            value=f"**Files**: `{total_files}`\n**Lines**: `{total_lines:,}`\n**Functions**: `{total_functions}`\n**Library**: `discord.py {discord.__version__}`",
            inline=True
        )

        embed.set_thumbnail(url="https://playfairs.cc/heresy.jpg")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="ms", help="Shows mutual servers with another user")
    async def mutual_servers(self, ctx, user: discord.User = None):
        """Shows servers that you share with the specified user or yourself."""
        target = user or ctx.author
        if target.bot:
            await ctx.send("I cannot check mutual servers with bots.")
            return

        mutual_guilds = [guild for guild in ctx.bot.guilds if guild.get_member(target.id)]
        
        if not mutual_guilds:
            await ctx.send(f"No mutual servers found with {target.name}.")
            return

        embed = discord.Embed(
            title=f"Mutual Servers with {target.name}",
            description=f"Found {len(mutual_guilds)} mutual servers",
            color=discord.Color.blue()
        )

        # Split into chunks of 10 servers per field
        for i in range(0, len(mutual_guilds), 10):
            chunk = mutual_guilds[i:i + 10]
            field_value = "\n".join(f"> **{guild.name}** (`{guild.id}`)" for guild in chunk)
            embed.add_field(
                name=f"Servers {i+1}-{i+len(chunk)}", 
                value=field_value, 
                inline=False
            )

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="nms", help="Shows non-mutual servers")
    async def non_mutual_servers(self, ctx, user: discord.User = None):
        """Shows servers that you don't share with the specified user or yourself."""
        target = user or ctx.author
        if target.bot:
            await ctx.send("I cannot check non-mutual servers with bots.")
            return

        all_guilds = ctx.bot.guilds
        mutual_guilds = [guild for guild in all_guilds if guild.get_member(target.id)]
        non_mutual_guilds = [guild for guild in all_guilds if guild not in mutual_guilds]

        if not non_mutual_guilds:
            await ctx.send(f"No non-mutual servers found (you're in all the same servers as {target.name}).")
            return

        embed = discord.Embed(
            title=f"Non-Mutual Servers with {target.name}",
            description=f"Found {len(non_mutual_guilds)} non-mutual servers",
            color=discord.Color.red()
        )

        # Split into chunks of 10 servers per field
        for i in range(0, len(non_mutual_guilds), 10):
            chunk = non_mutual_guilds[i:i + 10]
            field_value = "\n".join(f"> **{guild.name}** (`{guild.id}`)" for guild in chunk)
            embed.add_field(
                name=f"Servers {i+1}-{i+len(chunk)}", 
                value=field_value, 
                inline=False
            )

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="sbanner", description="Show your server banner.")
    async def sbanner(self, ctx, member: discord.Member = None):
        """Displays the server banner of the specified user or yourself if no one is mentioned."""
        member = member or ctx.author

        if member.guild_banner:
            embed = discord.Embed(title=f"{member.name}'s Server Banner", color=discord.Color.blue())
            embed.set_image(url=member.guild_banner.url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{member.mention} does not have a server banner.")

    @commands.command(name="lines")
    async def count_lines(self, ctx, *, cog_path: str):
        """Count lines in a cog file. Usage: ,lines cogs.lastfm"""
        try:
            # Get the bot's root directory and construct absolute path
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            file_path = os.path.join(root_dir, cog_path.replace('.', os.sep) + '.py')
            
            if not os.path.exists(file_path):
                await ctx.send(f"```py\nFileNotFoundError: Could not find cog file '{file_path}'```")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            total_lines = len(content.splitlines())
            blank_lines = len([line for line in content.splitlines() if not line.strip()])
            code_lines = total_lines - blank_lines
            
            # Count specific types of lines
            imports = len([line for line in content.splitlines() if line.strip().startswith(('import ', 'from '))])
            functions = len([line for line in content.splitlines() if line.strip().startswith(('def ', 'async def '))])
            classes = len([line for line in content.splitlines() if line.strip().startswith('class ')])
            comments = len([line for line in content.splitlines() if line.strip().startswith('#')])

            embed = discord.Embed(
                title=f"📊 Line Count for {cog_path}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Lines",
                value=f"```\nTotal: {total_lines:,}\nCode: {code_lines:,}\nBlank: {blank_lines:,}```",
                inline=True
            )
            
            embed.add_field(
                name="Components",
                value=f"```\nImports: {imports}\nFunctions: {functions}\nClasses: {classes}\nComments: {comments}```",
                inline=True
            )

            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"```py\n{type(e).__name__}: {str(e)}```")

    @commands.command(name="permissions", description="Shows current permissions for users or a role.")
    async def permissions(self, ctx, *, target: Union[discord.Member, discord.Role] = None):
        """Shows current permissions for users or a role."""
        try:
            target = target or ctx.author

            if isinstance(target, discord.Member):
                permissions = target.permissions
            elif isinstance(target, discord.Role):
                permissions = target.permissions
            else:
                return await ctx.send("Invalid target. Please specify a member or role.")

            embed = discord.Embed(
                title=f"🔧 Permissions for {target.name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Permissions",
                value=f"```\n{permissions}```",
                inline=False
            )
            
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"```py\n{type(e).__name__}: {str(e)}```")

    @commands.command(name="bots", description="Shows the number of bots in the server.")
    async def bots(self, ctx):
        """Shows the number of bots in the server."""
        bot_count = sum(1 for member in ctx.guild.members if member.bot)
        await ctx.send(embed=discord.Embed(
            title=f"Bots in {ctx.guild.name}",
            description=f"{bot_count} bots",
            color=discord.Color.blue()
        ))