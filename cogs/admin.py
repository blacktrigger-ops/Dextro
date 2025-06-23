import discord
from discord.ext import commands
import database

class Admin(commands.Cog):
    """Commands for bot administration and configuration."""
    def __init__(self, bot):
        self.bot = bot

    def get_channel_id(self, channel_name, guild_id=None):
        # channel_name: mod_channel, event_channel, team_channel, log_channel
        if guild_id is None:
            return None
        return database.get_channel(guild_id, channel_name)

    @commands.command(name="set_mod_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_mod_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for moderator commands."""
        database.set_channel(ctx.guild.id, "mod_channel", channel.id)
        await ctx.send(f"Moderator channel set to {channel.mention}")

    @commands.command(name="set_event_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_event_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for event announcements."""
        database.set_channel(ctx.guild.id, "event_channel", channel.id)
        await ctx.send(f"Event channel set to {channel.mention}")

    @commands.command(name="set_team_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_team_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for team joining and management."""
        database.set_channel(ctx.guild.id, "team_channel", channel.id)
        await ctx.send(f"Team channel set to {channel.mention}")

    @commands.command(name="set_log_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for bot logs."""
        database.set_channel(ctx.guild.id, "log_channel", channel.id)
        await ctx.send(f"Log channel set to {channel.mention}")

    @commands.command(name="show_channels")
    async def show_channels(self, ctx):
        """Shows the currently configured channels."""
        embed = discord.Embed(title="Configured Channels", color=discord.Color.og_blurple())
        for name in ["mod_channel", "event_channel", "team_channel", "log_channel"]:
            channel_id = database.get_channel(ctx.guild.id, name)
            channel_mention = f"<#{channel_id}>" if channel_id else "Not set"
            embed.add_field(name=name.replace('_', ' ').title(), value=channel_mention, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot)) 