import asyncpg
import logging

from pathlib import Path
from discord.ext import commands
from discord import Intents, AllowedMentions
from core.client.help import HerseyHelp

from config import DISCORD

log = logging.getLogger(__name__)

class Heresy(commands.AutoShardedBot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, 
            **kwargs,
            command_prefix=DISCORD.PREFIX,
            help_command=HerseyHelp(),
            shard_count=5,
            intents=Intents(
                guilds=True,
                members=True,
                messages=True,
                reactions=True,
                presences=True,
                moderation=True,
                message_content=True,
                emojis_and_stickers=True,
            ),
            allowed_mentions=AllowedMentions(
                everyone=False,
                users=True,
                roles=False,
                replied_user=True
            ),
        )
        self.owner_ids = DISCORD.OWNER_IDS
    
    def run(self) -> None:
        log.info("Starting the bot...")

        super().run(
            DISCORD.TOKEN,
            reconnect=True,
            log_handler=None,
        )

    async def load_extensions(self) -> None:
        await self.load_extension("jishaku")
        for feature in Path("cogs").iterdir():
            if feature.is_dir() and (feature / "__init__.py").is_file():
                try:
                    cog_name = ".".join(feature.parts)
                    print(f"Attempting to load extension: {cog_name}")
                    await self.load_extension(cog_name)
                    print(f"Successfully loaded: {cog_name}")
                except Exception as exc:
                    log.exception(
                        f"Failed to load extension {feature.name}.", exc_info=exc
                    )

    async def create_db_pool(self):
        self.db = await asyncpg.create_pool(
            port="5432",
            database="hersey",
            user="playfair",
            host="localhost",
            password="8462PlayfairDisplay.cc"
        )

    async def setup_hook(self):
        await self.create_db_pool()
        await self.load_extensions()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Shard ID: {self.shard_id} of {self.shard_count} shards')
        print("Heresy v2.1.0")
        
        await self.tree.sync()
        print("Synced global commands successfully.")
        print("Bot is ready and connected.")

    async def get_context(self, message, *, cls=commands.Context):
        # Convert the entire message content to lowercase
        message.content = message.content.lower()
        
        # Call the original get_context method
        return await super().get_context(message, cls=cls)

    async def get_prefix(self, message):
        # Convert the message content to lowercase for case-insensitive prefix matching
        prefixes = [',']
        return commands.when_mentioned_or(*prefixes)(self, message)

    async def process_commands(self, message):
        # Convert the command to lowercase to make it case-insensitive
        ctx = await self.get_context(message)
        
        if ctx.command is not None:
            # Convert the invoked command to lowercase
            ctx.invoked_with = ctx.invoked_with.lower()
            
            # Special handling for help command
            if ctx.command.name == 'help' or 'help' in ctx.command.aliases:
                # If the command is help, convert the first argument to lowercase
                if len(ctx.args) > 2:
                    ctx.args = list(ctx.args)
                    ctx.args[2] = ctx.args[2].lower()
            
            # Convert command arguments to lowercase if they are strings
            if ctx.args and len(ctx.args) > 2:
                ctx.args = list(ctx.args)
                for i in range(2, len(ctx.args)):
                    if isinstance(ctx.args[i], str):
                        ctx.args[i] = ctx.args[i].lower()
        
        await self.invoke(ctx)

    async def invoke(self, ctx):
        # Convert the command name to lowercase for case-insensitive matching
        if ctx.command is not None:
            # Modify the command's name to be case-insensitive
            ctx.command.name = ctx.command.name.lower()
            
            # Also modify any aliases to lowercase
            if hasattr(ctx.command, 'aliases'):
                ctx.command.aliases = [alias.lower() for alias in ctx.command.aliases]
        
        # Call the original invoke method
        await super().invoke(ctx)

if __name__ == "__main__":
    bot = Heresy()
    bot.run()
