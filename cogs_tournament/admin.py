import discord
from discord.ext import commands
from database import set_channel, get_channel
import config

class Admin(commands.Cog):
    """Commands for bot administration and configuration."""
    def __init__(self, bot):
        self.bot = bot

    def get_channel_id(self, channel_name, guild_id=None):
        # channel_name: mod_channel, event_channel, team_channel, log_channel, join_channel, game_channel
        if guild_id is None:
            return None
        return get_channel(guild_id, channel_name)

    async def check_mod_channel(self, ctx):
        """Check if command is being used in the mod channel"""
        mod_channel_id = self.get_channel_id("mod", ctx.guild.id)
        if not mod_channel_id:
            await ctx.send("❌ Mod channel not configured. Please set it up first with `dm.set_channel mod #channel`")
            return False
        if ctx.channel.id != mod_channel_id:
            mod_channel = ctx.guild.get_channel(mod_channel_id)
            await ctx.send(f"❌ This command can only be used in the mod channel: {mod_channel.mention if mod_channel else f'<#{mod_channel_id}>'}")
            return False
        return True

    async def log_mod_action(self, ctx, command_name, details=None):
        log_channel_id = self.get_channel_id("log", ctx.guild.id)
        if not log_channel_id:
            return
        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return
        embed = discord.Embed(
            title=f"🔧 Mod Command Executed",
            description=f"**Command:** `{command_name}`\n**By:** {ctx.author.mention} (`{ctx.author}`)\n**In:** {ctx.channel.mention} (`{ctx.guild.name}`)",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        if details:
            embed.add_field(name="Details", value=details, inline=False)
        embed.set_footer(text=f"User ID: {ctx.author.id}")
        await log_channel.send(embed=embed)

    @commands.command(name="set_mode", usage="<definition|tournament|both>")
    @commands.has_permissions(administrator=True)
    async def set_mode(self, ctx, mode: str):
        """Set the bot mode and reload cogs (admin only)."""
        if not await self.check_mod_channel(ctx):
            return
            
        mode = mode.lower()
        if mode not in ("definition", "tournament", "both"):
            await ctx.send("Invalid mode. Choose from: definition, tournament, both.")
            return
        config.set_mode(mode)
        await ctx.send(f"Bot mode set to **{mode}**. Reloading cogs...")
        await self.bot.reload_cogs(mode)
        await ctx.send(f"Cogs reloaded for mode: **{mode}**.")
        await self.log_mod_action(ctx, "set_mode", f"Mode set to: {mode}")

    @commands.command(name="set_channel", usage="<type> <channel>")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel_type: str, channel: discord.TextChannel):
        """Set a channel for a specific purpose (admin only).
        
        Available types: mod, event, team, log, join, game
        
        Examples:
        - dm.set_channel mod #moderation
        - dm.set_channel event #events
        - dm.set_channel team #teams
        - dm.set_channel log #bot-logs
        - dm.set_channel join #team-join
        - dm.set_channel game #game-chat
        """
        if not await self.check_mod_channel(ctx):
            return
            
        channel_type = channel_type.lower()
        valid_types = ["mod", "event", "team", "log", "join", "game"]
        
        if channel_type not in valid_types:
            await ctx.send(f"Invalid channel type. Available types: {', '.join(valid_types)}")
            return
            
        set_channel(ctx.guild.id, channel_type, channel.id)
        await ctx.send(f"✅ Set **{channel_type}** channel to {channel.mention}")
        details = f"Set `{channel_type}` channel to {channel.mention} ({channel.id})"
        await self.log_mod_action(ctx, "set_channel", details)

    @commands.command(name="clear_channel", usage="<type>")
    @commands.has_permissions(administrator=True)
    async def clear_channel(self, ctx, channel_type: str):
        """Clear a channel configuration (admin only).
        
        Available types: mod, event, team, log, join, game
        
        Examples:
        - dm.clear_channel mod
        - dm.clear_channel event
        """
        if not await self.check_mod_channel(ctx):
            return
            
        channel_type = channel_type.lower()
        valid_types = ["mod", "event", "team", "log", "join", "game"]
        
        if channel_type not in valid_types:
            await ctx.send(f"Invalid channel type. Available types: {', '.join(valid_types)}")
            return
            
        # Set to None to clear the channel
        set_channel(ctx.guild.id, channel_type, None)
        await ctx.send(f"✅ Cleared **{channel_type}** channel configuration")
        details = f"Cleared `{channel_type}` channel configuration"
        await self.log_mod_action(ctx, "clear_channel", details)

    @commands.command(name="show_channels")
    @commands.has_permissions(administrator=True)
    async def show_channels(self, ctx):
        """Show all configured channels for this server (admin only)."""
        if not await self.check_mod_channel(ctx):
            return
            
        types = ["mod", "event", "team", "log", "join", "game"]
        desc = ""
        for t in types:
            cid = get_channel(ctx.guild.id, t)
            if cid:
                ch = ctx.guild.get_channel(cid)
                desc += f"**{t.capitalize()}**: {ch.mention if ch else f'<#{cid}>'}\n"
            else:
                desc += f"**{t.capitalize()}**: Not set\n"
        await ctx.send(f"Configured channels:\n{desc}")
        await self.log_mod_action(ctx, "show_channels")

    @commands.command(name="show_mode")
    async def show_mode(self, ctx):
        """Show the current bot mode (definition, tournament, or both)."""
        if not await self.check_mod_channel(ctx):
            return
            
        import config
        mode = config.get_mode()
        await ctx.send(f"Current bot mode: **{mode}**")
        await self.log_mod_action(ctx, "show_mode")

    @commands.command(name="help", usage="<tournament|definitions>", help="Show help for the bot systems. Usage: dm.help tournament or dm.help definitions")
    async def help_command(self, ctx, *, arg: str = ""):
        if not await self.check_mod_channel(ctx):
            return
            
        if arg.lower() == "tournament":
            embed = discord.Embed(
                title="🏆 Tournament System Help",
                color=discord.Color.purple(),
                description="**Channel Structure:**\n"
                           "• **Mod Channel**: All admin commands (here)\n"
                           "• **Event Channel**: Tournament announcements + auto role management\n"
                           "• **Team Channel**: Tournament embed with clickable teams (DM details)\n"
                           "• **Join Channel**: Reaction-based team joining\n"
                           "• **Log Channel**: All tournament changes logged\n"
                           "• **Game Channel**: Auto-created for each tournament"
            )
            embed.add_field(
                name="📋 Event Management",
                value=(
                    "• `dm.create_event (Event Name/Max Sections)` - Create tournament\n"
                    "• `dm.list_events` - List all tournaments\n"
                    "• `dm.close_event <event_id>` - Delete tournament\n"
                    "• `dm.end_event <event_id> [event_role]` - End tournament & declare winners"
                ),
                inline=False
            )
            embed.add_field(
                name="📢 Tournament Announcements",
                value=(
                    "• `dm.announce <event_id> [announcement]` - Send tournament announcement"
                ),
                inline=False
            )
            embed.add_field(
                name="👥 Section & Team Management",
                value=(
                    "• `dm.create_section <event_id> (Section Name/Max Teams)` - Create section\n"
                    "• `dm.create_team <section_id> (Team Name/@Leader/Max Members)` - Create team\n"
                    "• `dm.join_team <team_name>` - Join team\n"
                    "• `dm.list_teams <event_id>` - List all teams\n"
                    "• `dm.delete_team <event_id> <sect_name> <team_name>` - Delete team\n"
                    "• `dm.delete_section <event_id> <sect_name>` - Delete section\n"
                    "• `dm.disqualify_team <event_id> <team_name> [reason]` - Disqualify team\n"
                    "• `dm.disqualify_member <event_id> <@member> [reason]` - Disqualify member"
                ),
                inline=False
            )
            embed.add_field(
                name="🏅 Leaderboard & Scores",
                value=(
                    "• `dm.create_leaderboard <event_id>` - Create leaderboard\n"
                    "• `dm.set_score <event_id> <team_name> <score>` - Set team score\n"
                    "• `dm.add_score <event_id> <team_name> <points>` - Add points\n"
                    "• `dm.show_scores <event_id>` - Show all scores"
                ),
                inline=False
            )
            embed.add_field(
                name="📊 Stats & Profiles",
                value=(
                    "• `dm.user_stats [@user]` - Show user stats\n"
                    "• `dm.team_stats <event_id> <team_name>` - Show team stats\n"
                    "• `dm.server_stats` - Show server stats\n"
                    "• `dm.profile [@user]` - Show user profile"
                ),
                inline=False
            )
            embed.set_footer(text="All commands must be used in the mod channel")
            await ctx.send(embed=embed)
        elif arg.lower() == "definitions":
            embed = discord.Embed(
                title="📚 Definitions System Help",
                color=discord.Color.blue(),
                description="How to use the Definitions system:"
            )
            embed.add_field(
                name="➕ Add a Definition",
                value=(
                    "1. **Reply** to the message you want to save as a definition.\n"
                    "2. Mention the bot and type: `define <title>[/author][/reference]` or `definition <title>[/author][/reference]`\n"
                    "   - Example: `@Bot define Python/Guido/PEP 8` (author and reference are optional)\n"
                    "3. The replied message's content will be saved as the definition."
                ),
                inline=False
            )
            embed.add_field(
                name="🔍 Get a Definition",
                value=(
                    "Mention the bot and type: `define <title>` or `definition <title>`\n"
                    "- Example: `@Bot define Python`\n"
                    "- If multiple definitions exist, use ◀️ ▶️ reactions to navigate."
                ),
                inline=False
            )
            embed.add_field(
                name="🗑️ Delete a Definition",
                value=(
                    "Use: `dm.del_definition <serial_number> <title>`\n"
                    "- Only the author or a moderator from the allowed server can delete definitions.\n"
                    "- Example: `dm.del_definition 2 Python`"
                ),
                inline=False
            )
            embed.set_footer(text="Definitions can be used in any channel")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🤖 Bot Help",
                color=discord.Color.green(),
                description="Welcome to the Discord Bot! Choose a system to learn more:"
            )
            embed.add_field(
                name="🏆 Tournament System",
                value="Use `dm.help tournament` to learn about tournament management, team creation, leaderboards, and more.",
                inline=False
            )
            embed.add_field(
                name="📚 Definitions System", 
                value="Use `dm.help definitions` to learn about saving and retrieving definitions from messages.",
                inline=False
            )
            embed.add_field(
                name="🔧 Admin Commands",
                value=(
                    "• `dm.set_channel <type> <#channel>` - Set channel for specific purpose\n"
                    "• `dm.show_channels` - Show all configured channels\n"
                    "• `dm.set_mode <mode>` - Set bot mode (definition/tournament/both)\n"
                    "• `dm.show_mode` - Show current bot mode"
                ),
                inline=False
            )
            embed.set_footer(text="All admin commands must be used in the mod channel")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot)) 