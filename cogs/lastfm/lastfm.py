import os
import sys
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Button
import aiohttp
import pylast
from typing import Optional, List
from urllib.parse import quote_plus
import asyncpg
from datetime import datetime
import asyncio
import re
import requests
from .tracking_users import TRACKING_USERS
import time

class ArtistPaginator(View):
    def __init__(self, author_id: int, artists: List[dict], username: str, period: str):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.artists = artists
        self.page = 1
        self.max_page = (len(artists) + 9) // 10
        self.username = username
        self.period = period

        self.prev_page.disabled = True
        self.next_page.disabled = self.max_page <= 1
        

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can't use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.page = max(1, self.page - 1)

        self.prev_page.disabled = self.page <= 1
        self.next_page.disabled = False

        await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.page = min(self.max_page, self.page + 1)
        
        self.prev_page.disabled = False
        self.next_page.disabled = self.page >= self.max_page

        await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    def get_page_content(self) -> discord.Embed:
        start_idx = (self.page - 1) * 10
        page_artists = self.artists[start_idx:start_idx + 10]
        
        description = []
        for idx, artist in enumerate(page_artists, start_idx + 1):
            name = artist["name"]
            plays = artist["playcount"]
            url = artist["url"]
            description.append(f"{idx}. [{name}]({url}) - {plays} plays")
        
        embed = discord.Embed(
            description="\n".join(description),
            color=discord.Color.red()
        )
        
        period_display = {
            "at": "All Time",
            "7d": "Weekly",
            "1m": "Monthly",
            "3m": "3 Months",
            "6m": "6 Months",
            "12m": "Yearly"
        }
        
        embed.set_author(name=f"{self.username}'s Top Artists ({period_display[self.period]})")
        embed.set_footer(text=f"Page {self.page}/{self.max_page} - {len(self.artists)} different artists in this time period")
        
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

class WhoKnowsPaginator(View):
    def __init__(self, author_id: int, listeners: List[dict], artist: str, guild_name: str, artist_info: dict):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.listeners = listeners
        self.artist = artist
        self.guild_name = guild_name
        self.artist_info = artist_info
        self.page = 1
        self.max_page = (len(listeners) + 9) // 10

        self.prev_page.disabled = True
        self.next_page.disabled = self.max_page <= 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can't use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.page = max(1, self.page - 1)
        
        self.prev_page.disabled = self.page <= 1
        self.next_page.disabled = False

        await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.page = min(self.max_page, self.page + 1)
        
        self.prev_page.disabled = False
        self.next_page.disabled = self.page >= self.max_page

        await interaction.response.edit_message(embed=self.get_page_content(), view=self)

    def get_page_content(self) -> discord.Embed:
        start_idx = (self.page - 1) * 10
        page_listeners = self.listeners[start_idx:start_idx + 10]
        
        description = []
        for idx, listener in enumerate(page_listeners, start_idx + 1):
            crown = "👑 " if idx == 1 else f"{idx}. "
            username = listener["username"]
            plays = listener["plays"]
            member_name = listener["member"].name
            profile_url = f"https://www.last.fm/user/{username}"
            description.append(f"{crown}[{member_name}]({profile_url}) - {plays} plays")

        embed = discord.Embed(
            description="\n".join(description),
            color=discord.Color.red()
        )
        
        embed.set_author(name=f"{self.artist} in {self.guild_name}")
        
        if "image" in self.artist_info:
            artist_image = self.artist_info["image"][-1]["#text"]
            if artist_image:
                embed.set_thumbnail(url=artist_image)

        global_listeners = self.artist_info["stats"]["listeners"]
        global_plays = self.artist_info["stats"]["playcount"]
        tags = self.artist_info.get("tags", {}).get("tag", [])
        tag_names = [tag["name"] for tag in tags[:5]] if tags else []
        tag_text = " · ".join(tag_names)

        footer_text = f"Artist - {global_listeners} listeners · {global_plays} plays · {len(self.listeners)} server listeners"
        if tag_text:
            footer_text = f"{tag_text}\n{footer_text}"

        embed.set_footer(text=footer_text)
        
        return embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

