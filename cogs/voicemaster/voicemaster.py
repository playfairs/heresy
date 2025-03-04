import discord
from discord.ext import commands
from googleapiclient.discovery import build
import yt_dlp
import asyncio
from discord import FFmpegPCMAudio
from discord.utils import get
from discord.ext import tasks, commands
from discord.ext.commands import group, has_permissions
import os
import numpy as np
import uwuipy

YOUTUBE_API_KEY = "key"

class VoiceMaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.no_context = {}
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        self.audio_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'Assets', 'MP3', 'Roblox Hi Wave Sound Effect.mp3')
        
        if not os.path.exists(self.audio_path):
            print(f"WARNING: Audio file not found at {self.audio_path}")
        else:
            print(f"Audio file found at {self.audio_path}")
        
        self.persistent_voice_channel = None
        self.last_activity_time = None
        self.keep_connected_tasks = {}
        
        self.bot.loop.create_task(self.start_keep_connected())
        self.bot.loop.create_task(self.voice_connection_manager())

    async def start_keep_connected(self):
        """Start keeping voice connections alive."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for voice_client in self.bot.voice_clients:
                    if voice_client.channel.id not in self.keep_connected_tasks:
                        task = self.bot.loop.create_task(self.keep_voice_connection_alive(voice_client))
                        self.keep_connected_tasks[voice_client.channel.id] = task
            except Exception as e:
                print(f"Error in start_keep_connected: {e}")
            
            await asyncio.sleep(60)

    async def keep_voice_connection_alive(self, voice_client):
        """Keep a voice connection alive by playing a silent audio stream."""
        try:
            while voice_client.is_connected():
                silent_frame = np.zeros(1920, dtype=np.int16)
                
                silent_bytes = silent_frame.tobytes()
                
                if not voice_client.is_playing():
                    with open('silent.raw', 'wb') as f:
                        f.write(silent_bytes)
                    
                    source = discord.FFmpegPCMAudio('silent.raw', pipe=True)
                    voice_client.play(source, after=lambda e: print('Silence played'))
                
                await asyncio.sleep(5)
        except Exception as e:
            print(f"Error in keep_voice_connection_alive: {e}")
        finally:
            if voice_client.channel.id in self.keep_connected_tasks:
                del self.keep_connected_tasks[voice_client.channel.id]

    async def voice_connection_manager(self):
        """Background task to manage persistent voice connection."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                if self.persistent_voice_channel and self.last_activity_time:
                    current_time = discord.utils.utcnow()
                    time_since_last_activity = (current_time - self.last_activity_time).total_seconds()
                    
                    if time_since_last_activity > 600:
                        for voice_client in self.bot.voice_clients:
                            if voice_client.channel == self.persistent_voice_channel:
                                await voice_client.disconnect()
                                print("Disconnected from voice channel due to inactivity")
                                
                                self.persistent_voice_channel = None
                                self.last_activity_time = None
                                break
            
            except Exception as e:
                print(f"Error in voice connection manager: {e}")
            
            await asyncio.sleep(300)

    @commands.command(name="join")
    async def join(self, ctx):
        """Join the user's voice channel."""
        print(f"Join command called by {ctx.author}")
        print(f"User voice state: {ctx.author.voice}")

        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to use this command.")
            return

        voice_channel = ctx.author.voice.channel
        print(f"Voice channel: {voice_channel}")

        if ctx.voice_client:
            if ctx.voice_client.channel == voice_channel:
                await ctx.send("I'm already in your voice channel.")
                return
            
            await ctx.voice_client.move_to(voice_channel)
            await ctx.send(f"Moved to {voice_channel.name}")
            return

        try:
            await voice_channel.connect()
            await ctx.send(f"Joined {voice_channel.name}")
        except Exception as e:
            print(f"Error joining voice channel: {e}")
            await ctx.send(f"Could not join the voice channel: {str(e)}")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Leave the current voice channel."""
        if ctx.voice_client and ctx.voice_client.is_connected():
            channel_id = ctx.voice_client.channel.id
            if channel_id in self.keep_connected_tasks:
                task = self.keep_connected_tasks[channel_id]
                task.cancel()
                del self.keep_connected_tasks[channel_id]
            
            await ctx.voice_client.disconnect()
            await ctx.send("no fuck you, i'll leave on my own.")
        else:
            await ctx.send("no means no bruh")

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        """Play music from a YouTube link or search."""
        channel_id = ctx.channel.id
        
        if (channel_id in self.no_context and 
            ctx.message.content.lower() == 'yes'):
            await ctx.send("no means no bruh")
            del self.no_context[channel_id]
            return

        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel to play music.")
            self.no_context[channel_id] = True
            return

        if not ctx.voice_client:
            await ctx.send("I'm not connected to a voice channel.")
            self.no_context[channel_id] = True
            return

        if ctx.voice_client.is_playing():
            await ctx.send("Already playing something. Stop current playback first.")
            self.no_context[channel_id] = True
            return

        try:
            if channel_id in self.no_context:
                del self.no_context[channel_id]

            if not query.startswith("http"):
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                request = youtube.search().list(
                    q=query, part="snippet", type="video", maxResults=1
                )
                response = request.execute()
                
                if not response['items']:
                    await ctx.send("No results found for your search.")
                    return
                
                video = response["items"][0]
                video_id = video["id"]["videoId"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                await ctx.send(f"🔍 Found: **{video['snippet']['title']}**\n{url}")
            else:
                url = query

            await ctx.send("Processing...")
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    await ctx.send("Could not retrieve audio information.")
                    return
                
                audio_url = info['formats'][0]['url']
                source = await discord.FFmpegOpusAudio.from_probe(audio_url, **{'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'})
                
                ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
                await ctx.send(f"🎵 Now playing: **{info['title']}**")

        except Exception as e:
            print(f"Error in play command: {e}")
            await ctx.send(f"An error occurred: {str(e)}")
            self.no_context[channel_id] = True

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stop the current playback."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏹️ Stopped playback.")
        else:
            await ctx.send("no means no bruh")

    @commands.command(name="search")
    async def search(self, ctx, *, query: str):
        """Search YouTube for a video and return the link."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query, part="snippet", type="video", maxResults=1
        )
        response = request.execute()

        video = response["items"][0]
        video_title = video["snippet"]["title"]
        video_id = video["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        await ctx.send(f"🔍 Found: **{video_title}**\n{video_url}")

    @commands.command(name="sdeafen", aliases= ["sd", "deafen"])
    @commands.has_permissions(moderate_members=True)
    async def server_deafen(self, ctx, member: discord.Member = None):
        """Server deafens the mentioned member, or self if none mentioned."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        target = member or ctx.author
        try:
            await target.edit(deafen=True)
            await ctx.send(f"👍")
        except discord.Forbidden:
            await ctx.send("no means no bruh")
        except Exception as e:
            await ctx.send(f"no means no bruh")

    @commands.command(name="smute", aliases= ["sm", "mute"])
    @commands.has_permissions(moderate_members=True)
    async def server_mute(self, ctx, member: discord.Member = None):
        """Server mutes the mentioned member, or self if none mentioned."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        target = member or ctx.author
        try:
            await target.edit(mute=True)
            await ctx.send(f"👍")
        except discord.Forbidden:
            await ctx.send("no means no bruh")
        except Exception as e:
            await ctx.send(f"no means no bruh")

    @commands.command(name="sundeafen", aliases= ["sund", "sunday", "undeafen"])
    @commands.has_permissions(moderate_members=True)
    async def server_undeafen(self, ctx, member: discord.Member = None):
        """Server undeafens the mentioned member, or self if none mentioned."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        target = member or ctx.author
        try:
            await target.edit(deafen=False)
            await ctx.send(f"👍")
        except discord.Forbidden:
            await ctx.send("no means no bruh")
        except Exception as e:
            await ctx.send(f"no means no bruh")

    @commands.command(name="sunmute", aliases= ["sum", "unmute"])
    @commands.has_permissions(moderate_members=True)
    async def server_unmute(self, ctx, member: discord.Member = None):
        """Server unmutes the mentioned member, or self if none mentioned."""
        if ctx.message.content.lower() in ["yes", "please"]:
            await ctx.send("no means no bruh")
            return

        target = member or ctx.author
        try:
            await target.edit(mute=False)
            await ctx.send(f"👍")
        except discord.Forbidden:
            await ctx.send("no means no bruh")
        except Exception as e:
            await ctx.send(f"no means no bruh")
