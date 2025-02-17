import os
import sqlite3
import time
import discord
import json
import pytz
import datetime
import yt_dlp
import aiohttp
import io
import re
import asyncio

from cogs.utility.timezone import TIMEZONE_ABBR
from discord.ext import commands
from discord.ext.commands import Cog, command, Context
from deep_translator import GoogleTranslator
from main import heresy

if not os.path.exists('db'):
    os.makedirs('db')

DB_FILE = 'db/timezones.json'

def load_timezones():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_timezones(timezones):
    with open(DB_FILE, 'w') as f:
        json.dump(timezones, f, indent=4)

class Utility(Cog):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.default_language = "en"
        self.db_path = os.path.join("db", "afk_users.db")
        self.initialize_db()
        print("[AFK] Initialized AFK cog and database connection.")

    def initialize_db(self):
        """Initialize the database folder and file to store AFK users."""
        try:
            if not os.path.exists("db"):
                os.makedirs("db")
                print("[AFK] Created 'db' directory for database files.")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS afk_users (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                afk_time INTEGER
            )''')
            conn.commit()
            conn.close()
            print("[AFK] Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"[AFK] Error initializing database: {e}")

    def set_afk(self, user_id, reason):
        """Sets the AFK status for a user with the current timestamp."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO afk_users (user_id, reason, afk_time)
            VALUES (?, ?, ?)''', (user_id, reason, int(time.time())))
            conn.commit()
            conn.close()
            print(f"[AFK] AFK set for user {user_id} with reason: {reason}")
        except sqlite3.Error as e:
            print(f"[AFK] Error setting AFK: {e}")

    def get_afk_status(self, user_id):
        """Gets the AFK status and timestamp for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT reason, afk_time FROM afk_users WHERE user_id = ?''', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except sqlite3.Error as e:
            print(f"[AFK] Error getting AFK status: {e}")
            return None

    def remove_afk(self, user_id):
        """Removes the AFK status for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM afk_users WHERE user_id = ?''', (user_id,))
            conn.commit()
            conn.close()
            print(f"[AFK] AFK removed for user {user_id}.")
        except sqlite3.Error as e:
            print(f"[AFK] Error removing AFK: {e}")

    def format_time_ago(self, afk_time):
        """Formats the time since the AFK status was set."""
        time_elapsed = int(time.time()) - afk_time
        if time_elapsed < 60:
            return "a few seconds ago"
        elif time_elapsed < 3600:
            minutes = time_elapsed // 60
            return f"{minutes} minutes ago"
        elif time_elapsed < 86400:
            hours = time_elapsed // 3600
            return f"{hours} hours ago"
        else:
            days = time_elapsed // 86400
            return f"{days} days ago"

    def validate_and_normalize_url(self, url: str) -> str:
        """Validate and normalize URLs for downloading"""
        import re

        # YouTube URL patterns
        youtube_patterns = [
            r'https?://(www\.)?(youtube\.com|youtu\.be)/.+',
            r'https?://(?:www\.)?youtube\.com/watch\?v=.+',
            r'https?://(?:www\.)?youtube\.com/embed/.+',
            r'https?://(?:www\.)?youtube\.com/shorts/.+'
        ]

        # TikTok URL patterns
        tiktok_patterns = [
            r'https?://(www\.)?tiktok\.com/.*',
            r'https?://vm\.tiktok\.com/.+',
            r'https?://vt\.tiktok\.com/.+',
            r'https?://(www\.)?tiktok\.com/t/.+'
        ]

        # Check if URL matches any YouTube or TikTok pattern
        if any(re.match(pattern, url, re.IGNORECASE) for pattern in youtube_patterns + tiktok_patterns):
            return url

        raise ValueError("Unsupported or invalid URL")

    @command(name='afk', aliases= ["kms", "despawn", "idle", "akf"])
    async def afk(self, ctx: Context, *, reason: str = "AFK"):
        """Set the AFK status with an optional reason."""
        user_id = ctx.author.id
        
        # Set specific status for kms alias
        if ctx.invoked_with == "kms":
            reason = "probably killing themselves"

        if ctx.invoked_with == "idle":
            reason = "idling? The fuck is this, roblox?"

        if ctx.invoked_with == "despawn":
            reason = "Why is despawn even an alias???"
        
        if ctx.invoked_with == "akf":
            reason = "close enough"
            
        self.set_afk(user_id, reason)

        embed = discord.Embed(
            description=f"<:check:1301903971535028314> {ctx.author.mention}, you're now AFK with status: **{reason}**",
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed, mention_author=True)

    @command(name="default-lang")
    async def set_default_language(self, ctx, language: str):
        """
        Sets the default language for the bot to use when translating.
        
        Usage:
        ,default-lang <language_code>
        
        Example:
        ,default-lang es
        """
        supported_languages = GoogleTranslator.get_supported_languages(as_dict=True)

        if language.lower() not in supported_languages.values():
            available_languages = ", ".join(supported_languages.values())
            embed = discord.Embed(
                title="Invalid Language",
                description=f"Please provide a valid language.\nAvailable languages:\n`{available_languages}`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return

        self.default_language = language.lower()
        embed = discord.Embed(
            title="Google Translate",
            description=f"The default language has been set to **{language}**.",
            color=discord.Color.blue()
        )
        await ctx.reply(embed=embed, mention_author=True)

    @command(name="translate")
    async def translate(self, ctx, *, text: str = None):
        """
        Translates the given text or a replied-to message into the default language.

        Usage:
        ,translate <text>
        OR
        Reply to a message with ,translate
        """
        if not text and ctx.message.reference:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            text = replied_message.content

        if not text:
            embed = discord.Embed(
                title="Missing Text",
                description="You must provide text to translate or reply to a message.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)
            return

        try:
            translated_text = GoogleTranslator(source="auto", target=self.default_language).translate(text)
            embed = discord.Embed(
                title="Google Translate",
                description=f"**Translated Text:** {translated_text}",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Translated to {self.default_language.upper()}")
            await ctx.reply(embed=embed, mention_author=True)
        except Exception as e:
            embed = discord.Embed(
                title="Translation Error",
                description=f"An error occurred while translating:\n```{e}```",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=True)

    @command(name="timezone", aliases=['tz'])
    async def timezone(self, ctx, timezone: str = None):
        """Set your timezone. Use a valid timezone abbreviation (e.g., 'CST', 'GMT')."""
        if timezone is None:
            await ctx.send("Please specify a timezone abbreviation. For example: `,timezone CST`")
            return

        timezone = timezone.upper()
        if timezone in TIMEZONE_ABBR:
            timezone = TIMEZONE_ABBR[timezone]
        else:
            await ctx.send(f"{timezone} is not a valid time zone abbreviation. Please try again.")
            return

        try:
            tz = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            await ctx.send(f"{timezone} is not a valid timezone. Please try again.")
            return

        timezones = load_timezones()

        timezones[str(ctx.author.id)] = timezone
        save_timezones(timezones)

        await ctx.send(f"Your timezone has been set to {timezone} ({TIMEZONE_ABBR[timezone] if timezone in TIMEZONE_ABBR else timezone}).")

    @command(name="mp3")
    async def download_mp3(self, ctx, url: str):
        """Download audio from a YouTube or TikTok video"""
        try:
            # Validate and normalize URL
            try:
                normalized_url = self.validate_and_normalize_url(url)
            except ValueError:
                return await ctx.send("Please provide a valid YouTube or TikTok URL.")

            # Send initial processing message
            processing_msg = await ctx.send("🔄 Processing your request...")

            # Temporary directory for downloads
            import tempfile
            import os

            # Configure yt-dlp for audio extraction
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
                'nooverwrites': True,
                'no_color': True,
                'quiet': True
            }

            # Download the audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(normalized_url, download=True)
                audio_file = ydl.prepare_filename(info_dict)
                audio_file = audio_file.rsplit(".", 1)[0] + ".mp3"

            # Check file size
            file_size = os.path.getsize(audio_file)
            if file_size > 8 * 1024 * 1024:  # 8MB limit
                os.remove(audio_file)
                return await processing_msg.edit(content="❌ File is too large to upload.")

            # Send the audio file
            try:
                await processing_msg.delete()
                await ctx.send(file=discord.File(audio_file, filename=os.path.basename(audio_file)))
            finally:
                # Clean up the temporary file
                os.remove(audio_file)

        except Exception as e:
            print(f"MP3 Download Error: {e}")
            await processing_msg.edit(content=f"❌ An error occurred: {str(e)}")

    @command(name="mp4")
    async def download_mp4(self, ctx, url: str):
        """Download video from a YouTube or TikTok video"""
        try:
            # Validate and normalize URL
            try:
                normalized_url = self.validate_and_normalize_url(url)
            except ValueError:
                return await ctx.send("Please provide a valid YouTube or TikTok URL.")

            # Send initial processing message
            processing_msg = await ctx.send("Processing your request...")

            # Temporary directory for downloads
            import tempfile
            import os

            # Configure yt-dlp for video download
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
                'nooverwrites': True,
                'no_color': True,
                'quiet': True
            }

            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(normalized_url, download=True)
                video_file = ydl.prepare_filename(info_dict)

            # Check file size
            file_size = os.path.getsize(video_file)
            if file_size > 8 * 1024 * 1024:  # 8MB limit
                os.remove(video_file)
                return await processing_msg.edit(content="❌ File is too large to upload.")

            # Send the video file
            try:
                await processing_msg.delete()
                await ctx.send(file=discord.File(video_file, filename=os.path.basename(video_file)))
            finally:
                # Clean up the temporary file
                os.remove(video_file)

        except Exception as e:
            print(f"MP4 Download Error: {e}")
            await processing_msg.edit(content=f"❌ An error occurred: {str(e)}")

    @command(name="time")
    async def time(self, ctx, user: discord.User = None):
        """Get the current time for the user (or yourself if no user is mentioned)."""
        if user is None:
            user = ctx.author

        timezones = load_timezones()

        if str(user.id) not in timezones:
            await ctx.send(f"{user.mention} has not set a timezone. Use `,timezone` to set one.")
            return

        timezone = timezones[str(user.id)]

        tz = pytz.timezone(timezone)
        current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(
            title=f"Current time for {user.display_name}",
            description=f"The current time in {timezone} is: {current_time}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @command(name='fetch')
    async def fetch_sticker(self, ctx):
        """Fetches the sticker from a reply and sends it as a downloadable file."""
        if ctx.message.reference is None:
            await ctx.send("Please reply to a sticker to fetch it.")
            return

        message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        sticker = message.stickers[0] if message.stickers else None

        if sticker:
            # Download the sticker
            async with aiohttp.ClientSession() as session:
                async with session.get(sticker.url) as resp:
                    if resp.status != 200:
                        await ctx.send("Failed to download the sticker.")
                        return
                    sticker_bytes = await resp.read()

            # Validate sticker size (Discord limit is 256 KB)
            if len(sticker_bytes) > 256 * 1024:
                await ctx.send("Sticker is too large to fetch (max 256 KB).")
                return

            # Determine the file format based on whether the sticker is animated
            file_format = 'gif' if sticker.url.endswith('.gif') else 'png'

            # Send the sticker as a downloadable file
            await ctx.send(file=discord.File(io.BytesIO(sticker_bytes), filename=f"sticker.{file_format}"))
        else:
            await ctx.send("No sticker found in the replied message.")

    @command(name='steal')
    @commands.has_permissions(manage_emojis=True)
    async def steal(self, ctx):
        """
        Steal a sticker from a replied message and add it to the server.
        Requires Manage Emojis permission.
        """
        # Check if the command is a reply
        if not ctx.message.reference:
            await ctx.send("Please reply to a message with a sticker you want to steal.")
            return

        try:
            # Fetch the referenced message
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Check if the message has any stickers
            if not referenced_message.stickers:
                await ctx.send("The replied message does not have any stickers.")
                return

            # Get the first sticker
            sticker = referenced_message.stickers[0]

            # Download the sticker
            async with aiohttp.ClientSession() as session:
                async with session.get(sticker.url) as resp:
                    if resp.status != 200:
                        await ctx.send("Failed to download the sticker.")
                        return
                    sticker_bytes = await resp.read()

            # Validate sticker size (Discord limit is 256 KB)
            if len(sticker_bytes) > 256 * 1024:
                await ctx.send("Sticker is too large to steal (max 256 KB).")
                return

            # Add the sticker to the server
            try:
                new_sticker = await ctx.guild.create_sticker(
                    name=sticker.name.lower().replace(' ', '_'), 
                    description=f"Stolen sticker from {referenced_message.author.name}", 
                    emoji="😀",  # Default emoji, can be changed later
                    file=discord.File(io.BytesIO(sticker_bytes), filename=f"{sticker.name.lower().replace(' ', '_')}.png")
                )
                await ctx.send(f"Sticker `{sticker.name}` successfully stolen and added to the server!")
            except discord.HTTPException as e:
                await ctx.send(f"Failed to add sticker: {e}")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            print(f"Sticker steal error: {e}")

    @command(name='force_remove_afk')
    async def force_remove_afk(self, ctx, member: discord.Member):
        """Forcefully removes AFK status from a mentioned user if they are AFK."""
        if ctx.author.id != 785042666475225109:
            await ctx.send("You do not have permission to use this command.")
            return

        afk_data = self.get_afk_status(member.id)
        if afk_data:
            self.remove_afk(member.id)  # Logic to remove AFK status
            await ctx.send(f"{member.mention} is no longer AFK.")
        else:
            await ctx.send(f"{member.mention} is not AFK.")

    @Cog.listener('on_message')
    async def afk_listener1(self, message):
        if message.author.bot or message.webhook_id is not None:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            print(f"[AFK Debug] Ignoring AFK removal for command: {message.content}")
            return

        afk_data = self.get_afk_status(message.author.id)
        
        if afk_data:
            print(f"[AFK Debug] Removing AFK for user: {message.author.id} due to manual message.")
            self.remove_afk(message.author.id)

            embed = discord.Embed(
                description=f"👋 Welcome back, {message.author.mention}! You went AFK {self.format_time_ago(afk_data[1])}.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)

        for mentioned_user in message.mentions:
            afk_data = self.get_afk_status(mentioned_user.id)
            if afk_data:
                reason, afk_time = afk_data
                embed = discord.Embed(
                    description=f"{mentioned_user.mention} went AFK {self.format_time_ago(afk_time)}: **{reason}**",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)

    @Cog.listener('on_message_edit')
    async def afk_listener2(self, before, after):
        afk_data = self.get_afk_status(before.author.id)
        if afk_data:
            embed = discord.Embed(
                description=f"{before.author.mention} is currently AFK: **{afk_data[0]}**.",
                color=discord.Color.red()
            )
            await after.channel.send(embed=embed)

    @Cog.listener('on_message_delete')
    async def afk_listener3(self, message):
        if message.author.bot:
            return
        
        afk_data = self.get_afk_status(message.author.id)
        if afk_data:
            embed = discord.Embed(
                description=f"{message.author.mention} is AFK: **{afk_data[0]}**.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
        
        # Check if the bot is AFK
        if message.author.id == self.bot.user.id:
            # Remove AFK status
            self.remove_afk(self.bot.user.id)  # Remove AFK status for the bot
            await message.channel.send(f"{self.bot.user.mention} was AFK, removing AFK as this shouldn't be possible.")
