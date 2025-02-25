import discord
import os

from discord.ext.commands import command, Cog, Context
from main import heresy
from discord.ext.commands import has_permissions


class Misc(Cog):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.reports_dir = './Reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        self.permanent_snipes = {}  # Separate dictionary for permanent snipes

    @command(name="report", help="Report an issue with the bot.")
    async def report(self, ctx, *, description: str = None):
        """Allows users to report issues with the bot."""
        if not description:
            await ctx.send("Please describe the issue you want to report.")
            return

        existing_issues = [f for f in os.listdir(self.reports_dir) if f.startswith("Issue #")]
        issue_number = len(existing_issues) + 1
        issue_file = os.path.join(self.reports_dir, f"Issue #{issue_number}.txt")

        with open(issue_file, 'w') as file:
            file.write(f"Issue #{issue_number}\n")
            file.write(f"Reported by: {ctx.author} (ID: {ctx.author.id})\n\n")
            file.write(f"Description:\n{description}")

        await ctx.send(f"Thank you for reporting! Your issue has been logged as `Issue #{issue_number}`.")

    @command(name="issues", help="View all reported issues.")
    async def issues(self, ctx: Context):
        """Lists all reported issues in an embed."""
        existing_issues = [f for f in os.listdir(self.reports_dir) if f.startswith("Issue #")]

        if not existing_issues:
            await ctx.send("No issues have been reported yet.")
            return

        embed = discord.Embed(title="Reported Issues", color=discord.Color.orange())
        for issue in existing_issues:
            embed.add_field(name=issue, value=f"`{issue}` logged in reports.", inline=False)

        await ctx.send(embed=embed)

#    @command(name="report", help="Report an issue with the bot.")
#    async def report(self, ctx, *, description: str = None):
#        """Allows users to report issues with the bot."""
#        if not description:
#            await ctx.send("Please describe the issue you want to report.")
#            return

#        existing_issues = [f for f in os.listdir(self.reports_dir) if f.startswith("Issue #")]
#        issue_number = len(existing_issues) + 1
#        issue_file = os.path.join(self.reports_dir, f"Issue #{issue_number}.txt")

#        with open(issue_file, 'w') as file:
#            file.write(f"Issue #{issue_number}\n")
#            file.write(f"Reported by: {ctx.author} (ID: {ctx.author.id})\n\n")
#            file.write(f"Description:\n{description}")

#        await ctx.send(f"Thank you for reporting! Your issue has been logged as `Issue #{issue_number}`.")

#    @command(name="issues", help="View all reported issues.")
#    async def issues(self, ctx: Context):
#        """Lists all reported issues in an embed."""
#        existing_issues = [f for f in os.listdir(self.reports_dir) if f.startswith("Issue #")]

#        if not existing_issues:
#            await ctx.send("No issues have been reported yet.")
#            return

#        embed = discord.Embed(title="Reported Issues", color=discord.Color.orange())
#        for issue in existing_issues:
#            embed.add_field(name=issue, value=f"`{issue}` logged in reports.", inline=False)

#        await ctx.send(embed=embed)

#    @command(name="rules")
#    @has_permissions(manage_guild=True)
#    async def rules(self, ctx):
#        """Posts the server rules in an embed"""
#        embed = discord.Embed(
#            title="Server Guides",
#            color=discord.Color.dark_theme()
#        )

#        rules_text = (
#            "## Rules\n\n"
#            "• Discord TOS and Guidelines must be followed, they can be found [here](https://discord.com/terms).\n\n"
#            "• No spamming - Except for in <#1332731298061488251>. This will mean on excess of 5 line splits. **This is does not apply to code blocks to a degree, as long as there not many white spaces, its fine. Try to send as a file, most file types have provided syntax highlighting.**\n\n"
#            "• No asking for anything to help for Malicious Intent, like Viruses, Malware, RAT'S, Scams, and Discord Selfbots.\n\n"
#            "• No Gore, NSFW, NSFL, or disgusting content, this is strictly enforced and perpetrators will be punished accordingly.\n\n"
#            "• No racism, sexism, homophobia, or transphobia,  It is importantto respect each other and their preferences.\n\n"
#            "• Anyone under the age of 13, per discord TOS, will be banned from the server for the safety of minors.\n\n"
#            "## Directory\n"
#            "• <id:customize> : Roles and Channels.\n"
#            "• <#1332729496754720828> : Main text channel for general discussion.\n"
#            "• <#1332731298061488251> : Venting, talking about projects, and possibly getting help.\n"
#            "• [VC1](https://discord.com/channels/1271976967381712989/1332734736480866356) : 1/2 Voice Channel to share and converse projects.\n"
#            "• [VC2](https://discord.com/channels/1271976967381712989/1332734781770829865) : 2/2 Voice Channel to share and converse projects.\n\n"
#            "## Other\n"
#            "• <#1332729301048623185> : Chat for testing and debugging bots.\n\n"
#            "• [VC3](https://discord.com/channels/1271976967381712989/1332729334808580220) : 1/1 Voice Channel for testing and debugging bots.\n\n"
#            "• <#1332733770981183529> : Forum for debugging, meant to help you get your code running and fix any bugs.\n\n"
#            "• <#1332734141279637574> : Forum for sharing your projects, milestones, and get input and feedback.\n\n"
#        )

