import discord
from discord.ext import commands
from database import set_channel, get_channel
import config

class Admin(commands.Cog):
    """Commands for bot administration and configuration."""
    def __init__(self, bot):
        self.bot = bot

    def get_channel_id(self, channel_name, guild_id=None):
        # channel_name: mod_channel, event_channel, team_channel, log_channel
        if guild_id is None:
            return None
        return get_channel(guild_id, channel_name)

    async def log_mod_action(self, ctx, command_name, details=None):
        log_channel_id = self.get_channel_id("log_channel", ctx.guild.id)
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
        mode = mode.lower()
        if mode not in ("definition", "tournament", "both"):
            await ctx.send("Invalid mode. Choose from: definition, tournament, both.")
            return
        config.set_mode(mode)
        await ctx.send(f"Bot mode set to **{mode}**. Reloading cogs...")
        await self.bot.reload_cogs(mode)
        await ctx.send(f"Cogs reloaded for mode: **{mode}**.")

    @commands.command(name="set_channel", usage="<type> <channel>")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel_type: str, channel: discord.TextChannel):
        """Set a channel for a specific purpose (mod, event, team, log, etc)."""
        set_channel(ctx.guild.id, channel_type.lower(), channel.id)
        await ctx.send(f"Set {channel_type} channel to {channel.mention}.")
        details = f"Set `{channel_type}` channel to {channel.mention} ({channel.id})"
        await self.log_mod_action(ctx, "set_channel", details)

    @commands.command(name="show_channels")
    @commands.has_permissions(administrator=True)
    async def show_channels(self, ctx):
        """Show all configured channels for this server."""
        types = ["mod", "event", "team", "log"]
        desc = ""
        for t in types:
            cid = get_channel(ctx.guild.id, t)
            if cid:
                ch = ctx.guild.get_channel(cid)
                desc += f"**{t.capitalize()}**: {ch.mention if ch else cid}\n"
            else:
                desc += f"**{t.capitalize()}**: Not set\n"
        await ctx.send(f"Configured channels:\n{desc}")
        await self.log_mod_action(ctx, "show_channels")

    @commands.command(name="help", usage="tournament", help="Show help for the tournament system. Usage: dm.help tournament")
    async def help_tournament(self, ctx, *, arg: str = ""):
        if arg.lower() != "tournament":
            return  # Only respond to 'dm.help tournament'
        embed = discord.Embed(
            title="Tournament Help",
            color=discord.Color.purple(),
            description="How to use the Tournament system:"
        )
        embed.add_field(
            name="Event Management",
            value=(
                "- `dm.create_event (Event Name/Max Sections)`: Create a new event.\n"
                "- `dm.list_events`: List all events.\n"
                "- `dm.close_event <event_id>`: Delete an event (admin only).\n"
                "- `dm.end_event <event_id> [event_role]`: End an event, declare winners, and reset leaderboard (admin only)."
            ),
            inline=False
        )
        embed.add_field(
            name="Section & Team Management",
            value=(
                "- `dm.create_section <event_id> (Section Name/Max Teams)`: Create a section in an event.\n"
                "- `dm.create_team <section_id> (Team Name/@Leader/Max Members)`: Create a team in a section.\n"
                "- `dm.join_team <team_name>`: Join a team.\n"
                "- `dm.list_teams <event_id>`: List all teams for an event.\n"
                "- `dm.delete_team <event_id> <sect_name> <team_name>`: Delete a team (admin only).\n"
                "- `dm.delete_section <event_id> <sect_name>`: Delete a section (admin only).\n"
                "- `dm.disqualify_team <event_id> <team_name> [reason]`: Disqualify a team (admin only).\n"
                "- `dm.disqualify_member <event_id> <@member> [reason]`: Disqualify a member from all teams in an event (admin only)."
            ),
            inline=False
        )
        embed.add_field(
            name="Leaderboard & Scores",
            value=(
                "- `dm.create_leaderboard <event_id>`: Create a leaderboard for an event.\n"
                "- `dm.set_score <event_id> <team_name> <score>`: Set a team's score.\n"
                "- `dm.add_score <event_id> <team_name> <points>`: Add points to a team's score.\n"
                "- `dm.show_scores <event_id>`: Show all scores for an event."
            ),
            inline=False
        )
        embed.add_field(
            name="Stats & Profiles",
            value=(
                "- `dm.user_stats [@user]`: Show a user's event participation, team, and rank.\n"
                "- `dm.team_stats <event_id> <team_name>`: Show stats for a team.\n"
                "- `dm.server_stats`: Show server-wide stats and top users.\n"
                "- `dm.profile [@user]`: Show a user's profile."
            ),
            inline=False
        )
        embed.set_footer(text="For more help, contact a moderator.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot)) 