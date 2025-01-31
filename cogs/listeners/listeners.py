import discord
from discord.ext.commands import Cog
from main import Heresy
import os

class Listeners(Cog):
    def __init__(self, bot: Heresy):
        self.bot = bot
        self.blacklisted_guilds = set()
        self.last_message_author = None
        self.consecutive_messages = 0
        self.owner_id = 785042666475225109  # Hardcoded owner ID from the existing code
        self.bot_id = 1284037026672279635  # Bot's user ID

    @Cog.listener('on_guild_join')
    async def join_logger(self, guild):
        """
        Event triggered when the bot joins a new server (guild).
        """
        inviter = None
        try:
            audit_logs = await guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add).flatten()
            if audit_logs:
                inviter = audit_logs[0].user
        except Exception as e:
            print(f"Could not retrieve inviter for {guild.name}: {e}")

        if inviter:
            embed = discord.Embed(
                title="Thanks for Choosing Heresy!",
                description=(
                    "Hello! Thank you for inviting Heresy to your server.\n"
                    "To see all available commands, use `,help`.\n\n"
                    "If you have any questions, join discord.gg/Heresy for more info on Heresy."
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text="I am in your walls.")
            try:
                await inviter.send(embed=embed)
            except Exception as e:
                print(f"Could not DM inviter {inviter}: {e}")

        invite_link = "Unable to generate invite"
        try:
            invite = await guild.text_channels[0].create_invite(max_age=3600, max_uses=1, unique=True)
            invite_link = invite.url
        except Exception as e:
            print(f"Could not create invite for {guild.name}: {e}")

        owner_dm_content = (
            f"Hello <@785042666475225109>, I was added to **{guild.name}** by "
            f"{inviter.mention if inviter else 'an unauthorized user'}.\n\n"
            f"If you did not authorize this action, feel free to revoke access. Invite link: {invite_link}"
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
        # Check if the bot is mentioned
        if message.author.bot:
            return

        # Check if the message mentions the bot
        bot_mention = f'<@{self.bot_id}>'
        if not message.content.startswith(bot_mention):
            return

        # Split the message content
        parts = message.content.split()

        # Special case for "where is your mom"
        if (len(parts) >= 4 and 
            parts[0] == bot_mention and 
            parts[1].lower() == 'where' and 
            parts[2].lower() == 'is' and 
            ' '.join(parts[3:]).lower() == 'your mom'):
            await message.channel.send("<@926665802957066291> where are you?")
            return

        # Check for the specific query format
        if (len(parts) < 4 or 
            parts[0] != bot_mention or 
            parts[1].lower() != 'where' or 
            parts[2].lower() != 'is'):
            return

        # Get the command name
        command_name = parts[3]

        # Search through all cogs for the command
        for cog_name, cog in self.bot.cogs.items():
            for cmd in cog.get_commands():
                if cmd.name == command_name or command_name in cmd.aliases:
                    # Find the file and get its absolute path
                    file_path = os.path.abspath(os.path.join('cogs', type(cog).__module__.replace('.', '/') + '.py'))
                    
                    # Try to find the exact line numbers
                    try:
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if f"def {cmd.name}" in line:
                                    start_line = i + 1
                                    break
                            else:
                                start_line = "unknown"
                    except Exception:
                        start_line = "unknown"

                    # Construct the response
                    response = (
                        f"Command `{command_name}` is located in:\n"
                        f"Folder: `cogs`\n"
                        f"File: `{os.path.basename(file_path)}`\n"
                        f"Start Line: `{start_line}`"
                    )
                    
                    await message.channel.send(response)
                    return

        # If command not found
        await message.channel.send(f"Could not find a command named `{command_name}`.")

    @Cog.listener('on_message')
    async def greet(self, message):
        if message.author == self.bot.user:
            return

        if message.content.lower() == "hi heresy":
            await message.channel.send(f"Hi, {message.author.mention}")