#        embed.description = rules_text
#        embed.add_field(name="", value="[GitHub](https://github.com/playfairs-cc) • [Website](https://playfairs.cc/heresy) • [Server](https://discord.gg/heresy)", inline=False)
#        embed.set_thumbnail(url="https://playfairs.cc/heresy.jpg?size=1024")
#        await ctx.send(embed=embed)

#    @command(name="modrules")
#    @has_permissions(manage_messages=True)
#    async def modrules(self, ctx):
#        """Posts the moderator rules in an embed (Mod+ only)"""
#        embed = discord.Embed(
#            title="Moderation Rules",
#            color=discord.Color.dark_theme()
#        )

#        rules_text = (
#            "## Guidelines\n\n"
#            "• Don't get an ego and do your own thing because you have perms, I will easily take them away.\n\n"
#            "• Do not abuse your permissions or you will be demoted.\n\n"
#            "• All actions will probably be logged in logs, so don't worry about doing it manually.\n\n"
#            "• If unsure about something, either ask staff or just wait till it seems like it's needed.\n\n"
#            "• Do not mass ping everyone just because the server is dead, it's annoying, user revive pings for that.\n\n"
#            "## Warning Protocol (Users who are boosting will be role stripped, banned only if deemed necessary)\n"
#            "• 1st Warning: Verbal warning in chat\n"
#            "• 2nd Warning: Timeout (1 hour)\n"
#            "• 3rd Warning: Jail (24 hours)\n"
#            "• 4th Warning: Ban\n\n"
#            "## Important Channels\n"
#            "• <#1286292755693441076> :: All moderation actions\n"
#            "• <#1310911272392327199> :: Jail related actions\n"
#            "• <#1294421265448439901> :: Staff discussion\n"
#            "## Other\n"
#            "• Don't ban or timeout someone because you don't like them, this isn't kindergarten.\n"
#            "• If your not active in the server, you will be demoted to make room for active staff.\n"
#            "• When taking action, use the bot for it, don't do it manually.\n"
#            "• Discuss moderation with staff, don't just do it yourself with notifying admins.\n\n"
#            "-# For questions about moderation, please consult higher staff or admins."
#        )

#        embed.description = rules_text
#        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/785042666475225109/a_49422bfa76ed118dbe14d94bc2c4818a.gif?size=1024")
#        await ctx.send(embed=embed)

#    @command(name="perks")
#    async def perks(self, ctx):
#        """Shows all server booster perks and information"""
#        embed = discord.Embed(
#            title="Booster Perks",
#            description="Thank you for considering boosting our server! Here are all the perks you receive:",
#            color=0xf47fff
#        )

#        perks_text = (
#            "## Perks\n\n"
#            "• Custom Role + Hoisted + Custom Hex\n"
#            "• Immunity to Jail, Ban, Kick, Mute, and Timeout\n"
#            "  *(Breaking rules will ignore this and result in a ban)*\n\n"
#            "## How to Claim\n"
#            "• DM or Ping Admins or staff to claim perks\n"
#            "• Or directly contact <@785042666475225109> to claim\n\n"
#            "## Additional Info\n"
#            "• Perks are active as long as your boost is active\n"
#            "• Custom roles must follow server guidelines\n"
#            "• Abuse of perks will result in removal and/or ban\n\n"
#            " Questions about perks? Feel free to ask staff!\n\n"
#            " More perks will be added as the server grows"
#        )

#        embed.description = perks_text
#        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/785042666475225109/a_49422bfa76ed118dbe14d94bc2c4818a.gif?size=1024")
#        embed.set_footer(text="Boost the server to unlock perks")
#        await ctx.send(embed=embed)

#    @command(name="psg")
#    async def partnership_guidelines(self, ctx):
#        """Shows partnership requirements and guidelines"""
#        embed = discord.Embed(
#            title="Partnership Guidelines",
#            color=discord.Color.dark_theme()
