import discord
from discord.ext import commands
import os
import json
import hashlib

class LoreView(discord.ui.View):
    def __init__(self, lorebook, user):
        super().__init__()
        self.lorebook = lorebook
        self.user = user
        self.current_page = 0

    def get_embed(self):
        if not self.lorebook:
            return discord.Embed(description="No lore entries found.")
        
        entry = self.lorebook[self.current_page]
        embed = discord.Embed(
            title=f"{self.user.display_name}'s Lore",
            description=entry.get('content', 'No content'),
            color=0x000000
        )
        
        embed.set_footer(text=f"Entry {self.current_page + 1}/{len(self.lorebook)}")
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, emoji="<:left:1307448382326968330>")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="<:right:1307448399624405134>")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.lorebook) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed())

class Lore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lorebooks_dir = "Lorebooks"
        self.initialize_lorebooks_dir()

    def initialize_lorebooks_dir(self):
        """Ensure the 'Lorebooks' folder exists."""
        if not os.path.exists(self.lorebooks_dir):
            os.makedirs(self.lorebooks_dir)
            print("[Lore] Created 'Lorebooks' directory.")

    def get_lorebook_path(self, user_id):
        """Get the path to a user's lorebook JSON file."""
        return os.path.join(self.lorebooks_dir, f"{user_id}.json")

    def load_lorebook(self, user_id):
        """Load a user's lorebook, or return an empty list if none exists."""
        path = self.get_lorebook_path(user_id)
        if os.path.exists(path):
            with open(path, "r") as file:
                return json.load(file)
        return []

    def save_lorebook(self, user_id, lorebook):
        """Save a user's lorebook to their JSON file."""
        path = self.get_lorebook_path(user_id)
        with open(path, "w") as file:
            json.dump(lorebook, file, indent=4)

    def generate_entry_hash(self, content):
        """Generate a unique hash for a lore entry to detect duplicates."""
        return hashlib.md5(content.encode()).hexdigest()

    @commands.group(name="lore", invoke_without_command=True, aliases=['hoe'])
    async def lore(self, ctx, user: discord.Member = None):
        """
        Shows the lorebook for a user with pagination. 
        If no user is mentioned, shows the invoking user's lorebook.
        """
        # If no user is mentioned, use the command invoker
        user = user or ctx.author

        # Load the user's lorebook
        lorebook = self.load_lorebook(user.id)

        # Check if the lorebook is empty
        if not lorebook:
            await ctx.send(f"Congrats {user.mention}, you haven't been clipped yet..")
            return

        # Create a view with pagination
        view = LoreView(lorebook, user)
        
        # Send the first page
        await ctx.send(embed=view.get_embed(), view=view)

    @lore.command(name="add")
    async def add_lore(self, ctx):
        """
        Adds a message to the lorebook of the user who sent the referenced message.
        Must be used by replying to a message.
        """
        # Check if this is a reply
        if not ctx.message.reference:
            await ctx.send("You must reply to a message to add lore!")
            return

        # Get the referenced message
        referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        # Set the user to the author of the referenced message
        user = referenced_message.author
        content = referenced_message.content

        # Load the user's current lorebook
        lorebook = self.load_lorebook(user.id)

        # Generate hash to check for duplicates
        entry_hash = self.generate_entry_hash(content)
        
        # Check if this exact message has already been added
        if any(self.generate_entry_hash(entry.get('content', '')) == entry_hash for entry in lorebook):
            await ctx.send("This message has already been added to lorebook.")
            return

        # Add the new entry
        lorebook.append({
            'content': content,
            'timestamp': referenced_message.created_at.isoformat(),
            'original_author_id': referenced_message.author.id,
            'author_id': ctx.author.id,
            'channel_id': referenced_message.channel.id
        })

        # Save the updated lorebook
        self.save_lorebook(user.id, lorebook)

        await ctx.send(f"Lore added for {user.mention}!")

    @lore.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_lore(self, ctx, entry_number: int, user: discord.Member = None):
        """
        Removes a specific lore entry by its number.
        """
        # If no user is mentioned, use the command invoker
        if user is None:
            user = ctx.author

        # Load the user's lorebook
        lorebook = self.load_lorebook(user.id)

        # Check if the entry number is valid
        if entry_number < 1 or entry_number > len(lorebook):
            await ctx.send(f"Invalid entry number. Please choose a number between 1 and {len(lorebook)}.")
            return

        # Remove the entry (adjusting for 1-based indexing)
        removed_entry = lorebook.pop(entry_number - 1)

        # Save the updated lorebook
        self.save_lorebook(user.id, lorebook)

        await ctx.send(f"Removed entry {entry_number} from {user.mention}'s lorebook.")

    @lore.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_lore(self, ctx, user: discord.Member = None):
        """
        Resets a user's entire lorebook.
        """
        # If no user is mentioned, use the command invoker
        if user is None:
            user = ctx.author

        # Reset the lorebook to an empty list
        self.save_lorebook(user.id, [])

        await ctx.send(f"Reset {user.mention}'s lorebook.")

    @lore.command(name="show")
    async def show_lore(self, ctx, entry_number: int, user: discord.Member = None):
        """
        Shows a specific lore entry for a user.
        If no user is mentioned, uses the command invoker.
        If entry number is out of range, shows a random entry.
        """
        # If no user is mentioned, use the command invoker
        if user is None:
            user = ctx.author

        # Load the user's lorebook
        lorebook = self.load_lorebook(user.id)

        # Check if the lorebook is empty
        if not lorebook:
            await ctx.send(f"Congrats {user.mention}, you haven't been clipped yet..")
            return

        # If entry number is out of range, choose a random entry
        import random
        if entry_number < 1 or entry_number > len(lorebook):
            entry_number = random.randint(1, len(lorebook))
            await ctx.send(f"Invalid entry number. Showing a random entry instead!")

        entry = lorebook[entry_number - 1]

        # Create an embed to display the entry
        embed = discord.Embed(
            title=f"{user.display_name}'s Lore - Entry {entry_number}",
            description=entry.get('content', 'No content'),
            color=0x000000
        )
        
        await ctx.send(embed=embed)

    @lore.command(name="search", help="Search for lore entries containing a keyword")
    async def search_lore(self, ctx, *, query: str = None):
        """
        Search for lore entries containing a specific keyword.
        Optional: specify a user to search only their lorebook.
        Usage: 
        - ,lore search keyword
        - ,lore search keyword @user
        """
        # If no query provided, send an error message
        if not query:
            await ctx.send("Please provide a keyword to search for.")
            return

        # Try to extract a user mention from the query
        user = ctx.author  # Default to command invoker
        parts = query.split()
        
        # Check if the last part is a user mention
        if len(parts) > 1 and parts[-1].startswith('<@') and parts[-1].endswith('>'):
            try:
                # Remove the mention from the query
                query = ' '.join(parts[:-1])
                # Convert mention to user
                user = await commands.MemberConverter().convert(ctx, parts[-1])
            except commands.MemberNotFound:
                # If conversion fails, keep the full query and use default user
                query = ' '.join(parts)
        
        # Load the user's lorebook
        lorebook = self.load_lorebook(user.id)

        # Convert keyword to lowercase for case-insensitive search
        query = query.lower()

        # Find matching entries
        matching_entries = [
            (index + 1, entry) for index, entry in enumerate(lorebook) 
            if query in entry.get('content', '').lower()
        ]

        # If no matches found
        if not matching_entries:
            await ctx.send(f"No lore entries found containing '{query}' for {user.display_name}.")
            return

        # Create a paginated view for search results
        class SearchLoreView(discord.ui.View):
            def __init__(self, ctx, matching_entries, user, query):
                super().__init__()
                self.ctx = ctx
                self.matching_entries = matching_entries
                self.user = user
                self.query = query
                self.current_page = 0

            def get_embed(self):
                # Get the current entry
                entry_number, entry = self.matching_entries[self.current_page]

                # Create embed
                embed = discord.Embed(
                    title=f"{self.user.display_name}'s Lore - Search Results",
                    description=f"Searching for '{self.query}'\nShowing result {self.current_page + 1} of {len(self.matching_entries)}",
                    color=0x000000
                )

                # Add entry content
                embed.add_field(name=f"Entry {entry_number}", value=entry.get('content', 'No content'), inline=False)
                
                return embed

            def update_buttons(self):
                # Disable previous button if on first page
                self.previous.disabled = (self.current_page == 0)
                # Disable next button if on last page
                self.next.disabled = (self.current_page == len(self.matching_entries) - 1)

            @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, emoji="<:left:1307448382326968330>")
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Check if the interaction user is the same as the command invoker
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                    return

                # Move to previous page
                if self.current_page > 0:
                    self.current_page -= 1
                    await interaction.response.edit_message(embed=self.get_embed(), view=self)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="<:right:1307448399624405134>")
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Check if the interaction user is the same as the command invoker
                if interaction.user != self.ctx.author:
                    await interaction.response.send_message("You cannot use these buttons.", ephemeral=True)
                    return

                # Move to next page
                if self.current_page < len(self.matching_entries) - 1:
                    self.current_page += 1
                    await interaction.response.edit_message(embed=self.get_embed(), view=self)

        # Create and send the view
        view = SearchLoreView(ctx, matching_entries, user, query)
        await ctx.send(embed=view.get_embed(), view=view)

    @lore.command(name="leaderboard", aliases=['lb', 'top'])
    async def lore_leaderboard(self, ctx):
        """
        Shows the top 10 users with the most lore entries.
        """
        # Get all lorebook files
        import os
        import json

        # Ensure the Lorebooks directory exists
        lorebooks_dir = self.lorebooks_dir
        if not os.path.exists(lorebooks_dir):
            await ctx.send("No lore entries found.")
            return

        # Collect lore counts
        lore_counts = []
        for filename in os.listdir(lorebooks_dir):
            if filename.endswith('.json'):
                try:
                    # Extract user ID from filename
                    user_id = int(filename.split('.')[0])
                    
                    # Load the lorebook
                    filepath = os.path.join(lorebooks_dir, filename)
                    with open(filepath, 'r') as f:
                        lorebook = json.load(f)
                    
                    # Try to get the member
                    try:
                        member = await ctx.guild.fetch_member(user_id)
                        display_name = member.display_name
                    except:
                        # Fallback to user ID if member not found
                        display_name = str(user_id)
                    
                    # Add to lore counts
                    lore_counts.append({
                        'user_id': user_id,
                        'display_name': display_name,
                        'lore_count': len(lorebook)
                    })
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

        # Sort by lore count in descending order
        lore_counts.sort(key=lambda x: x['lore_count'], reverse=True)

        # Create the embed
        embed = discord.Embed(
            title="Lore Leaderboard 📜",
            description="Top 10 users with the most lore entries",
            color=0x000000
        )

        # Add leaderboard entries
        for i, entry in enumerate(lore_counts[:10], 1):
            embed.add_field(
                name=f"{i}. {entry['display_name']}",
                value=f"**{entry['lore_count']}** lore entries",
                inline=False
            )

        # Try to set the bot's avatar as the thumbnail
        try:
            embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
        except:
            pass

        # Send the embed
        await ctx.send(embed=embed)

    @lore.command(name='glb')
    async def get_lorebook(self, ctx):
        """Fetches the user's lorebook in JSON format."""
        user_id = ctx.author.id
        lorebook_path = self.get_lorebook_path(user_id)

        if os.path.exists(lorebook_path):
            with open(lorebook_path, 'r') as f:
                lore_data = json.load(f)

            # Send the lorebook as a JSON file
            file_name = f"{ctx.author.name}_lorebook.json"
            with open(file_name, 'w') as json_file:
                json.dump(lore_data, json_file, indent=4)
            await ctx.author.send(file=discord.File(file_name))
        else:
            await ctx.send("You do not have a lorebook.")
