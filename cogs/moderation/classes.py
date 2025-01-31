import discord

from discord.ui import Button, View

class BanListView(View):
    def __init__(self, bans, author):
        super().__init__(timeout=60)
        self.bans = bans
        self.author = author
        self.current_page = 0
        self.items_per_page = 10

    def get_embed(self):
        embed = discord.Embed(title="Ban List", color=discord.Color.red())
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        bans_page = self.bans[start:end]

        ban_lines = [f"{ban.user} `(`{ban.user.id}`)`" for ban in bans_page]
        embed.description = "\n".join(ban_lines) if ban_lines else "No banned users found."

        total_bans = len(self.bans)
        embed.set_footer(
            text=f"Page: {self.current_page + 1}/{(total_bans - 1) // self.items_per_page + 1} | Showing {len(bans_page)}/{total_bans}"
        )
        return embed

    async def update_message(self, interaction):
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:left:1307448382326968330>", style=discord.ButtonStyle.primary)
    async def left_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed.", ephemeral=True)
            return
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(emoji="<:cancel:1307448502913204294>", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed.", ephemeral=True)
            return
        await interaction.response.edit_message(content="Ban list closed.", embed=None, view=None)

    @discord.ui.button(emoji="<:right:1307448399624405134>", style=discord.ButtonStyle.primary)
    async def right_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed.", ephemeral=True)
            return
        if (self.current_page + 1) * self.items_per_page < len(self.bans):
            self.current_page += 1
            await self.update_message(interaction)

class RolesView(View):
    def __init__(self, roles, author, custom_emojis):
        super().__init__(timeout=60)
        self.roles = roles
        self.author = author
        self.current_page = 0
        self.items_per_page = 10
        self.custom_emojis = custom_emojis

    def get_embed(self):
        embed = discord.Embed(title="Server Roles", color=discord.Color.blurple())
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        roles_page = self.roles[start:end]

        role_lines = [f"{role.name} `({role.id})`" for role in roles_page]
        embed.description = "\n".join(role_lines)

        embed.set_footer(
            text=f"Page {self.current_page + 1}/{(len(self.roles) - 1) // self.items_per_page + 1}"
        )
        return embed

    async def update_message(self, interaction):
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:left:1307448382326968330>", style=discord.ButtonStyle.primary)
    async def left_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed.", ephemeral=True)
            return
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(emoji="<:cancel:1307448502913204294>", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed, womp womp", ephemeral=True)
            return
        await interaction.response.edit_message(content="Embed closed.", embed=None, view=None)

    @discord.ui.button(emoji="<:right:1307448399624405134>", style=discord.ButtonStyle.primary)
    async def right_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't interact with this embed, womp womp", ephemeral=True)
            return
        if (self.current_page + 1) * self.items_per_page < len(self.roles):
            self.current_page += 1
            await self.update_message(interaction)