class LastFM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = "15ee566c9ee0781f498674b14c17dc7e"
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.custom_commands = {}
        self.network = pylast.LastFMNetwork(
            api_key=os.getenv('LASTFM_API_KEY'),
            api_secret=os.getenv('LASTFM_API_SECRET')
        )
        self.tracking_channel = 1326226914255568906
        self.tracking_users = {}
        self.last_tracks = {}
        
        self.bot.loop.create_task(self.load_tracking_users())
        
        self.continuous_tracking.start()

    def cog_unload(self):
        self.continuous_tracking.cancel()

    async def cog_load(self):
        """Create necessary database tables on cog load"""
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lastfm_usernames (
                    user_id BIGINT PRIMARY KEY,
                    lastfm_username TEXT NOT NULL
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lastfm_custom_commands (
                    user_id BIGINT PRIMARY KEY,
                    emoji TEXT NOT NULL
                )
            """)
            
            records = await conn.fetch("SELECT user_id, emoji FROM lastfm_custom_commands")
            self.custom_commands = {record['user_id']: record['emoji'] for record in records}

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS lastfm_continuous_tracking (
                    user_id BIGINT PRIMARY KEY,
                    lastfm_username TEXT NOT NULL,
                    tracking_channel_id BIGINT NOT NULL
                )
            """)

    async def get_lastfm_username(self, user_id: int) -> Optional[str]:
        """Get Last.fm username for a Discord user"""
        async with self.bot.db.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT lastfm_username FROM lastfm_usernames WHERE user_id = $1",
                user_id
            )
            return record['lastfm_username'] if record else None

    async def set_lastfm_username(self, user_id: int, username: str):
        """Set Last.fm username for a Discord user"""
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO lastfm_usernames (user_id, lastfm_username)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET lastfm_username = $2
            """, user_id, username)

    async def fetch_lastfm_data(self, method: str, params: dict) -> Optional[dict]:
        """Generic method to fetch data from Last.fm API"""
        params.update({
            "method": method,
            "api_key": self.api_key,
            "format": "json"
        })
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Error {response.status}: {await response.text()}")
                        return None
            except Exception as e:
                print(f"Error fetching Last.fm data: {e}")
                return None

    async def error_embed(self, ctx, message: str):
        """Helper method to send error embeds"""
        embed = discord.Embed(
            description=message,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def lf(self, ctx):
        """Last.fm command group with various subcommands."""
        await ctx.send_help(ctx.command)

    @lf.command(name="set")
    async def lf_set(self, ctx, username: str):
        """Set your Last.fm username."""
        data = await self.fetch_lastfm_data("user.getInfo", {"user": username})
        
        if not data or "error" in data:
            await self.error_embed(ctx, "Invalid Last.fm username. Please check and try again.")
            return

        await self.set_lastfm_username(ctx.author.id, username)
        embed = discord.Embed(
            description=f"Successfully set your Last.fm username to **{username}**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @lf.command(name="cc")
    async def custom_command(self, ctx, *, trigger: str = None):
        """Set a custom command trigger for Last.fm
        
        Usage:
        ,lf cc - Sets as your custom command
        ,lf cc np - Sets "np" as your custom command
        ,lf cc - Shows your current custom command
        """
        if trigger is None:
            current = await self.get_custom_command(ctx.author.id)
            if current:
                await ctx.send(f"Your current Last.fm custom command is: `{current}`")
            else:
                await ctx.send("You don't have a custom command set. Use `,lf cc <trigger>` to set one.")
            return

        if len(trigger) > 30:
            await ctx.send("Custom command must be 30 characters or less.")
            return

        trigger = trigger.strip()
        
        await self.set_custom_command(ctx.author.id, trigger)
        await ctx.send(f"Set your Last.fm custom command to: `{trigger}`")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip()
        if not content:
            return

        custom_command = await self.get_custom_command(message.author.id)
        if not custom_command or content.lower() != custom_command.lower():
            return

        ctx = await self.bot.get_context(message)
        cmd = self.bot.get_command('fm')
        if cmd:
            await ctx.invoke(cmd)

    @commands.command(name="ap")
    async def artist_plays(self, ctx, *, artist_name: Optional[str] = None):
        """Shows plays for current/specified artist"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not artist_name:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                track = data["recenttracks"]["track"][0]
                artist_name = track["artist"]["#text"]

            data = await self.fetch_lastfm_data("artist.getInfo", {
                "artist": artist_name,
                "username": username
            })

            if not data or "error" in data:
                await self.error_embed(ctx, f"Could not find artist: {artist_name}")
                return

            try:
                artist_plays = int(data["artist"]["stats"]["userplaycount"])
                artist_name = data["artist"]["name"]
                embed = discord.Embed(
                    description=f"You have {artist_plays:,} plays for {artist_name}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            except (KeyError, ValueError):
                await self.error_embed(ctx, "Error parsing Last.fm data")

    @commands.command(name="about")
    async def about_artist(self, ctx, *, artist_name: Optional[str] = None):
        """Shows information about current/specified artist"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not artist_name:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                artist_name = data["recenttracks"]["track"][0]["artist"]["#text"]

            data = await self.fetch_lastfm_data("artist.getInfo", {
                "artist": artist_name
            })

            if not data or "error" in data:
                await self.error_embed(ctx, f"Could not find artist: {artist_name}")
                return

            try:
                artist = data["artist"]
                artist_name = artist["name"]
                listeners = int(artist["stats"]["listeners"])
                playcount = int(artist["stats"]["playcount"])

                tags = artist.get("tags", {}).get("tag", [])
                tag_names = [tag["name"] for tag in tags[:5]] if tags else []
                bio = artist.get("bio", {}).get("content", "No biography available.")
                bio = bio.split("<a href")[0].strip()
                
                embed = discord.Embed(
                    title=artist_name,
                    description=bio[:1000] + "..." if len(bio) > 1000 else bio,
                    color=discord.Color.red()
                )
                
                if artist.get("image"):
                    image_url = artist["image"][-1]["#text"]
                    if image_url:
                        embed.set_thumbnail(url=image_url)
                
                embed.add_field(
                    name="Stats",
                    value=f"Listeners: {listeners:,}\nTotal Plays: {playcount:,}",
                    inline=False
                )
                
                if tag_names:
                    embed.add_field(
                        name="Tags",
                        value=" • ".join(tag_names),
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
            except (KeyError, ValueError):
                await self.error_embed(ctx, "Error parsing Last.fm data")

    @commands.command(name="cover")
    async def album_cover(self, ctx, *, album_name: Optional[str] = None):
        """Shows album cover of current/specified album"""
        username = await self.get_lastfm_username(ctx.author.id)

        if not username:
            await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
            return

        if not album_name:
            data = await self.fetch_lastfm_data("user.getrecenttracks", {
                "user": username,
                "limit": 1
            })

            if not data or "error" in data or not data["recenttracks"]["track"]:
                await self.error_embed(ctx, "No currently playing track found.")
                return

            track = data["recenttracks"]["track"][0]
            artist_name = track["artist"]["#text"]
            album_name = track["album"]["#text"]
            image_url = track["image"][-1]["#text"] if track["image"] else None

            if not album_name:
                await self.error_embed(ctx, "Current track has no album information.")
                return
        else:
            data = await self.fetch_lastfm_data("album.search", {
                "album": album_name
            })

            if not data or "error" in data or not data["results"]["albummatches"]["album"]:
                await self.error_embed(ctx, f"Could not find album: {album_name}")
                return

            album = data["results"]["albummatches"]["album"][0]
            artist_name = album["artist"]
            album_name = album["name"]
            image_url = album["image"][-1]["#text"] if album["image"] else None

        if not image_url:
            await self.error_embed(ctx, "No album cover found.")
            return

        embed = discord.Embed(
            title=album_name,
            description=f"by {artist_name}",
            color=discord.Color.red()
        )
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    @commands.command(name="wkt", aliases=["whoknowstrack"])
    async def whoknows_track(self, ctx, *, track_name: str = None):
        """See who knows the currently playing or specified track"""
        try:
            async with ctx.typing():
                if not track_name:
                    username = await self.get_lastfm_username(ctx.author.id)
                    if not username:
                        return await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")

                    data = await self.fetch_lastfm_data("user.getrecenttracks", {
                        "user": username,
                        "limit": 1
                    })

                    if not data or "recenttracks" not in data or not data["recenttracks"]["track"]:
                        return await self.error_embed(ctx, "No recent tracks found.")

                    track = data["recenttracks"]["track"]
                    if not track or not isinstance(track, list):
                        return await self.error_embed(ctx, "Unable to retrieve track information.")
                    
                    track = track[0] if track else {}
                    artist = track.get("artist", {}).get("#text", "Unknown Artist")
                    track_name = track.get("name", "Unknown Track")
                else:
                    parts = track_name.split(" - ", 1)
                    if len(parts) == 2:
                        artist, track_name = parts
                    else:
                        artist = " ".join(parts[:-1]) or "Unknown Artist"
                        track_name = parts[-1]

                track_info = await self.fetch_lastfm_data("track.getInfo", {
                    "track": track_name,
                    "artist": artist
                }) or {}

                image_data = track_info.get("track", {}).get("album", {}).get("image", [])
                image = image_data if image_data and isinstance(image_data, list) else []

                listeners = []
                async with self.bot.db.acquire() as conn:
                    records = await conn.fetch(
                        "SELECT user_id, lastfm_username FROM lastfm_usernames"
                    )

                for record in records:
                    member = ctx.guild.get_member(record['user_id'])
                    if not member:
                        continue

                    try:
                        user_track_info = await self.fetch_lastfm_data("track.getInfo", {
                            "track": track_name,
                            "artist": artist,
                            "username": record['lastfm_username']
                        }) or {}

                        playcount = int(user_track_info.get("track", {}).get("userplaycount", 0))
                        
                        if playcount > 0:
                            listeners.append({
                                "member": member,
                                "plays": playcount,
                                "username": record['lastfm_username']
                            })
                    except Exception:
                        continue

                if not listeners:
                    embed = discord.Embed(
                        description=f"Nobody in this server has listened to {track_name} by {artist}",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                    return

                listeners.sort(key=lambda x: x["plays"], reverse=True)

                view = WhoKnowsPaginator(
                    ctx.author.id, 
                    listeners, 
                    f"{track_name} by {artist}", 
                    ctx.guild.name, 
                    {"image": image}
                )
                embed = view.get_page_content()
                
                view.message = await ctx.send(
                    embed=embed, 
                    view=view if len(listeners) > 10 else None
                )

        except Exception as e:
            print(f"Critical error in whoknows_track: {e}")
            await self.error_embed(ctx, f"An unexpected error occurred: {str(e)}")

    @commands.command(name="wka")
    async def whoknows_album(self, ctx):
        """See who knows the currently playing album in the server"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)
            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            data = await self.fetch_lastfm_data("user.getrecenttracks", {
                "user": username,
                "limit": 1
            })

            if not data or "error" in data or not data["recenttracks"]["track"]:
                await self.error_embed(ctx, "No currently playing track found.")
                return

            track = data["recenttracks"]["track"][0]
            artist = track["artist"]["#text"]
            album = track["album"]["#text"]

            if not album:
                await self.error_embed(ctx, "Current track has no album information.")
                return

            album_info = await self.fetch_lastfm_data("album.getInfo", {
                "artist": artist,
                "album": album
            })

            if not album_info or "album" not in album_info:
                await self.error_embed(ctx, "Could not fetch album information.")
                return

            listeners = []
            async with self.bot.db.acquire() as conn:
                records = await conn.fetch(
                    "SELECT user_id, lastfm_username FROM lastfm_usernames"
                )

            for record in records:
                member = ctx.guild.get_member(record['user_id'])
                if not member:
                    continue

                user_info = await self.fetch_lastfm_data("user.getInfo", {
                    "user": record['lastfm_username']
                })

                if user_info and "user" in user_info:
                    user_albums = await self.fetch_lastfm_data("user.getAlbumScrobbles", {
                        "user": record['lastfm_username'],
                        "album": album,
                        "artist": artist
                    })

                    if user_albums and "album" in user_albums:
                        plays = int(user_albums["album"]["userplaycount"])
                        if plays > 0:
                            listeners.append({
                                "member": member,
                                "plays": plays,
                                "username": record['lastfm_username']
                            })

            if not listeners:
                await self.error_embed(ctx, f"Nobody in this server has listened to {album} by {artist}")
                return

            listeners.sort(key=lambda x: x["plays"], reverse=True)

            view = WhoKnowsPaginator(ctx.author.id, listeners, f"{album} by {artist}", ctx.guild.name, album_info["album"])
            embed = view.get_page_content()
            
            view.message = await ctx.send(embed=embed, view=view if len(listeners) > 10 else None)

    @commands.command(name="gwk")
    async def global_whoknows(self, ctx, *, artist_name: str = None):
        """See who knows the specified artist or currently playing artist globally"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)
            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not artist_name:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                artist_name = data["recenttracks"]["track"][0]["artist"]["#text"]

            artist_info = await self.fetch_lastfm_data("artist.getInfo", {
                "artist": artist_name
            })

            if not artist_info or "artist" not in artist_info:
                await self.error_embed(ctx, f"Could not find artist: {artist_name}")
                return

            listeners = int(artist_info["artist"]["stats"]["listeners"])
            playcount = int(artist_info["artist"]["stats"]["playcount"])
            
            tags = artist_info["artist"].get("tags", {}).get("tag", [])
            tag_names = [tag["name"] for tag in tags[:5]] if tags else []

            embed = discord.Embed(
                title=f"Global Stats for {artist_name}",
                color=discord.Color.red()
            )

            if artist_info["artist"].get("image"):
                image_url = artist_info["artist"]["image"][-1]["#text"]
                if image_url:
                    embed.set_thumbnail(url=image_url)

            description = [
                f"Global Statistics",
                f"Listeners: {listeners:,}",
                f"Total Plays: {playcount:,}",
                "\nTop Listeners"
            ]

            top_fans = artist_info["artist"].get("stats", {}).get("topfans", {}).get("user", [])
            if top_fans:
                for i, fan in enumerate(top_fans[:10], 1):
                    username = fan["name"]
                    plays = int(fan.get("playcount", 0))
                    description.append(f"`{i}.` [{username}](https://last.fm/user/{username}) - **{plays:,}** plays")

            embed.description = "\n".join(description)

            if tag_names:
                embed.add_field(
                    name="Tags",
                    value=" • ".join(tag_names),
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.command(name="gwt")
    async def global_whoknows_track(self, ctx, *, track_name: str = None):
        """See who knows the specified track or currently playing track globally"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)
            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not track_name:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                track = data["recenttracks"]["track"][0]
                artist = track["artist"]["#text"]
                track_name = track["name"]
            else:
                if " - " in track_name:
                    track_name, artist = map(str.strip, track_name.split(" - ", 1))
                else:
                    await self.error_embed(ctx, "Please specify both track and artist (track - artist)")
                    return

            track_info = await self.fetch_lastfm_data("track.getInfo", {
                "track": track_name,
                "artist": artist
            })

            if not track_info or "track" not in track_info:
                await self.error_embed(ctx, "Could not fetch track information.")
                return

            embed = discord.Embed(
                title=f"Global Stats for {track_name}",
                description=f"by {artist}",
                color=discord.Color.red()
            )

            listeners = int(track_info["track"]["listeners"])
            playcount = int(track_info["track"]["playcount"])

            if track_info["track"].get("album") and track_info["track"]["album"].get("image"):
                image_url = track_info["track"]["album"]["image"][-1]["#text"]
                if image_url:
                    embed.set_thumbnail(url=image_url)

            description = [
                f"Global Statistics",
                f"Listeners: {listeners:,}",
                f"Total Plays: {playcount:,}",
                "\nTop Listeners"
            ]

            top_fans = track_info["track"].get("topfans", {}).get("user", [])
            if top_fans:
                for i, fan in enumerate(top_fans[:10], 1):
                    username = fan["name"]
                    plays = int(fan.get("playcount", 0))
                    description.append(f"`{i}.` [{username}](https://last.fm/user/{username}) - **{plays:,}** plays")

            embed.description = "\n".join(description)
            await ctx.send(embed=embed)

    @commands.command(name="gwa")
    async def global_whoknows_album(self, ctx):
        """See who knows the currently playing album globally"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)
            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            data = await self.fetch_lastfm_data("user.getrecenttracks", {
                "user": username,
                "limit": 1
            })

            if not data or "error" in data or not data["recenttracks"]["track"]:
                await self.error_embed(ctx, "No currently playing track found.")
                return

            track = data["recenttracks"]["track"][0]
            artist = track["artist"]["#text"]
            album = track["album"]["#text"]

            if not album:
                await self.error_embed(ctx, "Current track has no album information.")
                return

            album_info = await self.fetch_lastfm_data("album.getInfo", {
                "artist": artist,
                "album": album
            })

            if not album_info or "album" not in album_info:
                await self.error_embed(ctx, "Could not fetch album information.")
                return

            embed = discord.Embed(
                title=f"Global Stats for {album}",
                description=f"by {artist}",
                color=discord.Color.red()
            )

            listeners = int(album_info["album"]["listeners"])
            playcount = int(album_info["album"]["playcount"])

            if album_info["album"].get("image"):
                image_url = album_info["album"]["image"][-1]["#text"]
                if image_url:
                    embed.set_thumbnail(url=image_url)

            embed.add_field(
                name="Global Statistics",
                value=f"Listeners: {listeners:,}\nTotal Plays: {playcount:,}",
                inline=False
            )

            tags = album_info["album"].get("tags", {}).get("tag", [])
            if tags:
                tag_names = [tag["name"] for tag in tags[:5]]
                embed.add_field(
                    name="Tags",
                    value=" • ".join(tag_names),
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.command(name="spotify", aliases=["spot"])
    async def spotify_link(self, ctx):
        """Generate Spotify URL for the currently playing track"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            try:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data:
                    await self.error_embed(ctx, "Error fetching tracks.")
                    return

                track = data["recenttracks"]["track"][0]
                artist = track["artist"]["#text"]
                song = track["name"]

                spotify_search_url = f"https://open.spotify.com/search/{quote_plus(f'{song} {artist}')}"

                embed = discord.Embed(
                    title="Spotify Link",
                    description=f"[Open '{song}' by {artist} on Spotify]({spotify_search_url})",
                    color=discord.Color.green()
                )
                
                await ctx.send(embed=embed)

            except (KeyError, IndexError):
                await self.error_embed(ctx, "No recent tracks found.")

    async def search_tracks(self, track_name, username=None, artist=None, limit=5):
        """
        Search for tracks on Last.fm and return the most relevant results.
        
        :param track_name: Name of the track to search
        :param username: Optional username to get more personalized results
        :param artist: Optional artist name to narrow down the search
        :param limit: Number of results to return
        :return: List of track search results
        """
        params = {
            "track": track_name,
            "limit": limit
        }
        
        if username:
            params["username"] = username
        
        if artist:
            params["artist"] = artist
        
        try:
            search_data = await self.fetch_lastfm_data("track.search", params)
            
            if not search_data or "results" not in search_data or "trackmatches" not in search_data["results"]:
                return []
            
            tracks = search_data["results"]["trackmatches"]["track"]
            if not isinstance(tracks, list):
                tracks = [tracks]
            
            return tracks
        except Exception as e:
            print(f"Error searching tracks: {e}")
            return []

    @commands.command(name="auth")
    async def lastfm_auth(self, ctx):
        """Authenticate and link your Last.fm account."""
        embed = discord.Embed(
            title="Last.fm Account Authentication",
            description=(
                "To authenticate your Last.fm account:\n\n"
                "1. Go to https://www.last.fm/api/account/create\n"
                "2. Create a new API account\n"
                "3. Copy your API Key and Shared Secret\n"
                "4. Use `,lf set <your_lastfm_username>` to link your account\n\n"
                "**Note:** This is a basic authentication method. "
                "For full API access, you may need to implement OAuth."
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Protect your API credentials and never share them!")
        
        await ctx.send(embed=embed)

    async def get_custom_command(self, user_id: int) -> Optional[str]:
        """Get custom command emoji for a user"""
        async with self.bot.db.acquire() as conn:
            record = await conn.fetchrow(
                "SELECT emoji FROM lastfm_custom_commands WHERE user_id = $1",
                user_id
            )
            return record['emoji'] if record else None

    async def set_custom_command(self, user_id: int, emoji: str):
        """Set custom command emoji for a user"""
        async with self.bot.db.acquire() as conn:
            await conn.execute("""
                INSERT INTO lastfm_custom_commands (user_id, emoji)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET emoji = $2
            """, user_id, emoji)
            self.custom_commands[user_id] = emoji

    @commands.command(name="np", aliases=["nowplaying", "fm"])
    async def now_playing(self, ctx, user: Optional[discord.Member] = None):
        """Show currently playing track"""
        async with ctx.typing():
            target = user or ctx.author
            lastfm_username = await self.get_lastfm_username(target.id)

            if not lastfm_username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            try:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": lastfm_username,
                    "limit": 1
                })

                if not data or "error" in data:
                    await self.error_embed(ctx, "Error fetching tracks, this is most likely due to the Last.FM API, not the bot.")
                    return

                track = data["recenttracks"]["track"]
                if not track or not isinstance(track, list):
                    await self.error_embed(ctx, "Unable to retrieve track information.")
                    return
                
                track = track[0] if track else {}
                
                is_now_playing = track.get('@attr', {}).get('nowplaying') == 'true'
                
                artist = track.get("artist", {}).get("#text", "Unknown Artist")
                song = track.get("name", "Unknown Track")
                album = track.get("album", {}).get("#text", "Unknown Album")
                image_url = track.get("image", [{}])[-1].get("#text", None)

                artist_data = await self.fetch_lastfm_data("artist.getInfo", {
                    "artist": artist,
                    "username": lastfm_username
                }) or {}

                user_info = await self.fetch_lastfm_data("user.getInfo", {
                    "user": lastfm_username
                }) or {}

                track_url = f"https://www.last.fm/music/{quote_plus(artist)}/_/{quote_plus(song)}"
                lastfm_profile_url = f"https://www.last.fm/user/{lastfm_username}"

                artist_plays = int(artist_data.get("artist", {}).get("stats", {}).get("userplaycount", 0))
                total_scrobbles = int(user_info.get("user", {}).get("playcount", 0))

                description = [
                    f"[{song}]({track_url})",
                    f"{artist} · {album}" if album else artist
                ]

                embed = discord.Embed(
                    description="\n".join(description),
                    color=0xffffff
                )

                if image_url:
                    embed.set_thumbnail(url=image_url)

                avatar_url = (
                    user_info.get("user", {}).get("image", [{}])[-1].get("#text") 
                    or "https://cdn.discordapp.com/embed/avatars/0.png"
                )

                embed.set_author(
                    name=f"Now playing - {lastfm_username}", 
                    icon_url=avatar_url,
                    url=lastfm_profile_url
                )
                
                footer_text = f"{artist_plays} artist scrobbles · {total_scrobbles} total scrobbles"
                
                embed.set_footer(text=footer_text)

                message = await ctx.send(embed=embed)
                await message.add_reaction("🔥")
                await message.add_reaction("🗑️")

            except (KeyError, IndexError):
                await self.error_embed(ctx, "No recent tracks found.")

    @commands.command(name="recent", aliases=["recents", "history"])
    async def recent_tracks(self, ctx, *, user: Optional[discord.Member] = None):
        """Show recent tracks"""
        target = user or ctx.author
        username = await self.get_lastfm_username(target.id)

        if not username:
            await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
            return

        data = await self.fetch_lastfm_data("user.getrecenttracks", {
            "user": username,
            "limit": 9
        })

        if not data or "error" in data:
            await self.error_embed(ctx, "Error fetching recent tracks from Last.fm")
            return

        try:
            tracks = data["recenttracks"]["track"]
            
            recent_tracks_text = []
            for i, track in enumerate(tracks, 1):
                artist = track.get("artist", {}).get("#text", "Unknown Artist")
                song = track.get("name", "Unknown Track")
                
                now_playing = "@attr" in track and track["@attr"].get("nowplaying") == "true"
                
                track_url = f"https://www.last.fm/music/{quote_plus(artist)}/_/{quote_plus(song)}"
                
                track_format = f"{i}. [{song}]({track_url}) - {artist}"
                if now_playing:
                    track_format = f"{track_format}"
                
                recent_tracks_text.append(track_format)

            embed = discord.Embed(
                title=f"Recent Tracks for {username}",
                description="\n".join(recent_tracks_text),
                color=discord.Color.red()
            )

            embed.set_footer(text=f"Last.fm | {username}", icon_url=target.display_avatar.url)
            await ctx.send(embed=embed)

        except (KeyError, IndexError):
            await self.error_embed(ctx, "No recent tracks found.")

    @commands.command(name="topartists", aliases=["ta"])
    async def top_artists(self, ctx, period="at", *, user: Optional[discord.Member] = None):
        """Show top artists (period: at (all time), 7d, 1m, 3m, 6m, 12m)"""
        target = user or ctx.author
        username = await self.get_lastfm_username(target.id)

        if not username:
            await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
            return

        period_map = {
            "at": "overall",
            "7d": "7day",
            "1m": "1month",
            "3m": "3month",
            "6m": "6month",
            "12m": "12month"
        }

        if period not in period_map:
            await self.error_embed(ctx, "Invalid period. Choose from: at, 7d, 1m, 3m, 6m, 12m")
            return

        data = await self.fetch_lastfm_data("user.gettopartists", {
            "user": username,
            "period": period_map[period],
            "limit": 50
        })

        if not data or "error" in data:
            await self.error_embed(ctx, "Error fetching top artists from Last.fm")
            return

        try:
            artists = data["topartists"]["artist"]
            
            view = ArtistPaginator(ctx.author.id, artists, username, period)
            embed = view.get_page_content()
            
            view.message = await ctx.send(embed=embed, view=view)

        except (KeyError, IndexError):
            await self.error_embed(ctx, "No top artists found.")

    @lf.command(name="user")
    async def lf_user(self, ctx, user: Optional[discord.Member] = None):
        """Show a user's Last.fm profile information."""
        user = user or ctx.author
        
        lastfm_username = await self.get_lastfm_username(user.id)
        if not lastfm_username:
            return await self.error_embed(ctx, f"{user.mention} has not set their Last.fm username. Use `,lf set <username>` to set it.")

        user_info_response = await self.fetch_lastfm_data("user.getinfo", {"user": lastfm_username})
        
        if not user_info_response or "error" in user_info_response:
            return await self.error_embed(ctx, f"Invalid Last.fm username: {lastfm_username}")

        try:
            user_info = user_info_response.get('user', {})
            
            top_artists_params = {
                'user': lastfm_username,
                'period': 'overall',
                'limit': 1
            }
            top_artists_response = await self.fetch_lastfm_data('user.gettopartists', top_artists_params)

            unique_tracks_params = {
                'user': lastfm_username,
                'period': 'overall',
                'limit': 1
            }
            unique_tracks_response = await self.fetch_lastfm_data('user.gettoptracks', unique_tracks_params)

            unique_albums_params = {
                'user': lastfm_username,
                'period': 'overall',
                'limit': 1
            }
            unique_albums_response = await self.fetch_lastfm_data('user.gettopalbums', unique_albums_params)

            embed = discord.Embed(
                title=f"Last.fm Profile: {lastfm_username}",
                color=discord.Color.blurple(),
                url=f"https://www.last.fm/user/{lastfm_username}"
            )

            embed.add_field(name="Total Scrobbles", value=user_info.get('playcount', 'N/A'), inline=True)
            embed.add_field(name="Unique Tracks", value=len(unique_tracks_response.get('toptracks', {}).get('track', [])), inline=True)
            embed.add_field(name="Unique Albums", value=len(unique_albums_response.get('topalbums', {}).get('album', [])), inline=True)
            embed.add_field(name="Unique Artists", value=len(top_artists_response.get('topartists', {}).get('artist', [])), inline=True)

            registered = user_info.get('registered', {})
            if registered:
                account_creation = datetime.fromtimestamp(int(registered.get('#text', 0)))
                embed.add_field(name="Account Created", value=account_creation.strftime("%B %d, %Y"), inline=False)

            if user_info.get('image'):
                for img in user_info['image']:
                    if img.get('size') == 'large':
                        embed.set_thumbnail(url=img['#text'])
                        break

            view = discord.ui.View()
            
            scrobbles_button = discord.ui.Button(
                label="Scrobbles", 
                style=discord.ButtonStyle.link, 
                url=f"https://www.last.fm/user/{lastfm_username}/library"
            )
            view.add_item(scrobbles_button)

            profile_button = discord.ui.Button(
                label="Profile", 
                style=discord.ButtonStyle.link, 
                url=f"https://www.last.fm/user/{lastfm_username}"
            )
            view.add_item(profile_button)

            await ctx.send(embed=embed, view=view)

        except Exception as e:
            import traceback
            print(f"Full error details for {lastfm_username}:")
            traceback.print_exc()
            await self.error_embed(ctx, f"Could not fetch Last.fm profile for {lastfm_username}. Error: {str(e)}")

    @commands.command(name="whoknows", aliases=["wk"], help="Shows who listens to a specific artist in the server")
    async def whoknows(self, ctx, *, artist: str = None):
        """Shows who listens to a specific artist in the server"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)
            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not artist:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                artist = data["recenttracks"]["track"][0]["artist"]["#text"]

            artist_info = await self.fetch_lastfm_data("artist.getInfo", {
                "artist": artist
            })

            if not artist_info or "artist" not in artist_info:
                await self.error_embed(ctx, f"Could not find artist: {artist}")
                return

            listeners = []
            async with self.bot.db.acquire() as conn:
                records = await conn.fetch(
                    "SELECT user_id, lastfm_username FROM lastfm_usernames"
                )

            for record in records:
                member = ctx.guild.get_member(record['user_id'])
                if not member:
                    continue

                user_info = await self.fetch_lastfm_data("user.getInfo", {
                    "user": record['lastfm_username']
                })

                if user_info and "user" in user_info:
                    user_artist_data = await self.fetch_lastfm_data("artist.getInfo", {
                        "artist": artist,
                        "username": record['lastfm_username']
                    })

                    if user_artist_data and "artist" in user_artist_data:
                        plays = int(user_artist_data["artist"]["stats"]["userplaycount"])
                        if plays > 0:
                            listeners.append({
                                "member": member,
                                "plays": plays,
                                "username": record['lastfm_username']
                            })

            if not listeners:
                await self.error_embed(ctx, f"Nobody in this server has listened to {artist}")
                return

            listeners.sort(key=lambda x: x["plays"], reverse=True)

            view = WhoKnowsPaginator(ctx.author.id, listeners, artist, ctx.guild.name, artist_info["artist"])
            embed = view.get_page_content()
            
            view.message = await ctx.send(embed=embed, view=view if len(listeners) > 10 else None)

    @commands.command(name="addtracking", help="Add a Last.fm username for continuous tracking.")
    @commands.has_permissions(manage_channels=True)
    async def add_tracking(self, ctx, lastfm_username: str):
        """
        Add a Last.fm username to continuous tracking.
        
        Usage: ,addtracking [lastfm_username]
        """
        try:
            response = requests.get(
                f"http://ws.audioscrobbler.com/2.0/?method=user.getinfo&user={lastfm_username}&api_key={self.api_key}&format=json"
            )
            
            if response.status_code == 200:
                user_data = response.json()
                if 'user' in user_data:
                    with open('/Users/playfair/Downloads/hersey-main/cogs/lastfm/tracking_users.py', 'r') as f:
                        content = f.read()
                    
                    import ast
                    tracking_users = ast.literal_eval(content.split('=')[1].strip())
                    
                    tracking_users[ctx.author.id] = lastfm_username
                    
                    with open('/Users/playfair/Downloads/hersey-main/cogs/lastfm/tracking_users.py', 'w') as f:
                        f.write(f"# Tracking users for continuous Last.fm tracking\nTRACKING_USERS = {tracking_users}")
                    
                    await ctx.send(f"Added {lastfm_username} to continuous tracking.")
                    return
            
            await ctx.send(f"Invalid Last.fm username: {lastfm_username}")
        
        except Exception as e:
            await ctx.send(f"Error adding tracking: {str(e)}")

    @commands.command(name="removetracking", help="Remove your Last.fm continuous tracking.")
    async def remove_tracking(self, ctx):
        """
        Remove your Last.fm username from continuous tracking.
        
        Usage: ,removetracking
        """
        try:
            with open('/Users/playfair/Downloads/hersey-main/cogs/lastfm/tracking_users.py', 'r') as f:
                content = f.read()
            
            import ast
            tracking_users = ast.literal_eval(content.split('=')[1].strip())
            
            if ctx.author.id in tracking_users:
                del tracking_users[ctx.author.id]
                
                with open('/Users/playfair/Downloads/hersey-main/cogs/lastfm/tracking_users.py', 'w') as f:
                    f.write(f"# Tracking users for continuous Last.fm tracking\nTRACKING_USERS = {tracking_users}")
                
                await ctx.send("Removed your Last.fm continuous tracking.")
            else:
                await ctx.send("You are not currently being tracked.")
        
        except Exception as e:
            await ctx.send(f"Error removing tracking: {str(e)}")

    async def load_tracking_users(self):
        """
        Load tracking users from the tracking_users.py file.
        """
        try:
            import importlib
            import sys
            
            if 'cogs.lastfm.tracking_users' in sys.modules:
                del sys.modules['cogs.lastfm.tracking_users']
            
            import cogs.lastfm.tracking_users as tracking_users_module
            
            self.tracking_users.clear()
            
            self.tracking_users.update(tracking_users_module.TRACKING_USERS)
            
            print(f"Total tracking users loaded: {len(self.tracking_users)}")
        
        except Exception as e:
            print(f"Error loading tracking users: {e}")

    @tasks.loop(seconds=1)
    async def continuous_tracking(self):
        """
        Continuously track Last.fm listening history for registered users.
        Checks every 1 second and posts updates to the dedicated channel when track changes.
        """
        try:
            channel = self.bot.get_channel(self.tracking_channel)
            if not channel:
                print("Tracking channel not found.")
                self.continuous_tracking.stop()
                return

            for user_id, lastfm_username in list(self.tracking_users.items()):
                try:
                    data = await self.fetch_lastfm_data("user.getrecenttracks", {
                        "user": lastfm_username,
                        "limit": 1
                    })

                    if not data or "error" in data:
                        continue

                    track = data["recenttracks"]["track"]
                    
                    if not track or not isinstance(track, list):
                        continue
                    
                    track = track[0] if track else {}
                    
                    is_now_playing = track.get('@attr', {}).get('nowplaying') == 'true'
                    
                    if is_now_playing:
                        artist = track.get("artist", {}).get("#text", "Unknown Artist")
                        song = track.get("name", "Unknown Track")
                        album = track.get("album", {}).get("#text", "Unknown Album")
                        image_url = track.get("image", [{}])[-1].get("#text", None)

                        current_track_id = f"{artist} - {song}"
                        
                        last_track_data = self.last_tracks.get(lastfm_username, {})
                        last_track = last_track_data.get('track')

                        if current_track_id != last_track:
                            artist_data = await self.fetch_lastfm_data("artist.getInfo", {
                                "artist": artist,
                                "username": lastfm_username
                            }) or {}

                            user_info = await self.fetch_lastfm_data("user.getInfo", {
                                "user": lastfm_username
                            }) or {}

                            track_url = f"https://www.last.fm/music/{quote_plus(artist)}/_/{quote_plus(song)}"
                            lastfm_profile_url = f"https://www.last.fm/user/{lastfm_username}"

                            artist_plays = int(artist_data.get("artist", {}).get("stats", {}).get("userplaycount", 0))
                            total_scrobbles = int(user_info.get("user", {}).get("playcount", 0))

                            description = [
                                f"[{song}]({track_url})",
                                f"{artist} · {album}" if album else artist
                            ]

                            embed = discord.Embed(
                                description="\n".join(description),
                                color=0xffffff
                            )

                            if image_url:
                                embed.set_thumbnail(url=image_url)

                            avatar_url = (
                                user_info.get("user", {}).get("image", [{}])[-1].get("#text") 
                                or "https://cdn.discordapp.com/embed/avatars/0.png"
                            )

                            embed.set_author(
                                name=f"Now playing - {lastfm_username}", 
                                icon_url=avatar_url,
                                url=lastfm_profile_url
                            )
                            
                            footer_text = f"{artist_plays} artist scrobbles · {total_scrobbles} total scrobbles"
                            
                            embed.set_footer(text=footer_text)

                            try:
                                await channel.send(embed=embed)
                                
                                self.last_tracks[lastfm_username] = {
                                    'track': current_track_id
                                }
                            except Exception as send_error:
                                print(f"Failed to send message for {lastfm_username}: {send_error}")

                except Exception as user_error:
                    print(f"Error processing user {lastfm_username}: {user_error}")

        except Exception as e:
            print(f"Unexpected error in continuous tracking: {e}")
            self.continuous_tracking.stop()

    @continuous_tracking.before_loop
    async def before_continuous_tracking(self):
        await self.bot.wait_until_ready()

    @commands.command(name="last")
    async def last_track(self, ctx, *, user: Optional[discord.Member] = None):
        """Show the last played track (excluding currently playing track)"""
        async with ctx.typing():
            target = user or ctx.author
            username = await self.get_lastfm_username(target.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            data = await self.fetch_lastfm_data("user.getrecenttracks", {
                "user": username,
                "limit": 2
            })

            if not data or "error" in data:
                await self.error_embed(ctx, "Error fetching recent tracks from Last.fm")
                return

            try:
                tracks = data["recenttracks"]["track"]
                
                last_track = next((track for track in tracks if "@attr" not in track), None)
                
                if not last_track:
                    await self.error_embed(ctx, "No last track found.")
                    return

                artist = last_track.get("artist", {}).get("#text", "Unknown Artist")
                song = last_track.get("name", "Unknown Track")
                album = last_track.get("album", {}).get("#text", "Unknown Album")
                image_url = last_track.get("image", [{}])[-1].get("#text", None)
                
                track_url = f"https://www.last.fm/music/{quote_plus(artist)}/_/{quote_plus(song)}"
                
                track_info = await self.fetch_lastfm_data("track.getInfo", {
                    "artist": artist,
                    "track": song,
                    "username": username
                }) or {}

                artist_info = await self.fetch_lastfm_data("artist.getInfo", {
                    "artist": artist,
                    "username": username
                }) or {}

                user_track_plays = track_info.get("track", {}).get("userplaycount", "0")
                user_artist_plays = artist_info.get("artist", {}).get("stats", {}).get("userplaycount", "0")

                embed = discord.Embed(
                    description=f"[{song}]({track_url})\n{artist} · {album}",
                    color=discord.Color.red()
                )

                if image_url:
                    embed.set_thumbnail(url=image_url)

                embed.set_author(
                    name=f"Last Track - {username}", 
                    icon_url=target.display_avatar.url
                )

                embed.set_footer(text=f"Track plays: {user_track_plays} · Artist plays: {user_artist_plays}")

                await ctx.send(embed=embed)

            except (KeyError, IndexError):
                await self.error_embed(ctx, "No last track found.")

    @commands.group(name="plays", aliases=["p", "scrobbles"], invoke_without_command=True)
    async def plays(self, ctx, user: discord.Member = None):
        """Shows total Last.fm scrobbles for a user"""
        if ctx.invoked_subcommand is None:
            pass
        target = user or ctx.author
        username = await self.get_lastfm_username(target.id)

        if not username:
            await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
            return

        async with ctx.typing():
            data = await self.fetch_lastfm_data("user.getInfo", {
                "user": username
            })

            if not data or "error" in data:
                await self.error_embed(ctx, "Error fetching data from Last.fm")
                return

            try:
                total_plays = int(data["user"]["playcount"])
                embed = discord.Embed(
                    description=f"{target.mention} has {total_plays:,} total scrobbles",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            except (KeyError, ValueError):
                await self.error_embed(ctx, "Error parsing Last.fm data")
        
    @plays.command(name="artist", aliases= ["a"])
    async def artist_plays(self, ctx, *, artist_name: Optional[str] = None):
        """Shows plays for current/specified artist"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            if not artist_name:
                data = await self.fetch_lastfm_data("user.getrecenttracks", {
                    "user": username,
                    "limit": 1
                })

                if not data or "error" in data or not data["recenttracks"]["track"]:
                    await self.error_embed(ctx, "No currently playing track found.")
                    return

                track = data["recenttracks"]["track"][0]
                artist_name = track["artist"]["#text"]

            data = await self.fetch_lastfm_data("artist.getInfo", {
                "artist": artist_name,
                "username": username
            })

            if not data or "error" in data:
                await self.error_embed(ctx, f"Could not find artist: {artist_name}")
                return

            try:
                artist_plays = int(data["artist"]["stats"]["userplaycount"])
                artist_name = data["artist"]["name"]
                embed = discord.Embed(
                    description=f"You have `{artist_plays:,}` plays for *{artist_name}*",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            except (KeyError, ValueError):
                await self.error_embed(ctx, "Error parsing Last.fm data")


    @plays.command(name="song", aliases= ["s", "track"])
    async def song_plays(self, ctx, *, song_name: Optional[str] = None):
        """Shows plays for current/specified song"""
        async with ctx.typing():
            username = await self.get_lastfm_username(ctx.author.id)

            if not username:
                await self.error_embed(ctx, "No Last.fm username set. Use `,lf set <username>` to set one.")
                return

            current_artist = None
            data = await self.fetch_lastfm_data("user.getrecenttracks", {
                "user": username,
                "limit": 1
            })

            if data and "recenttracks" in data and data["recenttracks"]["track"]:
                current_artist = data["recenttracks"]["track"][0]["artist"]["#text"]

            if not song_name:
                track = data["recenttracks"]["track"][0]
                artist_name = track["artist"]["#text"]
                song_name = track["name"]
            else:
                tracks = []
                if current_artist:
                    tracks = await self.search_tracks(song_name, username, artist=current_artist)
                
                if not tracks:
                    tracks = await self.search_tracks(song_name, username)
                
                if not tracks:
                    await self.error_embed(ctx, f"No tracks found matching '{song_name}'")
                    return
                
                best_match = tracks[0]
                song_name = best_match["name"]
                artist_name = best_match["artist"]
 
                if len(tracks) > 1:
                    selection_embed = discord.Embed(
                        title="Multiple Tracks Found",
                        description="Please select a track by typing its number:",
                        color=discord.Color.blue()
                    )
                    
                    for i, track in enumerate(tracks[:5], 1):
                        selection_embed.add_field(
                            name=f"{i}. {track['name']}", 
                            value=f"Artist: {track['artist']}", 
                            inline=False
                        )
                    
                    selection_embed.set_footer(text="You have 30 seconds to respond.")
                    
                    await ctx.send(embed=selection_embed)
                    
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
                    
                    try:
                        response = await self.bot.wait_for('message', check=check, timeout=30.0)
                        index = int(response.content) - 1
                        
                        if 0 <= index < len(tracks):
                            best_match = tracks[index]
                            song_name = best_match["name"]
                            artist_name = best_match["artist"]
                        else:
                            await ctx.send(embed=discord.Embed(
                                description="Invalid selection. Using the first result.", 
                                color=discord.Color.orange()
                            ))
                    except asyncio.TimeoutError:
                        await ctx.send(embed=discord.Embed(
                            description="No selection made. Using the first result.", 
                            color=discord.Color.orange()
                        ))

            track_data = await self.fetch_lastfm_data("track.getInfo", {
                "track": song_name,
                "artist": artist_name,
                "username": username
            })

            if not track_data or "track" not in track_data:
                await self.error_embed(ctx, f"Could not find track: {song_name} by {artist_name}")
                return

            try:
                plays = int(track_data["track"].get("userplaycount", 0))
                song_name = track_data["track"]["name"]
                artist_name = track_data["track"]["artist"]["name"]
                
                embed = discord.Embed(
                    description=f"You have `{plays:,}` plays for *{song_name}* by *{artist_name}*",
                    color=discord.Color.red()
                )
                
                if track_data["track"].get("album") and track_data["track"]["album"].get("image"):
                    image_url = track_data["track"]["album"]["image"][-1]["#text"]
                    if image_url:
                        embed.set_thumbnail(url=image_url)
                
                await ctx.send(embed=embed)
            except (KeyError, ValueError):
                await self.error_embed(ctx, "Error parsing Last.fm data")

async def setup(bot):
    await bot.add_cog(LastFM(bot))
