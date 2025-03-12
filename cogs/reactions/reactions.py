import discord
from discord.ext import commands
from discord.ext.commands import Cog
import random
import sqlite3
import os
import asyncio
import json
import re
import aiohttp
from datetime import datetime, timedelta

from main import heresy

class Reactions(Cog, description="View commands in Reactions."):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.custom_reactions = {}
        self.skull_targets = set()
        self.auto_react_targets = {}
        
        self.db_path = "reactions.db"
        self.setup_database()
        self.load_data()
        self.responses = {
            "kms": [
                "Do it, no balls",
                "stream your suicide pussy"
            ],
            "dont care": [
                "no one cares if u care bruh ",
                "bro said dont care 😭 man im hurt",
                "cool nigga",
                "'dont care + didnt ask + ratio' head ahh",
                "you should care tho",
                "bro really dont care fr",
                "damn bro aint care 😭"
            ],
            "type shit": [
                "type shit"
            ],
            "i literally made you": [
                "'i brought u into this world and i will take you out of it' head ass 😭"
            ],
            "where the fuck my blunt where the fuck my cup where the fuck my reefer": [
                "# HUH HUH HUH HUH HUH HUH, IM SMOKING ON KUSH, HUH HUH HUH HUH HUH HUH, IM SMOKING ON KUSH"
            ],
            "what is heresy": [
                "heresy is the act of holding or promoting beliefs or opinions that go against the established doctrines of a religious, social, or political system, particularly within the context of religion. Historically, it often referred to deviations from the teachings of a dominant church or faith; The 6th Circle of Dante's Inferno."
            ],
            "band for band": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "ur poor": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "pooron": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "harm u": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "show funds": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "harm you": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "im in extorting com": [
                "https://cdn.discordapp.com/attachments/1302445192762359900/1302459603266699314/com_kid_bingo.gif?ex=672ccec7&is=672b7d47&hm=f1a89f9ae4669cfb7d36b86927067e332a95d7a91a1fbde3bfd376b33b55b7ae&"
            ],
            "stop fighting": [
                "https://cdn.discordapp.com/attachments/1087100819066867762/1264261435819687956/togif.gif?ex=672cee37&is=672b9cb7&hm=44f9bdf35ed1309ee27529e038a33d0452afb87d9a9490d84631a0526d7a72f6&"
            ],
            "thug shake": [
                "https://cdn.discordapp.com/attachments/1274808994149433445/1274821393829199952/heist.gif?ex=672fc071&is=672e6ef1&hm=6ecbfb2d8a5e73b0fbaadd6d8b87a684c0dab3d6cc1152beb71280882ed155ca&"
            ],
            "i keep a baby glock i aint fightin w no random, period 😭✌️": [
                "i keep a baby glock i aint fightin w no random, period 😭✌️"
            ],
            "get back to work": [
                "Slavery is the practice of owning another person as property, usually for their labor. People who are enslaved are called slaves or enslaved people. They are treated as property with few or no rights, and are often forced to work",
                "this isn't the fucking 18th century, fym get back to work"
            ],
            "playlist:suicideboys": [
                "https://open.spotify.com/playlist/3jz2V2ezNScj1pr1zceA9V?si=1d311c717c6c42b6"
            ],
            ",snipe": [
                "I don't wanna be a rapper..."
            ],
            "WIPF": [
                "Playfair is currently taking a break, not sure how long since I am just a bot, and he coded me to say this, aw shit I may as well just say it, I'm taking a break for a little bit, nothing happened, there is no tragic reason or anything bad that caused this, I'm just sleep deprived and admitible a bit depressed maybe, i have no idea if i am for sure but my mom told me ive been giving signs of being depressed, (lack of eating, lack of sleep, not very active or energetic), i mean shit on 11/29 i stayed in bed from waking up at 12 al the way to 5pm, got up at 5:30ish and walked my dog, took her inside and stayed outside for an hour, I'm perfectly fine, i am just tired and not very motivated"
            ],
            "im gonna deprecate": [
                "ah nah bro wanna get rid of features instead of adding them 😭🙏"
            ],
            "what happened to heresy": [
                "heresy is currently offline, in replacement, heresy is running heresy's code to ensure the bot still functions, meanwhile, heresy is getting a new Src."
            ],
            "Not me dude lol whats happening lol I hate this lol": [
                "Not me dude lol whats happening lol I hate this lol"
            ],
            "fuck you heresy": [
                "why is bro sayin fuck you to a bot",
                "what did i do"
            ], 
            "im playfairs": [
                "no your not."
            ],
            "im playfair": [
                "no your not."
            ],
            "i am playfair": [
                "no your not."
            ],
            "i am playfairs": [
                "no your not."
            ],
            "shit type": [
                "oh ok"
            ],
            "yoy": [
                "yoy"
            ],
            "zip it nigga": [
                "https://media.discordapp.net/attachments/1063022232378552350/1170779048214024243/ezgif.com-gif-maker.gif?ex=67c0a2f5&is=67bf5175&hm=d96d6cd1e101e1718f25a9d9aae0f27690594da9fe0dab0e3becfb75e562b783&"
            ],
            "kys": [
                "hey be nice!"
            ],
            "nigger": [
                "hey you can't say that!",
                "hey thats a no no word",
                "bad kitten we don't say those words herey!"
            ],
            "yesn't": [
                "which one is it you fucking nigger",
                "make up ur mind u albino faggot",
                "u albino faggot is it yes or no"
            ],
            "yesnt": [
                "which one is it you fucking nigger",
                "make up ur mind u albino faggot",
                "u albino faggot is it yes or no"
            ],
            "oh yea": [
                "https://tenor.com/view/oh-yeah-oh-yeah-gif-oh-yeah-meme-kool-aid-kool-aid-man-gif-18211119326397565445"
            ],
            "im cold": [
                "https://playfairs.cc/images/mommy.png"
            ]
        }

        self.conversation_context = {}

        self.bot_responders = {}

        print("Responses Initialized:", self.bot_responders)

    async def add_response(self, ctx, args):
        """Add a new autoresponse."""
        if ',' in args:
            keyword, response = map(str.strip, args.split(',', 1))
            if keyword and response:
                guild_id = ctx.guild.id
                if guild_id not in self.responses:
                    self.responses[guild_id] = {}
                self.responses[guild_id][keyword.lower()] = response
                
                embed = discord.Embed(
                    title="Autoresponse Added",
                    description=f"Keyword: `{keyword}`\nResponse: `{response}`",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await self.send_error(ctx, "Keyword and response cannot be empty.")
        else:
            await self.send_error(ctx, "Invalid syntax. Usage: `,autoresponder add <keyword> <response>`.")

    async def remove_response(self, ctx, args):
        """Remove an autoresponse."""
        keyword = args.strip()
        guild_id = ctx.guild.id
        
        if guild_id in self.responses and keyword in self.responses[guild_id]:
            del self.responses[guild_id][keyword]
            embed = discord.Embed(
                title="Autoresponse Removed",
                description=f"Keyword: `{keyword}` has been removed.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            await self.send_error(ctx, f"No autoresponse found for keyword: `{keyword}`.")

    async def send_error(self, ctx, message):
        """Send an error message in an embed."""
        embed = discord.Embed(
            title="Error",
            description=message,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    async def send_help(self, ctx):
        """Send help information for the autoresponder command."""
        embed = discord.Embed(
            title="Autoresponder Help",
            description="Manage autoresponses for your server.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Add Response",
            value="Usage: `,autoresponder add <keyword> <response>`",
            inline=False
        )
        embed.add_field(
            name="Remove Response",
            value="Usage: `,autoresponder remove <keyword>`",
            inline=False
        )
        embed.add_field(
            name="Permissions",
            value="Administrator",
            inline=False
        )
        await ctx.send(embed=embed)

    def setup_database(self):
        """Initialize the SQLite database for reactions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS skull_targets (
                        user_id INTEGER PRIMARY KEY
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auto_react_targets (
                        user_id INTEGER,
                        emoji TEXT,
                        PRIMARY KEY (user_id, emoji)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS custom_reactions (
                        trigger TEXT PRIMARY KEY,
                        reaction TEXT
                    )
                ''')
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database setup error: {e}")

    def load_data(self):
        """Load reaction data from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT user_id FROM skull_targets')
                self.skull_targets = {row[0] for row in cursor.fetchall()}
                
                cursor.execute('SELECT user_id, emoji FROM auto_react_targets')
                self.auto_react_targets = {}
                for user_id, emoji in cursor.fetchall():
                    if user_id not in self.auto_react_targets:
                        self.auto_react_targets[user_id] = []
                    self.auto_react_targets[user_id].append(emoji)
                
                cursor.execute('SELECT trigger, reaction FROM custom_reactions')
                self.custom_reactions = dict(cursor.fetchall())
        except sqlite3.Error as e:
            print(f"Data loading error: {e}")
            self.skull_targets = set()
            self.auto_react_targets = {}
            self.custom_reactions = {}

    @commands.command()
    async def skull(self, ctx: commands.Context, user: discord.Member):
        """Toggles the skull reaction targeting for a user."""
        if user.id in self.skull_targets:
            self.skull_targets.remove(user.id)
            embed = discord.Embed(
                title="Skull Reaction Target Removed",
                description=f"{user.mention} will no longer receive a 💀 reaction.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM skull_targets WHERE user_id = ?', (user.id,))
            conn.commit()
            conn.close()
        else:
            self.skull_targets.add(user.id)
            embed = discord.Embed(
                title="Skull Reaction Targeted",
                description=f"{user.mention} will receive a 💀 reaction whenever they send a message.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO skull_targets (user_id) VALUES (?)', (user.id,))
            conn.commit()
            conn.close()

    @commands.command()
    async def skullreset(self, ctx: commands.Context):
        """Resets all users targeted by the skull command."""
        self.skull_targets.clear()
        
        embed = discord.Embed(
            title="Skull Targets Reset",
            description="All skull targets have been reset.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM skull_targets')
        conn.commit()
        conn.close()

    @commands.command(name= "ar", aliases= ["autoreactor, autoreaction, reactions"])
    async def autoreact(self, ctx: commands.Context, user: discord.Member, *emojis):
        """Sets up auto-react for a specified user with given emojis."""
        if user.id not in self.auto_react_targets:
            self.auto_react_targets[user.id] = []

        self.auto_react_targets[user.id].extend(emojis)
        
        embed = discord.Embed(
            title="Auto-Reaction Set",
            description=f"{user.mention} will receive reactions: {', '.join(emojis)}",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        await ctx.send(embed=embed)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO auto_react_targets (user_id, emoji) VALUES (?, ?)', (user.id, ",".join(self.auto_react_targets[user.id])))
        conn.commit()
        conn.close()

    @commands.command(name="arreset", aliases= ["reactionsreset, removereactions, reactionsremove"])
    async def auto_react_reset(self, ctx: commands.Context):
        """Resets all auto-react settings."""
        self.auto_react_targets.clear()
        
        embed = discord.Embed(
            title="Auto-Reactions Reset",
            description="All auto-reaction settings have been reset.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM auto_react_targets')
        conn.commit()
        conn.close()

    @commands.group(name="reaction", invoke_without_command=True)
    async def reaction(self, ctx: commands.Context):
        """Base command for custom reactions."""
        await ctx.send("Available subcommands: `add`, `remove`, `reset`")

    @reaction.command(name="add")
    async def custom_word_add(self, ctx: commands.Context, word: str, emoji: str):
        """Adds a custom word for auto-reaction."""
        word_lower = word.lower()
        self.custom_reactions[word_lower] = emoji
        
        embed = discord.Embed(
            title="Custom Reaction Added",
            description=f"Now reacting to '{word}' with {emoji}",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO custom_reactions (word, emoji) VALUES (?, ?)', (word_lower, emoji))
            conn.commit()
        except Exception as e:
            print(f"Error saving to database: {e}")
        finally:
            conn.close()

    @reaction.command(name="remove")
    async def custom_word_remove(self, ctx: commands.Context, word: str):
        """Removes a custom word for auto-reaction."""
        word_lower = word.lower()
        if word_lower in self.custom_reactions:
            del self.custom_reactions[word_lower]
            embed = discord.Embed(
                title="Custom Reaction Removed",
                description=f"Removed reaction for the word '{word}'.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('DELETE FROM custom_reactions WHERE word = ?', (word_lower,))
                conn.commit()
            except Exception as e:
                print(f"Error removing from database: {e}")
            finally:
                conn.close()
        else:
            embed = discord.Embed(
                title="Word Not Found",
                description=f"There is no custom reaction for '{word}'.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @reaction.command(name="reset")
    async def custom_word_reset(self, ctx: commands.Context):
        """Resets all custom keyword reactions."""
        self.custom_reactions.clear()
        
        embed = discord.Embed(
            title="Custom Reactions Reset",
            description="All custom keyword reactions have been reset.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM custom_reactions')
        conn.commit()
        conn.close()

    @commands.command(name="autoresponder")
    @commands.has_permissions(administrator=True)
    async def autoresponder(self, ctx: commands.Context, action: str, *, args: str):
        """Main command for managing autoresponses."""
        if action.lower() == "add":
            await self.add_response(ctx, args)
        elif action.lower() == "remove":
            await self.remove_response(ctx, args)
        else:
            await self.send_help(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle automatic reactions and responses"""
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()

        try:
            if message.author.id in self.skull_targets:
                await message.add_reaction("💀")

            if "sob" in content or "😭" in content:
                await message.add_reaction("😭")

            if "ochra" in content or "1317632496636002344" in content:
                await message.add_reaction("<:pov_ochra:1317632496636002344>")

            if "hershey" in content or "1317632496636002344" in content:
                await message.add_reaction("<:pov_ochra:1317632496636002344>")

            if "heresy" in content or "1291967026788831232" in content:
                await message.add_reaction("<:heresyicon:1338845590033006744>")

            if "nova" in content or "1320964930387709973" in content:
                await message.add_reaction("<:nova:1320964930387709973>")

            if "playfair" in content or "1276099010779942954" in content:
                await message.add_reaction("<:playfair:1276099010779942954>")

            if "nigger" in content:
                await message.add_reaction("💀")

            if "kys" in content or "kill yourself" in content:
                await message.add_reaction("💀")

            for trigger, reaction in self.custom_reactions.items():
                if trigger.lower() in content:
                    await message.add_reaction(reaction)

            if message.author.id in self.auto_react_targets:
                for emoji in self.auto_react_targets[message.author.id]:
                    await message.add_reaction(emoji)
        except discord.HTTPException:
            pass

        for trigger, responses in self.responses.items():
            trigger_lower = trigger.lower()
            

            if trigger_lower in content:
                try:

                    response = random.choice(responses)
                    
                    await message.reply(response)
                except Exception as e:
                    print(f"Error sending response for trigger {trigger}: {e}")
                break

        for trigger, secondary_responses in getattr(self, 'secondary_responses', {}).items():
            trigger_lower = trigger.lower()

            if trigger_lower in content:
                try:
                    secondary_response = random.choice(secondary_responses)
                    
                    await message.reply(secondary_response)
                except Exception as e:
                    print(f"Error sending secondary response for trigger {trigger}: {e}")
                break

        if message.author.id == 1252011606687350805 or message.author.id == 1265662059056463976 and message.content == 'hwlp':  
            await message.reply("<@1252011606687350805> https://www.grammarly.com")  
            print(f"Response sent for hwlp from user {message.author.id}")  

        if message.author.id == 854145272749490216 and message.content == 'grr':  
            await message.channel.send("hi <@854145272749490216>")  
            print(f"Response sent for hello from user {message.author.id}")

        if message.author.id == 757355424621133914 and message.content == 'guess what':
            await message.channel.send("chicken butt")
            print(f"Response sent for guess what from user {message.author.id}")

        if message.author.id == 757355424621133914 and message.content == 'pocket pussy':
            await message.channel.send("stfu lina")
            print(f"Response sent for pocket pussy from user {message.author.id}")
            
        if message.author.id == self.bot.user.id and message.content == 'failed to fetch that post!':
            await message.channel.send("this is why I'm better <@1203514684326805524>")
            print(f"Response sent for failed to fetch that post! from user {message.author.id}")

    @commands.Cog.listener()
    async def sob_skull(self, message):
        """Listens for specific keywords and reacts accordingly."""
        if message.author == self.bot.user:
            return

        if message.author.id in self.skull_targets:
            await message.add_reaction("💀")
        elif "sob" in message.content.lower():
            await message.add_reaction("😭")
        elif message.content.lower() in self.custom_reactions:
            await message.add_reaction(self.custom_reactions[message.content.lower()])
        
        if message.author.id in self.auto_react_targets:
            for emoji in self.auto_react_targets[message.author.id]:
                await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def mp3(self, message):
        """Listens for specific phrases in messages and sends an MP3 file."""
        if message.author.bot:
            return

        trigger_phrases = ["nobody cares", "no one cares", "idc"]

        if any(phrase in message.content.lower() for phrase in trigger_phrases):
            file_path = "/root/heresy/Assets/MP3/nobody cares nig"

            await message.channel.send(
                file=discord.File(file_path, filename="VoiceMessage.mp3"),
                content="",
            )

    @commands.command(name="fox")
    async def fox(self, ctx):
        """Shows a fox gif"""
        embed = discord.Embed(color=discord.Color.orange())
        embed.set_image(url="https://playfairs.cc/images/fox.gif")
        await ctx.send(embed=embed)

    @commands.command(name="mouse")
    async def mouse(self, ctx):
        """Shows a mouse gif"""
        embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 255))
        embed.set_image(url="https://playfairs.cc/images/mouse.gif")
        await ctx.send(embed=embed)

    def add_bot_responder(self, triggers, responses):
        """
        Add a bot-specific responder.
        
        :param triggers: List of trigger phrases
        :param responses: List of possible responses
        """
        self.bot_responders[len(self.bot_responders)] = {
            'triggers': triggers,
            'responses': responses
        }

    def remove_bot_responder(self, index):
        """
        Remove a bot-specific responder.
        
        :param index: Index of the responder to remove
        """
        if index in self.bot_responders:
            del self.bot_responders[index]
