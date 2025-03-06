import discord
from discord.ext import commands
from discord import app_commands
from main import heresy
from discord.ext.commands import Context, group, has_permissions, Cog
from datetime import datetime, timezone
from discord import AutoModRuleEventType, AutoModRuleTriggerType, AutoModAction

class Automod(Cog, description="View commands in Automod. (Need Work.)"):
    def __init__(self, bot: heresy):
        self.bot = bot
        self.start_time = datetime.now(timezone.utc)

    @group(name="automod", aliases=["am"])
    @has_permissions(manage_guild=True)
    async def automod(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @automod.command(name="create", aliases=["createrule"])
    @has_permissions(manage_guild=True)
    async def create_rule(self, ctx: Context, *, name: str, event_type: AutoModRuleEventType, trigger_type: AutoModRuleTriggerType, trigger_metadata: dict, actions: list[AutoModAction], enabled: bool, exempt_roles: list[discord.Role], exempt_channels: list[discord.TextChannel]):
        rule = await ctx.guild.auto_moderation_rules.create(
            name=name,
            event_type=event_type,
            trigger_type=trigger_type,
            trigger_metadata=trigger_metadata,
            actions=actions,
            enabled=enabled,
            exempt_roles=exempt_roles,
            exempt_channels=exempt_channels,
        )
        await ctx.send(f"Created automod rule: {rule.name}")

    @automod.command(name="delete", aliases=["deleterule"])
    @has_permissions(manage_guild=True)
    async def delete_rule(self, ctx: Context, *, name: str):
        rule = await ctx.guild.auto_moderation_rules.get(name)
        if not rule:
            await ctx.send(f"Rule '{name}' not found.")
            return
        await rule.delete()
        await ctx.send(f"Deleted automod rule: {name}")

    @automod.command(name="list", aliases=["listrules"])
    @has_permissions(manage_guild=True)
    async def list_rules(self, ctx: Context):
        rules = await ctx.guild.auto_moderation_rules.all()
        if not rules:
            await ctx.send("No automod rules found.")
            return
        
        embed = discord.Embed(title="Automod Rules", color=0xADD8E6)
        for rule in rules:
            embed.add_field(name=rule.name, value=f"Event Type: {rule.event_type}\nTrigger Type: {rule.trigger_type}")
        await ctx.send(embed=embed) 

    @automod.command(name="edit", aliases=["editrule"])
    @has_permissions(manage_guild=True)
    async def edit_rule(self, ctx: Context, *, name: str, new_name: str, event_type: AutoModRuleEventType, trigger_type: AutoModRuleTriggerType, trigger_metadata: dict, actions: list[AutoModAction], enabled: bool, exempt_roles: list[discord.Role], exempt_channels: list[discord.TextChannel]):
        rule = await ctx.guild.auto_moderation_rules.get(name)
        if not rule:
            await ctx.send(f"Rule '{name}' not found.")
            return
        
        await rule.edit(
            name=new_name,
            event_type=event_type,
            trigger_type=trigger_type,
            trigger_metadata=trigger_metadata,
            actions=actions,
            enabled=enabled,
            exempt_roles=exempt_roles,
            exempt_channels=exempt_channels,
        )
        await ctx.send(f"Edited automod rule: {rule.name}")

    @group(name="filter", description="Filters words using automod.", invoke_without_command=True)
    @has_permissions(manage_guild=True)
    async def filter(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @filter.command(name="add", description="Adds a word to the filter list.")
    @has_permissions(manage_guild=True)
    async def add(self, ctx: Context, *, word: str):
        existing_rules = await ctx.guild.fetch_automod_rules()
        heresy_rule = discord.utils.get(existing_rules, name="heresy")

        if heresy_rule:
            current_keywords = heresy_rule.trigger_metadata.get("keyword_filter", [])
            if word in current_keywords:
                await ctx.reply(f"The keyword `{word}` is already filtered.")
                return
            
            current_keywords.append(word)
            await hvam_rule.edit(
                trigger_metadata={"keyword_filter": current_keywords}
            )
        else:
            await ctx.guild.create_automod_rule(
                name="heresy",
                event_type=AutoModRuleEventType.message_send,
                trigger=AutoModRuleTriggerType.keyword,
                metadata={
                    "keyword_filter": [word],
                    "regex_patterns": []
                },
                actions=[
                    AutoModAction(
                        type=1,
                        metadata={}
                    )
                ],
                enabled=True,
                exempt_roles=[],
                exempt_channels=[],
            )
        await ctx.send(f"Added word: {word}")

    @filter.command(name="remove", description="Removes a word from the filter list.")
    @has_permissions(manage_guild=True)
    async def remove(self, ctx: Context, *, word: str):
        existing_rules = await ctx.guild.auto_moderation_rules.all()
        heresy_rule = discord.utils.get(existing_rules, name="heresy")

        if not heresy_rule:
            await ctx.send(f"Rule 'heresy' not found.")
            return

        current_keywords = heresy_rule.trigger_metadata.get("keyword_filter", [])
        if word not in current_keywords:
            await ctx.reply(f"The keyword `{word}` is not filtered.")
            return

        current_keywords.remove(word)
        await hvam_rule.edit(
            trigger_metadata={"keyword_filter": current_keywords}
        )
        await ctx.send(f"Removed word: {word}")

    @filter.command(name="list", description="Lists all filtered words.")
    @has_permissions(manage_guild=True)
    async def list(self, ctx: Context):
        existing_rules = await ctx.guild.auto_moderation_rules.all()
        hvam_rule = discord.utils.get(existing_rules, name="HVAM")

        if not heresy_rule:
            await ctx.send(f"Rule 'heresy' not found.")
            return

        current_keywords = heresy_rule.trigger_metadata.get("keyword_filter", [])
        if not current_keywords:
            await ctx.send("No words are currently filtered.")
            return

        embed = discord.Embed(title="Filtered Words", color=0xADD8E6)
        embed.add_field(name="Filtered Words", value="\n".join(current_keywords))
        await ctx.send(embed=embed)