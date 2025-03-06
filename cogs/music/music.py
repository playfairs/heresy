import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class AppleMusic(
    Cog,
    command_attrs=dict(hidden=True)
):
    def __init__(self, bot):
        self.bot = bot
        self.user_tracking = {}
        self.db_path = "./json/applemusic_tracking.json"
        self.load_tracking_data()

    def load_tracking_data(self):
        """Load existing tracking data from JSON file."""
        if not os.path.exists(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w') as f:
                json.dump({}, f)
        
        with open(self.db_path, 'r') as f:
            self.user_tracking = json.load(f)

    def save_tracking_data(self):
        """Save tracking data to JSON file."""
        with open(self.db_path, 'w') as f:
            json.dump(self.user_tracking, f, indent=4)

    @commands.group(name="applemusic")
    async def apple_music_group(self, ctx):
        """Apple Music tracking commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(self.apple_music_group)

    @apple_music_group.command(name="playing", aliases=["np", "now"])
    async def now_playing(self, ctx):
        """Show the currently playing track."""
        member = ctx.author
        
        apple_music_activity = next((
            activity for activity in member.activities 
            if isinstance(activity, discord.Activity) and 
            activity.type == discord.ActivityType.listening and
            activity.name == "Apple Music"
        ), None)

        if not apple_music_activity:
            custom_activity = next((
                activity for activity in member.activities 
                if isinstance(activity, discord.Activity) and 
                activity.type == discord.ActivityType.custom
            ), None)
            
            if custom_activity and custom_activity.name:
                try:
                    parts = custom_activity.name.split(" - ")
                    if len(parts) >= 2 and "on Apple Music" in custom_activity.name:
                        apple_music_activity = type('AppleMusicActivity', (), {
                            'details': parts[1].split(" on ")[0].strip(),
                            'state': parts[0].strip()
                        })
                except:
                    apple_music_activity = None

        if apple_music_activity and hasattr(apple_music_activity, 'details') and hasattr(apple_music_activity, 'state'):

            embed = discord.Embed(
                title="🎵 Now Playing on Apple Music",
                color=discord.Color.red()
            )
            embed.add_field(name="Track", value=apple_music_activity.details, inline=False)
            embed.add_field(name="Artist", value=apple_music_activity.state, inline=False)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🎵 No Music Detected",
                description="Could not find any Apple Music activity.\n\n"
                            "**Troubleshooting:**\n"
                            "- Ensure Apple Music is playing\n"
                            "- Check Discord Rich Presence settings\n"
                            "- Verify Vencord custom status integration",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Feature under active development")
            await ctx.send(embed=embed)

    @apple_music_group.command(name="track")
    async def track_music(self, ctx, *, apple_music_username: str = None):
        """Set up Apple Music tracking for your account."""
        if apple_music_username is None:
            await ctx.send("Please provide your Apple Music username.")
            return

        self.user_tracking[str(ctx.author.id)] = {
            "username": apple_music_username,
            "tracking_method": "vencord"
        }
        self.save_tracking_data()
        await ctx.send(f"Now tracking Apple Music for {apple_music_username}")

    @apple_music_group.command(name="untrack")
    async def untrack_music(self, ctx):
        """Stop tracking Apple Music for your account."""
        if str(ctx.author.id) in self.user_tracking:
            del self.user_tracking[str(ctx.author.id)]
            self.save_tracking_data()
            await ctx.send("Stopped tracking Apple Music.")
        else:
            await ctx.send("You are not currently being tracked.")

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playlists_file = os.path.join(os.path.dirname(__file__), '..', '..', 'json', 'playlists.json')

    def load_playlists(self):
        """Load playlists from JSON file."""
        try:
            with open(self.playlists_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def save_playlists(self, playlists):
        """Save playlists to JSON file."""
        with open(self.playlists_file, 'w') as f:
            json.dump(playlists, f, indent=4)

    @commands.group(name="playlist", invoke_without_command=True)
    async def playlist(self, ctx):
        """Playlist management commands."""
        await ctx.send_help(ctx.command)

    @playlist.command(name="send")
    async def playlist_send(self, ctx, keyword: str):
        """Send a playlist URL by keyword."""
        playlists = self.load_playlists()
        
        if keyword.lower() not in playlists:
            await ctx.send(f"No playlist found for keyword '{keyword}'.")
            return
        
        playlist_url = playlists[keyword.lower()]
        await ctx.send(f"Playlist '{keyword}': {playlist_url}")

    @playlist.command(name="list")
    async def playlist_list(self, ctx):
        """List all available playlists with pagination."""
        playlists = self.load_playlists()
        
        if not playlists:
            await ctx.send("No playlists available.")
            return
        
        playlist_items = list(playlists.items())
        ITEMS_PER_PAGE = 10
        
        class PlaylistPaginatorView(discord.ui.View):
            def __init__(self, playlists, author):
                super().__init__()
                self.playlists = playlists
                self.author = author
                self.current_page = 0
                self.max_pages = (len(playlists) - 1) // ITEMS_PER_PAGE
            
            def get_page_items(self):
                """Get items for the current page."""
                start = self.current_page * ITEMS_PER_PAGE
                end = start + ITEMS_PER_PAGE
                return self.playlists[start:end]
            
            @discord.ui.button(label=" ", emoji="<:left:1307448382326968330>", style=discord.ButtonStyle.secondary)
            async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.author:
                    await interaction.response.send_message("You can't control this menu.", ephemeral=True)
                    return
                
                self.current_page = max(0, self.current_page - 1)
                
                embed = discord.Embed(
                    title="Available Playlists", 
                    color=discord.Color.blue()
                )
                
                page_items = self.get_page_items()
                
                description = "\n".join([f"• [{keyword}]({url})" for keyword, url in page_items])
                embed.description = description
                
                embed.set_footer(text=f"Page {self.current_page + 1} of {self.max_pages + 1}")
                
                await interaction.response.edit_message(embed=embed, view=self)
            
            @discord.ui.button(label=" ", emoji="<:right:1307448399624405134>", style=discord.ButtonStyle.secondary)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.author:
                    await interaction.response.send_message("You can't control this menu.", ephemeral=True)
                    return
                
                self.current_page = min(self.max_pages, self.current_page + 1)
                
                embed = discord.Embed(
                    title="Available Playlists", 
                    color=discord.Color.blue()
                )
                
                page_items = self.get_page_items()
                
                description = "\n".join([f"• [{keyword}]({url})" for keyword, url in page_items])
                embed.description = description
                
                embed.set_footer(text=f"Page {self.current_page + 1} of {self.max_pages + 1}")
                
                await interaction.response.edit_message(embed=embed, view=self)
        
        initial_embed = discord.Embed(
            title="Available Playlists", 
            color=discord.Color.blue()
        )
        
        first_page_items = playlist_items[:ITEMS_PER_PAGE]
        
        initial_description = "\n".join([f"• [{keyword}]({url})" for keyword, url in first_page_items])
        initial_embed.description = initial_description
        
        initial_embed.set_footer(text=f"Page 1 of {(len(playlist_items) - 1) // ITEMS_PER_PAGE + 1}")
        
        view = PlaylistPaginatorView(playlist_items, ctx.author)
        
        await ctx.send(embed=initial_embed, view=view)

    @playlist.command(name="add")
    @commands.is_owner()
    async def playlist_add(self, ctx, keyword: str, url: str):
        """Add a new playlist (bot owner only)."""
        playlists = self.load_playlists()
        
        if not (url.startswith('http://') or url.startswith('https://')):
            await ctx.send("Invalid URL. Must start with http:// or https://")
            return

        keyword = keyword.lower()
        
        if keyword in playlists:
            await ctx.send(f"Playlist '{keyword}' already exists. Use a different keyword.")
            return
        
        playlists[keyword] = url
        self.save_playlists(playlists)
        
        embed = discord.Embed(
            title="Playlist Added", 
            description=f"Added playlist '{keyword}': {url}", 
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AppleMusic(bot))
    await bot.add_cog(Playlist(bot))