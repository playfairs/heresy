import os
import re
import random
import asyncio
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Cog, Context, command
import json
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import aiohttp
import random
from database import db_manager

from discord import app_commands
from discord.app_commands import Choice
from main import flesh

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

MERRIAM_WEBSTER_API_KEY = (
    os.getenv("MERRIAM_WEBSTER_API_KEY") or "32b24f5f-8518-4520-9225-b6ce2d9f728a"
)


class Fun(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.owner_id = 785042666475225109
        self.mirrored_user = None
        self.mirror_webhook = None
        self.lorebooks_dir = "Lorebooks"
        self.initialize_lorebooks_dir()
        self.confession_channel = None

    def initialize_lorebooks_dir(self):
        """Ensure the 'Lorebooks' folder exists."""
        if not os.path.exists(self.lorebooks_dir):
            os.makedirs(self.lorebooks_dir)
            print("[Lore] Created 'Lorebooks' directory.")

    async def get_avatar_from_url(self, url):
        """Fetch avatar bytes from a given URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(
                        f"Failed to fetch avatar. Status code: {response.status}"
                    )

    async def create_mirror_webhook(self, ctx):
        """Create a webhook in the current channel for mirroring."""
        try:
            # Delete existing webhook if it exists
            if self.mirror_webhook:
                try:
                    await self.mirror_webhook.delete()
                except:
                    pass

            # Create a new webhook
            self.mirror_webhook = await ctx.channel.create_webhook(
                name="Mirror Webhook"
            )
            return True
        except discord.Forbidden:
            await ctx.send(
                "I don't have permission to create a webhook in this channel."
            )
            return False
        except Exception as e:
            await ctx.send(f"Failed to create webhook: {e}")
            return False

    @commands.command(name="THE_EVIL_THAT_MEN_DO")
    async def the_evil_that_men_do(self, ctx: commands.Context):
        """
        A completely useless command that displays a specific phrase.
        """
        embed = discord.Embed(
            description=(
                "**Who the fuck said ruby done lost his touch?**\n\n"
                "[Listen on Spotify](https://open.spotify.com/track/5diz02QLFSmDur9R9M6bcD?si=2a4b70a6d4a241e3)"
            ),
            color=discord.Color.red(),
        )
        embed.set_footer(text="THE_EVIL_THAT_MEN_DO")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="mirror")
    async def mirror_user(self, ctx: commands.Context, user: discord.Member):
        # Create webhook first
        webhook_created = await self.create_mirror_webhook(ctx)
        if not webhook_created:
            return

        # Set the mirrored user
        self.mirrored_user = user

        # Try to get user's avatar
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.display_avatar.url)) as response:
                    if response.status == 200:
                        avatar_bytes = await response.read()
                        await self.mirror_webhook.edit(
                            name=user.display_name, avatar=avatar_bytes
                        )
                    else:
                        await self.mirror_webhook.edit(name=user.display_name)
        except Exception as e:
            await ctx.send(f"Could not set webhook avatar: {e}")
            await self.mirror_webhook.edit(name=user.display_name)

        await ctx.send(f"Now mirroring {user.mention} using a webhook!")

    @commands.command(name="stopmirror")
    async def stop_mirror(self, ctx: commands.Context):
        if self.mirrored_user:
            # Delete the webhook
            if self.mirror_webhook:
                try:
                    await self.mirror_webhook.delete()
                except:
                    pass

            await ctx.send(f"Stopped mirroring {self.mirrored_user.mention}.")
            self.mirrored_user = None
            self.mirror_webhook = None
        else:
            await ctx.send("No user is currently being mirrored.")

    @commands.command(
        name="urban", help="Fetches the definition of a word from Urban Dictionary."
    )
    async def urban(self, ctx, *, word: str):
        url = f"https://api.urbandictionary.com/v0/define?term={word}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data["list"]:
                definition_data = data["list"][0]
                word = definition_data["word"]
                definition = definition_data["definition"]
                example = definition_data.get("example", "No example available.")

                embed = discord.Embed(
                    title=f"Urban Dictionary: {word}", color=discord.Color.blue()
                )
                embed.add_field(name="Definition", value=definition, inline=False)
                embed.add_field(name="Example", value=example, inline=False)
                embed.set_footer(text="Provided by Urban Dictionary")

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No definitions found for **{word}**.")
        else:
            await ctx.send(
                "Failed to fetch data from Urban Dictionary. Please try again later."
            )

    @commands.command(
        name="define", help="Fetches the definition of a word from Merriam-Webster."
    )
    async def dictionary(self, ctx, *, word: str):
        if not MERRIAM_WEBSTER_API_KEY:
            await ctx.send("The API key is not set.")
            return

        api_url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={MERRIAM_WEBSTER_API_KEY}"
        response = requests.get(api_url)

        if response.status_code != 200:
            await ctx.send(
                "Sorry, I couldn't fetch the definition at the moment. Please try again later."
            )
            return

        data = response.json()

        if not data or isinstance(data[0], str):
            await ctx.send(f"No definition found for **{word}**.")
            return

        definition_data = data[0]
        word_definition = definition_data.get("shortdef", ["No definition available."])[
            0
        ]
        part_of_speech = definition_data.get("fl", "Unknown")

        embed = discord.Embed(title=f"Definition of {word}", color=discord.Color.blue())
        embed.add_field(name="Word", value=word, inline=False)
        embed.add_field(name="Part of Speech", value=part_of_speech, inline=True)
        embed.add_field(name="Definition", value=word_definition, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="shame")
    async def shame(self, ctx, user: discord.Member = None):
        """
        Publicly shame a user with a humorous message.
        """
        if not user:
            user = ctx.author

        # List of shaming messages
        shame_messages = [
            f"{user.mention} has been publicly shamed for their questionable life choices!",
            f"Everyone point and laugh at {user.mention}!",
            f"{user.mention} is now experiencing the ultimate embarrassment!",
            f"Shame! Shame! Shame! 🔔 {user.mention}",
        ]

        # Select a random shaming message
        shame_message = random.choice(shame_messages)

        # Send the shaming message
        await ctx.send(shame_message)

    def translate_text(self, text, language="lolcat"):
        """Translate text to a fun language"""
        try:
            import pytranslate

            # Supported languages: lolcat, pirate, shakespeare, chef
            translators = {
                "lolcat": pytranslate.lolcat,
                "pirate": pytranslate.pirate,
                "shakespeare": pytranslate.shakespeare,
                "chef": pytranslate.chef,
            }

            if language not in translators:
                language = "lolcat"  # default to lolcat

            return translators[language](text)
        except ImportError:
            # Fallback to simple uwu-style translation if library is not available
            replacements = {
                "l": "w",
                "r": "w",
                "Love": "Wuv",
                "love": "wuv",
                "hello": "hewwo",
                "Hello": "Hewwo",
                "hi": "hai",
                "Hi": "Hai",
            }

            for old, new in replacements.items():
                text = text.replace(old, new)

            return text + " uwu"

    @commands.group(name="uwu", invoke_without_command=True)
    async def uwu_group(self, ctx, *, text: str = None):
        """UwU command group"""
        # Only allow the bot owner to use this command
        if ctx.author.id != self.owner_id:
            await ctx.send("Only the bot owner can use this command.")
            return

        # If no subcommand and no text, show help embed
        if not text:
            embed = discord.Embed(
                title="Language Translation Commands",
                description=(
                    "**Available Subcommands:**\n"
                    "- `uwulock <user> [language]`: Lock a user's messages\n"
                    "- `uwureset [user]`: Reset translation locks\n\n"
                    "**Available Languages:**\n"
                    "- lolcat\n- uwu\n- pirate"
                ),
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            return

        # If text is provided, translate it
        translated = self.translate_text(text, "uwu")
        await ctx.send(translated)

    @commands.command(name="uwulock")
    async def uwu_lock(self, ctx, member: discord.Member, language: str = "lolcat"):
        """Lock a user's messages and translate them"""
        # Only allow the bot owner to use this command
        if ctx.author.id != self.owner_id:
            await ctx.send("Only the bot owner can use this command.")
            return

        # Validate language
        valid_languages = ["lolcat", "pirate", "shakespeare", "chef"]
        if language.lower() not in valid_languages:
            await ctx.send(
                f"Invalid language. Choose from: {', '.join(valid_languages)}"
            )
            return

        # Perform the lock
        if not hasattr(self.bot, "uwu_locks"):
            self.bot.uwu_locks = {}

        self.bot.uwu_locks[member.id] = {
            "language": language.lower(),
            "channel_id": ctx.channel.id,
        }
        await ctx.send(f"Locked {member.mention}'s messages in {language} mode.")

    @commands.command(name="uwureset")
    async def uwu_reset(self, ctx, member: discord.Member = None):
        """Reset translation lock for a user or all users"""
        # Only allow the bot owner to use this command
        if ctx.author.id != self.owner_id:
            await ctx.send("Only the bot owner can use this command.")
            return

        # If no member specified, clear all locks
        if not member:
            if hasattr(self.bot, "uwu_locks"):
                self.bot.uwu_locks.clear()
            await ctx.send("All translation locks have been reset!")
            return

        # Remove specific user's lock
        if hasattr(self.bot, "uwu_locks") and member.id in self.bot.uwu_locks:
            del self.bot.uwu_locks[member.id]
            await ctx.send(f"Translation lock for {member.mention} has been reset!")
        else:
            await ctx.send(
                f"{member.mention} does not have an active translation lock."
            )

    @commands.command(name="f")
    async def flip_table(self, ctx):
        """Flip a table and then apologize."""
        # Send the table flip embed
        flip_embed = discord.Embed(
            title="Table Flip! 😡",
            description="(╯°□°)╯︵ ┻━┻",
            color=discord.Color.red(),
        )

        # Send the first embed
        message = await ctx.send(embed=flip_embed)

        # Wait a moment
        await asyncio.sleep(2)

        # Create the apology embed
        apology_embed = discord.Embed(
            title="I'm Sorry, Table 😔",
            description="┬─┬ノ( º _ ºノ)",
            color=discord.Color.blue(),
        )

        # Edit the message with the apology embed
        await message.edit(embed=apology_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return

        # Check if user is translation locked
        if hasattr(self.bot, "uwu_locks") and message.author.id in self.bot.uwu_locks:
            # Get webhook info
            lock_info = self.bot.uwu_locks[message.author.id]

            try:
                # Delete original message
                await message.delete()

                # Create webhook client in the current channel
                async with aiohttp.ClientSession() as session:
                    # Fetch or create webhook for this specific channel
                    channel = message.channel
                    try:
                        webhooks = await channel.webhooks()
                        webhook = next(
                            (
                                w
                                for w in webhooks
                                if w.name.startswith(lock_info["language"].capitalize())
                            ),
                            None,
                        )

                        # If no webhook exists, create a new one
                        if not webhook:
                            webhook = await channel.create_webhook(
                                name=f"{lock_info['language'].capitalize()} Translation"
                            )
                    except discord.Forbidden:
                        # If can't fetch or create webhooks, remove the lock
                        del self.bot.uwu_locks[message.author.id]
                        return

                    # Translate the message
                    translated_content = self.translate_text(
                        message.content, lock_info.get("language", "lolcat")
                    )

                    # Send via webhook
                    await webhook.send(
                        translated_content,
                        username=f"{lock_info['language'].capitalize()} {message.author.name}",
                        avatar_url=message.author.display_avatar.url,
                    )
            except (discord.Forbidden, discord.NotFound):
                # Remove lock if webhook or permissions fail
                del self.bot.uwu_locks[message.author.id]

    @commands.command(name="tame")
    async def tame(self, ctx):
        """Attempts to tame a Diplodoculus."""
        outcomes = [
            "Diplodoculus looks at you suspiciously and runs away. You fail to tame it.",
            "You offer Diplodoculus some food, and it considers your offer. It's a draw!",
            "Diplodoculus playfully lets you ride on its back. You win and tame it!",
            "Diplodoculus is too wild and escapes into the forest. You lose!",
            "Diplodoculus challenges you to a dance-off, and you impress it! You win!",
            "A meteor distracts Diplodoculus. It's a draw!",
            "Diplodoculus gives you a leaf as a token of friendship. You win!",
            "Diplodoculus accidentally steps on your shoe. You lose!",
            "Diplodoculus challenges you to a staring contest. It's a draw!",
            "Diplodoculus roars loudly, scaring you away. You lose!",
            "You manage to outwit Diplodoculus with a clever trap. You win!",
            "Diplodoculus whips its tail and creates a gust of wind. It's a draw!",
            "Diplodoculus finds you amusing and decides to spare you. You win!",
            "Diplodoculus gets tired halfway through the battle. It's a draw!",
            "Diplodoculus does a silly dance, and you can't stop laughing. You lose!",
            "Diplodoculus teaches you a secret dinosaur technique. You win!",
            "Diplodoculus accidentally trips over a rock. It's a draw!",
            "You offer Diplodoculus a snack, and it decides not to fight. You win!",
            "Diplodoculus roars, but it sounds more like a funny squeak. You laugh. It's a draw!",
            "Diplodoculus starts eating leaves mid-battle. You awkwardly leave. It's a draw!",
            "Diplodoculus puts something silly inside of you. You win!",
            "You put something silly inside Diplodoculus. Its a draw.",
            "Diplodoculus puts something silly inside of the tree. You lose! :(",
            "Diplodoculus learns how to rollerskate and trips you, now you have bruises all over your knees. You lose!",
            "Diplodoculus slaps the fuck out of you! You lose!",
            "Diplodoculus slaps your ass but it turns you on! Its a draw!",
        ]

        outcome = random.choice(outcomes)

        # Check if the user successfully tamed the Diplodoculus
        if "You win" in outcome:
            db_manager.add_dino(ctx.author.id)
            embed_color = discord.Color.green()
        elif "It's a draw" in outcome:
            embed_color = discord.Color.yellow()
        else:
            embed_color = discord.Color.red()

        # Display outcome and add XP
        xp_reward = 10 if "win" in outcome else 5 if "draw" in outcome else 0
        new_xp, new_level = db_manager.add_xp(ctx.author.id, xp_reward)

        embed = discord.Embed(
            title="Tame Diplodoculus", description=outcome, color=embed_color
        )
        embed.add_field(name="XP Earned", value=f"{xp_reward} XP", inline=True)
        embed.add_field(name="Current Level", value=new_level, inline=True)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="summon")
    async def summon(self, ctx):
        """Summons Diplodoculus if the user owns one."""
        user_dino = db_manager.get_dino(ctx.author.id)

        if not user_dino:
            await ctx.send("You don't own a Diplodoculus, try to tame one first!")
            return

        summon_outcomes = [
            "Diplodoculus majestically appears, its long neck swaying gracefully.",
            "Diplodoculus stomps the ground and lets out a mighty roar!",
            "Diplodoculus emerges from the forest, carrying a bundle of leaves.",
            "Diplodoculus appears with a playful demeanor, ready for fun.",
            "Diplodoculus charges in dramatically, scattering the nearby grass.",
            "Diplodoculus gracefully swims through a nearby river to meet you.",
            "Diplodoculus winks at you and strikes a heroic pose.",
            "Diplodoculus appears with an entourage of smaller dinos.",
            "Diplodoculus munches on leaves while greeting you with a gentle nudge.",
            "Diplodoculus stands tall, blocking the sun, casting a mighty shadow.",
        ]

        outcome = random.choice(summon_outcomes)
        embed = discord.Embed(
            title=f"Summoning {user_dino.dino_name}",
            description=outcome,
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="name")
    async def name_dino(self, ctx, *, pet_name: str):
        """Names your Diplodocus."""
        user_dino = db_manager.get_dino(ctx.author.id)

        if not user_dino:
            await ctx.send("You don't own a Diplodoculus, try to tame one first!")
            return

        db_manager.add_dino(ctx.author.id, pet_name)
        await ctx.send(f"Your Diplodoculus is now named **{pet_name}**!")

    @commands.command(name="pets")
    async def pets(self, ctx):
        """Shows how many pets the user owns."""
        all_dinos = db_manager.get_all_dinos()
        pet_count = len(all_dinos)

        embed = discord.Embed(
            title="Pet Count",
            description=f"Total Diplodocus(es) owned: {pet_count} 🦕",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="xp")
    async def xp(self, ctx, member: discord.Member = None):
        """Displays the user's XP and level."""
        # If no member is mentioned, default to the author
        member = member or ctx.author

        # Debug print to check the db_manager
        print(f"DB Manager: {db_manager}")
        print(f"DB Manager methods: {dir(db_manager)}")

        try:
            user_xp = db_manager.get_xp(member.id)

            # Explicitly call calculate_level
            user_level = getattr(db_manager, "calculate_level", lambda x: 0)(user_xp)

            embed = discord.Embed(
                title=f"{member.name}'s XP and Level", color=discord.Color.green()
            )
            embed.add_field(name="XP", value=user_xp, inline=True)
            embed.add_field(name="Level", value=user_level, inline=True)
            embed.set_thumbnail(url=member.avatar.url)
            await ctx.send(embed=embed)
        except Exception as e:
            # Catch and print any errors
            print(f"Error in XP command: {e}")
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="diplodraw")
    async def diplodraw(self, ctx):
        """Shares an ASCII art of Diplodoculus."""
        art = (
            "         🦕\n"
            "         Diplodoculus in its majestic glory!\n"
            "           \\       /            \n"
            "           ( o_o )\n"
            "           (     )\n"
            "           /     \\ "
        )
        await ctx.send(f"```{art}```")

    @commands.command(name="diplometer")
    async def diplodometer(self, ctx):
        """Rates how Diplodoculus-like the user is."""
        score = random.randint(1, 100)
        await ctx.send(f"{ctx.author.mention}, you are {score}% Diplodoculus!")

    @commands.command(name="1v1")
    async def one_v_one(self, ctx, opponent: discord.Member):
        """1v1 battle between two Diplodoculus owners."""
        if ctx.author == opponent:
            await ctx.send("You can't 1v1 yourself!")
            return

        user_dino = db_manager.get_dino(ctx.author.id)
        if not user_dino:
            await ctx.send("You don't own a Diplodoculus, try to tame one first!")
            return

        opponent_dino = db_manager.get_dino(opponent.id)
        if not opponent_dino:
            await ctx.send(f"{opponent.mention} doesn't own a Diplodoculus!")
            return

        battle_outcomes = [
            "Diplodoculus sneezes and knocks you over. You lose!",
            "You tame Diplodoculus and ride into the sunset. You win!",
            "Diplodoculus eats a tree instead of fighting. It's a draw.",
            "You throw a rock at Diplodoculus. It doesn't even notice. You lose!",
            "Diplodoculus learns kung fu and defeats you easily. You lose!",
            "A meteor distracts Diplodoculus. It's a draw!",
            "Diplodoculus gives you a leaf as a token of friendship. You win!",
            "Diplodoculus accidentally steps on your shoe. You lose!",
            "Diplodoculus challenges you to a staring contest. It's a draw!",
            "Diplodoculus roars loudly, scaring you away. You lose!",
            "You manage to outwit Diplodoculus with a clever trap. You win!",
            "Diplodoculus whips its tail and creates a gust of wind. It's a draw!",
            "Diplodoculus finds you amusing and decides to spare you. You win!",
            "Diplodoculus gets tired halfway through the battle. It's a draw!",
            "Diplodoculus does a silly dance, and you can't stop laughing. You lose!",
            "Diplodoculus teaches you a secret dinosaur technique. You win!",
            "Diplodoculus accidentally trips over a rock. It's a draw!",
            "You offer Diplodoculus a snack, and it decides not to fight. You win!",
            "Diplodoculus roars, but it sounds more like a funny squeak. You laugh. It's a draw!",
            "Diplodoculus starts eating leaves mid-battle. You awkwardly leave. It's a draw!",
            "Diplodoculus puts something silly inside of you. You win!",
            "You put something silly inside Diplodoculus. Its a draw.",
            "Diplodoculus puts something silly inside of the tree. You lose! :(",
            "Diplodoculus learns how to rollerskate and trips you, now you have bruises all over your knees. You lose!",
            "Diplodoculus slaps the fuck out of you! You lose!",
            "Diplodoculus slaps your ass but it turns you on! Its a draw!",
        ]

        outcome = random.choice(battle_outcomes)

        # Determine XP rewards based on outcome
        if "You win" in outcome:
            winner_xp = 50
            loser_xp = 10
            winner = ctx.author
            loser = opponent
        elif "You lose" in outcome:
            winner_xp = 50
            loser_xp = 10
            winner = opponent
            loser = ctx.author
        else:  # Draw
            winner_xp = 25
            loser_xp = 25
            winner = None
            loser = None

        # Add XP to participants
        if winner:
            db_manager.add_xp(winner.id, winner_xp)
        if loser:
            db_manager.add_xp(loser.id, loser_xp)

        # Create embed with battle outcome
        embed = discord.Embed(
            title="🦕 Diplodoculus Battle 🦕",
            description=outcome,
            color=discord.Color.random(),
        )

        # Add XP information to embed
        if winner:
            embed.add_field(
                name="Battle Results",
                value=f"{winner.mention} wins and gains {winner_xp} XP!\n{loser.mention} loses and gains {loser_xp} XP.",
                inline=False,
            )
        else:
            embed.add_field(
                name="Battle Results",
                value=f"It's a draw! Both participants gain {winner_xp} XP.",
                inline=False,
            )

        # Add participants' Diplodoculus names
        embed.add_field(
            name="Combatants",
            value=f"{ctx.author.mention}'s {user_dino.dino_name} vs {opponent.mention}'s {opponent_dino.dino_name}",
            inline=False,
        )

        await ctx.send(embed=embed)

    def load_outcomes(self):
        """Load battle outcomes from JSON file."""
        outcomes_file = "./json/battle_outcomes.json"
        try:
            with open(outcomes_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    @commands.command(name="battle")
    async def battle(self, ctx):
        """Starts a battle with Diplodoculus."""
        outcomes = self.load_outcomes()
        if not outcomes:
            await ctx.send(
                "No battle outcomes available! Please add some using the `add-outcome` command."
            )
            return

        outcome = random.choice(outcomes)

        # Add XP based on outcome
        if "You win" in outcome:
            db_manager.add_xp(ctx.author.id, 10)  # Award 10 XP for wins
            embed_color = discord.Color.green()
        elif "You lose" in outcome:
            db_manager.add_xp(ctx.author.id, 5)  # Award 5 XP for losses
            embed_color = discord.Color.red()
        else:
            db_manager.add_xp(ctx.author.id, 2)  # Award 2 XP for draws
            embed_color = discord.Color.yellow()

        embed = discord.Embed(
            title="Battle Outcome", description=outcome, color=embed_color
        )
        embed.add_field(
            name="XP Earned",
            value=f"{'10 XP' if 'win' in outcome else '5 XP' if 'lose' in outcome else '2 XP'}",
            inline=True,
        )
        embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="add-outcome")
    async def add_battle_outcome(self, ctx, *, outcome: str):
        """Add a new battle outcome to the JSON file."""
        outcomes_file = "./json/battle_outcomes.json"

        try:
            with open(outcomes_file, "r") as f:
                outcomes = json.load(f)
        except FileNotFoundError:
            outcomes = []

        # Check if outcome already exists
        if outcome in outcomes:
            await ctx.send("This outcome already exists!")
            return

        outcomes.append(outcome)

        with open(outcomes_file, "w") as f:
            json.dump(outcomes, f, indent=4)

        await ctx.send(f"Added new battle outcome: {outcome}")

    @commands.command(name="9/11")
    async def nine_eleven(self, ctx):
        """A somber emoji representation."""
        # First plane sequence
        first_plane_stages = [
            "✈️       🏢",
            " ✈️      🏢",
            "  ✈️     🏢",
            "   ✈️    🏢",
            "    ✈️   🏢",
            "     ✈️  🏢",
            "      ✈️ 🏢",
            "       ✈️🏢",
            "        💥",
        ]

        # Second plane sequence
        second_plane_stages = [
            "🏢       ✈️",
            "🏢      ✈️ ",
            "🏢     ✈️  ",
            "🏢    ✈️   ",
            "🏢   ✈️    ",
            "🏢  ✈️     ",
            "🏢 ✈️      ",
            "🏢✈️       ",
            "💥",
        ]

        # First plane animation
        message = await ctx.send(first_plane_stages[0])
        for stage in first_plane_stages[1:]:
            await asyncio.sleep(0.5)
            await message.edit(content=stage)

        await asyncio.sleep(1)

        # Second plane animation
        message = await ctx.send(second_plane_stages[0])
        for stage in second_plane_stages[1:]:
            await asyncio.sleep(0.5)
            await message.edit(content=stage)

        await asyncio.sleep(1)

        # Aftermath
        await message.edit(content="💨 🏢💥🏢")

        await asyncio.sleep(1)
        await message.edit(content="😔")

    @commands.group(name="bday", invoke_without_command=True)
    async def birthday(self, ctx, member: discord.Member = None):
        """Show a user's birthday and time until next birthday."""
        # If no member specified, use the command invoker
        member = member or ctx.author

        try:
            # Get birthday from database
            user_birthday = db_manager.get_birthday(member.id)

            if not user_birthday:
                await ctx.send(
                    f"{member.mention} hasn't set a birthday yet. Use `bday set` to set one!"
                )
                return

            # Calculate days until next birthday
            today = date.today()
            next_birthday = date(today.year, user_birthday.month, user_birthday.day)

            # If birthday has passed this year, set to next year
            if next_birthday < today:
                next_birthday = date(
                    today.year + 1, user_birthday.month, user_birthday.day
                )

            # Calculate time difference
            time_diff = relativedelta(next_birthday, today)

            # Create embed
            embed = discord.Embed(
                title=f"🎂 {member.name}'s Birthday", color=discord.Color.gold()
            )
            embed.add_field(
                name="Birthday", value=user_birthday.strftime("%B %d"), inline=False
            )

            # Format time until next birthday
            time_parts = []
            if time_diff.years > 0:
                time_parts.append(
                    f"{time_diff.years} year{'s' if time_diff.years > 1 else ''}"
                )
            if time_diff.months > 0:
                time_parts.append(
                    f"{time_diff.months} month{'s' if time_diff.months > 1 else ''}"
                )
            if time_diff.days > 0:
                time_parts.append(
                    f"{time_diff.days} day{'s' if time_diff.days > 1 else ''}"
                )

            time_str = (
                " and ".join(time_parts) if time_parts else "Today is your birthday!"
            )

            embed.add_field(name="Next Birthday", value=f"In {time_str}", inline=False)
            embed.set_thumbnail(url=member.avatar.url)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            # Additional debug print
            import traceback

            traceback.print_exc()

    @birthday.command(name="set")
    async def set_birthday(self, ctx, *, birthday_str: str):
        """Set your birthday. Format: YYYY-MM-DD or MM-DD"""
        try:
            # Try parsing with year first
            try:
                birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
            except ValueError:
                # If year parsing fails, assume current year
                try:
                    birthday = (
                        datetime.strptime(birthday_str, "%m-%d")
                        .date()
                        .replace(year=date.today().year)
                    )
                except ValueError:
                    await ctx.send(
                        "Invalid date format. Please use YYYY-MM-DD or MM-DD (e.g., 2000-05-15 or 05-15)."
                    )
                    return

            # Validate birthday
            if birthday.year < 1900 or birthday > date.today():
                await ctx.send("Please provide a valid birthday.")
                return

            # Save to database
            db_manager.set_birthday(ctx.author.id, birthday)

            embed = discord.Embed(
                title="🎂 Birthday Set",
                description=f"Your birthday has been set to {birthday.strftime('%B %d')}!",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            # Additional debug print
            import traceback

            traceback.print_exc()

    async def check_birthdays(self):
        """Background task to check and announce birthdays."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            try:
                today = date.today()
                birthdays = db_manager.get_all_birthdays()

                for birthday_entry in birthdays:
                    if (
                        birthday_entry.birthday.month == today.month
                        and birthday_entry.birthday.day == today.day
                    ):

                        # Find the user in the guild
                        user = await self.bot.fetch_user(int(birthday_entry.user_id))

                        # Find a general channel to announce
                        channel = self.bot.get_channel(self.bot.general_channel_id)
                        if channel:
                            await channel.send(
                                f"🎉 Happy birthday {user.mention}! 🎂🥳"
                            )

            except Exception as e:
                print(f"Error in birthday check: {e}")

            # Wait 24 hours before checking again
            await asyncio.sleep(86400)

    @commands.command(name="tism")
    async def tism(self, ctx):
        """A playful command celebrating neurodiversity."""
        tism_responses = [
            "*hyperfixates on an obscure topic for 3 hours*",
            "Did someone say DETAILED INFORMATION? 🧠",
            "I can recite every Pokémon in order. Want to hear? 📋",
            "*makes extremely precise observation about something no one asked about*",
            "My brain is like a computer with too many browser tabs open 💻",
            "Social cues? Never heard of them. 🤔",
            "*explains the entire history of toasters in excruciating detail*",
            "I don't have a short attention span, I have MULTIPLE attention spans! 🌈",
            "Sensory overload incoming in 3... 2... 1... 🚨",
            "My special interest today is EVERYTHING and NOTHING! 🌟",
            "*reorganizes something for maximum efficiency*",
            "Did you know the exact manufacturing date of this Discord server? I do! 📅",
            "Stimming is just my way of downloading updates 🤖",
            "Social interaction loading... please wait... **error**: **Failed to load Social Interaction: No such file or directory**",
            "Autism isn't a processing error, it's a FEATURE! 🧩",
        ]

        await ctx.send(random.choice(tism_responses))

    @commands.command(name="grr")
    async def grr(self, ctx):
        """Responds with a greeting."""
        await ctx.send("Hi ochra <:pov_ochra:1317632496636002344>")

    @commands.command(name="erection")
    async def errection(self, ctx):
        """Sends an embedded image of a stick."""
        embed = discord.Embed(title="Don't ask why this is a command.. blame vio.", color=discord.Color.gold())
        embed.set_image(url="https://c.tenor.com/U2y9ZVq5HSAAAAAd/tenor.gif")
        await ctx.send(embed=embed)

    @commands.command(name="fire")
    async def fire(self, ctx):
        """Responds with a specific message."""
        msg = await ctx.send("california.")
        await msg.add_reaction("🔥")

    @commands.command(name="ochra")
    async def ochra(self, ctx):
        """Responds with a specific message."""
        await ctx.send("<:pov_ochra:1317632496636002344>")

    @commands.group(name="confess", invoke_without_command=True)
    async def confess(self, ctx, *, message: str = None):
        if message is None:
            await ctx.send("Please provide a message to confess.")
        else:
            await ctx.message.delete()  # Delete the original message
            channel_id = 1334727473396584518
            channel = self.bot.get_channel(channel_id)
            if channel is not None:
                embed = discord.Embed(title=f"Anonymous Confession", description=message, color=discord.Color.blue())
                await channel.send(embed=embed)
            else:
                await ctx.send("Confession channel not found.")
