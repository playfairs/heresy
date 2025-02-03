import asyncpg
import logging
import config

from pathlib import Path
from discord.ext import commands
from discord import Intents, AllowedMentions
from core.client.help import HerseyHelp

log = logging.getLogger(__name__)

class Vanity(commands.AutoShardedBot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, 
            **kwargs,
        command_prefix=config.VANITY.PREFIX,
        help_command=HerseyHelp(),
        intents=Intents(
            guilds=True,
            members=True,
            messages=True,
            reactions=True,
            presences=True,
            moderation=True,
            message_content=True,
            emojis_and_stickers=True,
            auto_moderation=True,
        ),
        allowed_mentions=AllowedMentions(
            everyone=False,
            users=True,
            roles=False,
            replied_user=False
        ),
    )
        self.owner_ids = config.VANITY.OWNER_IDS
    
    def run(self) -> None:
        log.info("Starting the bot...")

        super().run(
            config.VANITY.VANITY_TOKEN,
            reconnect=True,
            log_handler=None,
        )

    async def load_extensions(self) -> None:
        await self.load_extension("jishaku")
        for path in Path("cogs/vanity").rglob("*.py"):
            if path.stem == "__init__":
                continue
            try:
                extension = ".".join(path.with_suffix("").parts)
                await self.load_extension(extension)
            except Exception as exc:
                log.exception(
                    f"Failed to load extension {path.stem}", exc_info=exc
                )

    async def create_db_pool(self):
        self.db = await asyncpg.create_pool(port="5432", database="hersey", user="postgres", host="localhost", password="admin")

    async def setup_hook(self):
        self.loop.create_task(self.create_db_pool())

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print ("flesh Vanity 1.0.0")
        await self.load_extensions()
        print("Bot is ready and connected.")

if __name__ == "__main__":
    bot = Vanity()
    bot.run()