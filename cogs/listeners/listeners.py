import discord
from discord.ext import commands
from discord.ext.commands import Cog
from main import heresy
import os

class Listeners(Cog):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.blacklisted_guilds = set()
        self.last_message_author = None
        self.consecutive_messages = 0
        self.owner_id = 785042666475225109
        self.bot_id = 1284037026672279635
#        self.users_listen = {
#            "playfairs": 785042666475225109,
#            "playfair": 785042666475225109
#        }


    @Cog.listener('on_guild_join')
    async def join_logger(self, guild):
        """
        Event triggered when the bot joins a new server (guild).
        """
        inviter = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                inviter = entry.user
                break
        except Exception as e:
            print(f"Could not retrieve inviter for {guild.name}: {e}")

        if inviter:
            embed = discord.Embed(
                title="Thanks for inviting Heresy!",
                description=(
                    "Hello! Thank you for inviting Heresy to your server.\n"
                    "To see all available commands, use `,h`.\n\n"
                    "If you have any questions, join the [Support Server](https://discord.com/invite/heresy) for more info on Heresy."
                ),
                color=discord.Color(0xFFFFFF)
            )
            embed.set_thumbnail(url="https://playfairs.cc/heresy.png")
        embed.add_field(
            name="Resources",
            value="**[invite](https://discordapp.com/oauth2/authorize?client_id=1284037026672279635&scope=bot+applications.commands&permissions=8)**  • "
            "**[server](https://discord.gg/heresy)**  • "
            "**[website](https://playfairs.cc/heresy)**  ",
            inline=False,
        )
        embed.set_footer(text="I'm in your fucking walls.")
        try:
            await inviter.send(embed=embed)
        except Exception as e:
            print(f"Could not DM inviter {inviter}: {e}")

        invite_link = "Unable to generate invite"
        try:
            invite = await guild.text_channels[0].create_invite(max_age=604800, max_uses=1, unique=True)
            invite_link = invite.url
        except Exception as e:
            print(f"Could not create invite for {guild.name}: {e}")

        owner_dm_content = (
            f"Hello <@785042666475225109>, I was added to `{guild.name}` by "
            f"{inviter.mention if inviter else 'an unauthorized user'}.\n\n"
            f"If you did not authorize this action, feel free to revoke access.\n\n"
            f"**Invite link**: {invite_link}"
        )
        try:
            owner_user = await self.bot.fetch_user(self.owner_id)
            await owner_user.send(owner_dm_content)
        except Exception as e:
            print(f"Could not DM owner: {e}")

    @Cog.listener('on_guild_join')
    async def blacklist_check(self, guild):
        """
        Listener to check if the bot joins a blacklisted server.
        If the server is blacklisted, the bot will leave immediately.
        """
        if guild.id in self.blacklisted_guilds:
            await guild.leave()
            print(f"Left blacklisted guild: {guild.name} ({guild.id})")

    @Cog.listener('on_message')
    async def command_location(self, message):
        """
        Listener to find the location of a command when bot is mentioned.
        """
        if message.author.bot:
            return

        bot_mention = f'<@{self.bot_id}>'
        if not message.content.startswith(bot_mention):
            return

        parts = message.content.split()

        if (len(parts) >= 4 and 
            parts[0] == bot_mention and 
            parts[1].lower() == 'where' and 
            parts[2].lower() == 'is' and 
            ' '.join(parts[3:]).lower() == 'your mom'):
            await message.channel.send("<@926665802957066291> where are you?")
            return

        if (len(parts) < 4 or 
            parts[0] != bot_mention or 
            parts[1].lower() != 'where' or 
            parts[2].lower() != 'is'):
            return

        command_name = ' '.join(parts[3:])

        command_name = parts[3]

        for cog_name, cog in self.bot.cogs.items():
            for cmd in cog.get_commands():
                if cmd.name == command_name or command_name in cmd.aliases:
                    file_path = os.path.abspath(os.path.join('cogs', type(cog).__module__.replace('.', '/') + '.py'))
                    
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if f"async def {cmd.name}" in line:
                                    start_line = i + 1
                                    break
                            else:
                                start_line = "unknown"
                    except Exception:
                        start_line = "unknown"

                    response = (
                        f"Command `{command_name}` is located in:\n"
                        f"Folder: `cogs`\n"
                        f"File: `{os.path.basename(file_path)}`\n"
                        f"Start Line: `{start_line}`"
                    )
                    
                    await message.channel.send(response)
                    return

        await message.channel.send("I don't know where that command is located, or it doesn't exist.")

    @Cog.listener('on_message')
    async def greet(self, message):
        if message.author == self.bot.user:
            return
        if message.author == self.bot.user:
            return

        if message.content.lower() == "hi heresy" or message.content.lower() == "hi <@1284037026672279635>" or message.content.lower() == "hello heresy" or message.content.lower() == "hello <@1284037026672279635>":
            await message.channel.send(f"Hi, {message.author.mention}")

#    @Cog.listener()
#    async def on_message(self, message: discord.Message):
#        if message.author.bot:
#            return

#        mentioned_user = None

#        for name, user_id in self.users_listen.items():
#            if name in message.content.lower():
#                mentioned_user = await self.bot.fetch_user(user_id)
#                break

#        if mentioned_user:
#            await message.channel.send(f'{mentioned_user.mention}, {message.author.mention} mentioned your name.')