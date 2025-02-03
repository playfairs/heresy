from discord.ui import Select, View, Button
from discord import Interaction, SelectOption, Embed, ButtonStyle, ui
from discord.ext.commands import Group, MinimalHelpCommand
from discord.ext.commands.cog import Cog
from discord.ext.commands.flags import FlagsMeta
from discord.ext.commands.cog import Cog
from discord.ext.commands import Command
from discord.utils import MISSING
from discord.ext.commands import Context

from typing import List, Mapping, Union, Any, Callable, Coroutine

class HelpNavigator(View):
    def __init__(self, pages: list[Embed], timeout: int = 180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current page."""
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.pages) - 1

    @ui.button(label="◀", style=ButtonStyle.gray)
    async def previous_page(self, interaction: Interaction, button: Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @ui.button(label="▶", style=ButtonStyle.gray)
    async def next_page(self, interaction: Interaction, button: Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class HerseyHelp(MinimalHelpCommand):
    context: "Context"

    def __init__(self, **options):

        super().__init__(
            command_attrs={
                "help": "Shows help about the bot, a command, or a category of commands.",
                "aliases": ["h"],
                "example": "lastfm",
            },
            **options,
        )

        self.bot_user = None

    async def initialize_bot_user(self):

        if not self.bot_user:
            self.bot_user = self.context.bot.user

    def create_main_help_embed(self, ctx):

        embed = Embed(
            description="**information**\n> [ ] = optional, < > = required\n",
        )

        embed.add_field(
            name="Resources",
            value="**[invite](https://discordapp.com/oauth2/authorize?client_id=1284037026672279635&scope=bot+applications.commands&permissions=8)**  • "
            "**[server](https://discord.gg/flesh)**  • "
            "**[website](https://playfairs.cc/flesh)**  ",
            inline=False,
        )

        embed.set_author(
            name=f"{ctx.bot.user.name}",
            icon_url="https://playfairs.cc/flesh.png",
            # url=config.CLIENT.SUPPORT_URL,
        )
        embed.set_footer(text="Select a category from the dropdown menu below")

        return embed

    async def send_default_help_message(self, command: Command):
        await self.initialize_bot_user()         

        embed = Embed(
            title=f"Command: {command.qualified_name}",
            description=command.help or command.description or "No description available.",
            color=0x2b2d31,
        )

        embed.set_author(
            name=f"{self.context.bot.user.name} Command Help",
            icon_url="https://playfairs.cc/flesh.png",
        )

        syntax = self._format_syntax(command)
        example = getattr(command, 'example', '')
        embed.add_field(
            name="Syntax",
            value=f"```\n{syntax}\n```",
            inline=False,
        )

        if example:
            embed.add_field(
                name="Example",
                value=f"```\n{self.context.clean_prefix}{command.qualified_name} {example}\n```",
                inline=False,
            )

        if command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=True,
            )

        if command.checks:
            embed.add_field(
                name="Required Permissions",
                value=", ".join(
                    check.__qualname__.split(".")[0].replace("_", " ").title()
                    for check in command.checks
                ),
                inline=True,
            )

        embed.set_footer(
            text=f"Module: {command.cog_name or 'No Category'}",
            icon_url=self.context.author.display_avatar.url,
        )

        await self.context.reply(embed=embed)

    async def send_bot_help(
        self, mapping: Mapping[Union[Cog, None], List[Command[Any, Callable[..., Any], Any]]]  # type: ignore
    ) -> Coroutine[Any, Any, None]:  # type: ignore

        await self.initialize_bot_user()
        bot = self.context.bot

        embed = self.create_main_help_embed(self.context)
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        categories = sorted(
            [
                (cog.qualified_name, cog.description)
                for cog in mapping.keys()
                if cog
                and cog.qualified_name
                not in [
                    "Network",
                    "API",
                    "Owner",
                    "Status",
                    "Listeners",
                    "Hog",
                    "Developer",
                    "RateLimit",
                ]
                and (
                    "cogs" in cog.__module__
                    or cog.qualified_name == "Jishaku"  # Include Jishaku
                )
            ]
        )

        if not categories:
            return

        select = Select(
            placeholder="Choose a category...",
            options=[
                SelectOption(
                    label=category[0],
                    value=category[0],
                    description=category[1] if category[1] else "Developer Tools" if category[0] == "Jishaku" else None,
                    emoji="🛠️" if category[0] == "Jishaku" else None
                )
                for category in categories[:25]
            ],
        )

        async def select_callback(interaction: Interaction):
            if interaction.user.id != self.context.author.id:
                await interaction.warn("You cannot interact with this menu!")  # type: ignore
                return

            selected_category = interaction.data["values"][0]  # type: ignore
            selected_cog = next(
                (
                    cog
                    for cog in mapping.keys()
                    if cog and cog.qualified_name == selected_category
                ),
                None,
            )

            commands = mapping[selected_cog]
            command_list = ", ".join(
                [
                    (
                        f"{command.name}*"
                        if isinstance(command, Group)
                        else f"{command.name.replace('jishaku', 'jsk')}" if selected_category == "Jishaku"
                        else f"{command.name}"
                    )
                    for command in sorted(commands, key=lambda x: x.name)
                ]
            )

            embed = Embed(
                title=f"Category: {'Developer Tools' if selected_category == 'Jishaku' else selected_category}",
                description=f"```\n{command_list}\n```",
                color=0x2b2d31
            )

            if selected_category == "Jishaku":
                embed.add_field(
                    name="Note",
                    value="These commands are restricted to bot developers only.\nUse `help jsk` for detailed information.",
                    inline=False
                )

            embed.set_author(
                name=f"{bot.user.name}",
                icon_url="https://playfairs.cc/flesh.png"
            )

            embed.set_footer(
                text=f"{len(commands)} command{'s' if len(commands) != 1 else ''}"
            )

            await interaction.response.edit_message(embed=embed, view=view)

        select.callback = select_callback

        view = View(timeout=180)
        view.add_item(select)

        await self.context.reply(embed=embed, view=view)

    async def send_group_help(self, group: Group):
        """Special handling for command groups with pagination."""
        await self.initialize_bot_user()

        if group.cog is None or "cogs" not in getattr(group.cog, "__module__", ""):
            await self.send_default_help_message(group)
            return

        bot = self.context.bot
        pages = []

        # First page: Main group info
        main_embed = Embed(
            title=f"Command Group: {group.qualified_name}",
            description=f"> {group.description.capitalize() if group.description else (group.help.capitalize() if group.help else 'No description available')}",
            color=0x2b2d31
        )
        
        main_embed.set_author(
            name=f"{bot.user.name} Command Help",
            icon_url="https://playfairs.cc/flesh.png"
        )

        # Main command syntax
        syntax = self._format_syntax(group)
        main_embed.add_field(
            name="Group Syntax",
            value=f"```\n{syntax}\n```",
            inline=False
        )

        # Example usage if different from syntax
        example = self._format_example(group)
        if example != syntax:
            main_embed.add_field(
                name="Example",
                value=f"```\n{example}\n```",
                inline=False
            )

        # Aliases
        aliases = ", ".join(f"`{a}`" for a in group.aliases) if group.aliases else "None"
        main_embed.add_field(
            name="Aliases",
            value=aliases,
            inline=True
        )

        # Permissions
        try:
            permissions = ", ".join(
                [
                    permission.lower().replace("n/a", "None").replace("_", " ")
                    for permission in group.permissions
                ]
            )
        except AttributeError:
            permissions = "None"

        if permissions and permissions.lower() != "none":
            main_embed.add_field(
                name="Required Permissions",
                value=permissions,
                inline=True
            )

        main_embed.set_footer(
            text=f"Module: {group.cog_name} • Page 1/{len(group.commands) + 1}",
            icon_url=self.context.author.display_avatar.url
        )

        pages.append(main_embed)

        # Create a page for each subcommand
        for i, cmd in enumerate(sorted(group.commands, key=lambda x: x.name), 1):
            cmd_embed = Embed(
                title=f"Subcommand: {group.qualified_name} {cmd.name}",
                description=f"> {cmd.description.capitalize() if cmd.description else (cmd.help.capitalize() if cmd.help else 'No description available')}",
                color=0x2b2d31
            )
            
            cmd_embed.set_author(
                name=f"{bot.user.name} Command Help",
                icon_url="https://playfairs.cc/flesh.png"
            )

            # Subcommand syntax
            cmd_syntax = self._format_syntax(cmd)
            cmd_embed.add_field(
                name="Syntax",
                value=f"```\n{cmd_syntax}\n```",
                inline=False
            )

            # Example usage
            cmd_example = self._format_example(cmd)
            if cmd_example != cmd_syntax:
                cmd_embed.add_field(
                    name="Example",
                    value=f"```\n{cmd_example}\n```",
                    inline=False
                )

            # Add any command-specific flags
            for param in cmd.clean_params.values():
                if isinstance(param.annotation, FlagsMeta):
                    flags = param.annotation.__commands_flags__
                    flag_desc = []
                    for flag_name, flag in flags.items():
                        req = "required" if flag.required else "optional"
                        desc = flag.help or "No description"
                        flag_desc.append(f"• --{flag_name}: {desc} ({req})")
                    
                    cmd_embed.add_field(
                        name="Flags",
                        value="\n".join(flag_desc),
                        inline=False
                    )

            cmd_embed.set_footer(
                text=f"Module: {group.cog_name} • Page {i + 1}/{len(group.commands) + 1}",
                icon_url=self.context.author.display_avatar.url
            )

            pages.append(cmd_embed)

        # Send the paginated help
        view = HelpNavigator(pages)
        await self.context.reply(embed=pages[0], view=view)

    async def send_cog_help(self, cog: Cog):
        await self.initialize_bot_user()
        bot = self.context.bot

        if cog.qualified_name == "Jishaku":
            pages = []
            
            # Create main overview page
            overview = Embed(
                title="Developer Tools (Jishaku)",
                description=(
                    "Advanced developer commands for debugging and maintenance.\n"
                    "These commands are restricted to bot developers only.\n\n"
                    "**Common Aliases:**\n"
                    "• `jsk py` → Python evaluation\n"
                    "• `jsk sh` → Shell commands\n"
                    "• `jsk load/reload/unload` → Extension management\n"
                    "• `jsk rtfs` → Source code lookup\n"
                ),
                color=0x2b2d31
            )
            overview.set_author(
                name=f"{bot.user.name} Developer Tools",
                icon_url="https://playfairs.cc/flesh.png"
            )
            overview.set_footer(
                text=f"Page 1/{len(cog.get_commands()) + 1}",
                icon_url=self.context.author.display_avatar.url
            )
            pages.append(overview)

            # Create a page for each command
            for i, cmd in enumerate(sorted(cog.get_commands(), key=lambda x: x.name), 1):
                embed = Embed(
                    title=f"Command: {cmd.name.replace('jishaku', 'jsk')}",
                    description=cmd.help or cmd.description or "No description available",
                    color=0x2b2d31
                )
                
                embed.set_author(
                    name=f"{bot.user.name} Developer Tools",
                    icon_url="https://playfairs.cc/flesh.png"
                )

                # Command syntax
                syntax = self._format_syntax(cmd)
                embed.add_field(
                    name="Syntax",
                    value=f"```\n{syntax}\n```",
                    inline=False
                )

                # Add aliases if any
                aliases = cmd.aliases
                if aliases:
                    # Replace 'jishaku' with 'jsk' in aliases
                    aliases = [alias.replace('jishaku', 'jsk') for alias in aliases]
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(f"`{a}`" for a in aliases),
                        inline=True
                    )

                embed.set_footer(
                    text=f"Page {i + 1}/{len(cog.get_commands()) + 1}",
                    icon_url=self.context.author.display_avatar.url
                )
                pages.append(embed)

            # Send paginated help
            view = HelpNavigator(pages)
            await self.context.reply(embed=pages[0], view=view)
            return

        # Regular cog help for non-Jishaku cogs
        embed = Embed(
            title=f"Category: {cog.qualified_name}",
            description=cog.description,
            color=0x2b2d31
        )

        embed.set_author(
            name=f"{bot.user.name} Command Help",
            icon_url="https://playfairs.cc/flesh.png"
        )

        embed.set_footer(
            text=f"Module: {cog.qualified_name}",
            icon_url=self.context.author.display_avatar.url
        )

        await self.context.reply(embed=embed)

    async def send_command_help(self, command: Command):
        await self.initialize_bot_user()

        # Special handling for 'jsk' or 'jishaku' command
        if command.qualified_name.lower() in ['jsk', 'jishaku'] or command.name.lower() in ['jsk', 'jishaku']:
            # Find the Jishaku cog
            jsk_cog = self.context.bot.get_cog('Jishaku')
            if not jsk_cog:
                # Try to find any command that starts with jishaku or jsk
                for cmd in self.context.bot.commands:
                    if cmd.name.startswith(('jishaku', 'jsk')):
                        jsk_cog = cmd.cog
                        break

            if jsk_cog:
                pages = []
                bot = self.context.bot

                # Get all Jishaku commands and sort them
                jsk_commands = sorted(jsk_cog.get_commands(), key=lambda x: x.name)
                
                # Create a page for each command
                for i, cmd in enumerate(jsk_commands):
                    cmd_name = cmd.name.replace('jishaku', 'jsk')
                    embed = Embed(
                        title="Developer Tools (Jishaku)",
                        description=f"Command {i + 1}/{len(jsk_commands)}",
                        color=0x2b2d31
                    )
                    
                    embed.set_author(
                        name=f"{bot.user.name} Command Help",
                        icon_url="https://playfairs.cc/flesh.png"
                    )

                    # Command name and description
                    embed.add_field(
                        name=f"Command: {cmd_name}",
                        value=f"> {cmd.help or cmd.description or 'No description available'}",
                        inline=False
                    )

                    # Command syntax
                    syntax = self._format_syntax(cmd).replace('jishaku', 'jsk')
                    embed.add_field(
                        name="Syntax",
                        value=f"```\n{syntax}\n```",
                        inline=False
                    )

                    # Add aliases if any
                    aliases = cmd.aliases
                    if aliases:
                        # Replace 'jishaku' with 'jsk' in aliases
                        aliases = [alias.replace('jishaku', 'jsk') for alias in aliases]
                        embed.add_field(
                            name="Aliases",
                            value=", ".join(f"`{a}`" for a in aliases),
                            inline=True
                        )

                    # Add parameters if any
                    params = []
                    for name, param in cmd.clean_params.items():
                        if isinstance(param.annotation, FlagsMeta):
                            flags = param.annotation.__commands_flags__
                            flag_desc = []
                            for flag_name, flag in flags.items():
                                req = "required" if flag.required else "optional"
                                desc = flag.help or "No description"
                                flag_desc.append(f"• --{flag_name}: {desc} ({req})")
                            
                            if flag_desc:
                                embed.add_field(
                                    name="Flags",
                                    value="\n".join(flag_desc),
                                    inline=False
                                )
                        else:
                            required = "required" if param.default == param.empty else "optional"
                            param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else 'Any'
                            if param_type == '_empty':
                                param_type = 'Any'
                            params.append(f"• **{name}** ({param_type}): {required}")
                    
                    if params:
                        embed.add_field(
                            name="Parameters",
                            value="\n".join(params),
                            inline=False
                        )

                    # Add note about developer-only access
                    embed.add_field(
                        name="Required Permissions",
                        value="Bot Developer",
                        inline=True
                    )

                    embed.set_footer(
                        text=f"Module: Jishaku • Use ◀ ▶ to view all commands",
                        icon_url=self.context.author.display_avatar.url
                    )
                    pages.append(embed)

                # Send paginated help
                if pages:
                    view = HelpNavigator(pages)
                    await self.context.reply(embed=pages[0], view=view)
                    return

        # Regular command help for non-jsk commands
        if command.cog is None or "cogs" not in getattr(command.cog, "__module__", ""):
            await self.send_default_help_message(command)
            return

        bot = self.context.bot

        try:
            permissions = ", ".join(
                [
                    permission.lower().replace("n/a", "None").replace("_", " ")
                    for permission in command.permissions
                ]
            )
        except AttributeError:
            permissions = "None"

        brief = command.brief or ""

        if permissions != "None" and brief:
            permissions = f"{permissions}\n{brief}"
        elif brief:
            permissions = brief

        # Create embed
        embed = Embed(
            title=f"Command: {command.qualified_name}",
            description=f"> {command.description.capitalize() if command.description else (command.help.capitalize() if command.help else 'No description available')}",
            color=0x2b2d31
        )
        
        embed.set_author(
            name=f"{bot.user.name} Command Help",
            icon_url="https://playfairs.cc/flesh.png"
        )

        # Command syntax
        syntax = self._format_syntax(command)
        embed.add_field(
            name="Syntax",
            value=f"```\n{syntax}\n```",
            inline=False
        )

        # Example usage with standardized placeholders
        example = self._format_example(command)
        if example != syntax:  # Only show example if it's different from syntax
            embed.add_field(
                name="Example",
                value=f"```\n{example}\n```",
                inline=False
            )

        # Aliases section
        aliases = ", ".join(f"`{a}`" for a in command.aliases) if command.aliases else "None"
        embed.add_field(
            name="Aliases",
            value=aliases,
            inline=True
        )

        # Permissions section
        if permissions and permissions.lower() != "none":
            embed.add_field(
                name="Required Permissions",
                value=permissions,
                inline=True
            )

        # Cooldown info
        if hasattr(command, '_buckets') and command._buckets._cooldown:
            cd = command._buckets._cooldown
            embed.add_field(
                name="Cooldown",
                value=f"{cd.rate} use{'s' if cd.rate > 1 else ''} per {cd.per:.0f} seconds",
                inline=True
            )

        # Add flags if command has them
        for param in command.clean_params.values():
            if isinstance(param.annotation, FlagsMeta):
                flags = param.annotation.__commands_flags__
                flag_desc = []
                for flag_name, flag in flags.items():
                    req = "required" if flag.required else "optional"
                    desc = flag.help or "No description"
                    flag_desc.append(f"• --{flag_name}: {desc} ({req})")
                
                embed.add_field(
                    name="Flags",
                    value="\n".join(flag_desc),
                    inline=False
                )

        embed.set_footer(
            text=f"Module: {command.cog_name}",
            icon_url=self.context.author.display_avatar.url
        )

        await self.context.reply(embed=embed)

    async def send_error_message(self, error: str):

        if not error or not error.strip():
            return

        embed = Embed(
            title="Error",
            description=error,
        )

        await self.context.send(embed=embed)

    async def command_not_found(self, string: str):

        if not string:
            return

        error_message = f"> {config.EMOJIS.CONTEXT.WARN} {self.context.author.mention}: Command `{string}` does not exist"  # type: ignore
        if not error_message.strip():
            return

        embed = Embed(description=error_message)
        await self.context.send(embed=embed)

        # React to the original message with a question mark
        await self.context.message.add_reaction('❓')

    async def subcommand_not_found(self, command: str, subcommand: str):

        if not command or not subcommand:
            return

        error_message = f"> {config.EMOJIS.CONTEXT.WARN} {self.context.author.mention}: Command `{command} {subcommand}` does not exist"  # type: ignore
        if not error_message.strip():
            return

        embed = Embed(title="", description=error_message)
        await self.context.send(embed=embed)

    def _format_syntax(self, command: Command) -> str:
        """Format command syntax with proper argument formatting."""
        try:
            params = []
            for name, param in command.clean_params.items():
                if isinstance(param.annotation, FlagsMeta):
                    # Handle flags
                    flag_params = []
                    for flag_name, flag in param.annotation.__commands_flags__.items():
                        if flag.required:
                            flag_params.append(f"--{flag_name} <value>")
                        else:
                            flag_params.append(f"[--{flag_name} value]")
                    params.append(" ".join(flag_params))
                else:
                    # Regular parameters
                    if param.default == param.empty:
                        params.append(f"<{name}>")
                    else:
                        params.append(f"[{name}]")
            
            return f"{self.context.clean_prefix}{command.qualified_name} {' '.join(params)}"
        except AttributeError:
            return f"{self.context.clean_prefix}{command.qualified_name}"

    def _format_example(self, command: Command) -> str:
        """Format command example with standardized placeholders."""
        try:
            example = command.example or ""
            # Replace common placeholders with standardized values
            replacements = {
                "@user": "@playfairs",
                "@member": "@playfairs",
                "@role": "@role",
                "@channel": "#general",
                "<user>": "@playfairs",
                "<member>": "@playfairs",
                "<role>": "@role",
                "<channel>": "#general"
            }
            
            for old, new in replacements.items():
                example = example.replace(old, new)
                
            return f"{self.context.clean_prefix}{command.qualified_name} {example}"
        except AttributeError:
            return f"{self.context.clean_prefix}{command.qualified_name}"
