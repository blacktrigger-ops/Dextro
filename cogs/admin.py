from typing import Dict, Optional
import discord
from discord.ext import commands

class Admin(commands.Cog):
    """Commands for bot administration and configuration."""
    def __init__(self, bot):
        self.bot = bot
        self.channels: Dict[str, Optional[int]] = {
            "mod_channel": None,
            "event_channel": None,
            "team_channel": None,
            "log_channel": None
        }

    def get_channel_id(self, channel_name):
        return self.channels.get(channel_name)

    @commands.command(name="set_mod_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_mod_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for moderator commands."""
        self.channels["mod_channel"] = channel.id
        await ctx.send(f"Moderator channel set to {channel.mention}")

    @commands.command(name="set_event_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_event_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for event announcements."""
        self.channels["event_channel"] = channel.id
        await ctx.send(f"Event channel set to {channel.mention}")

    @commands.command(name="set_team_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_team_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for team joining and management."""
        self.channels["team_channel"] = channel.id
        await ctx.send(f"Team channel set to {channel.mention}")

    @commands.command(name="set_log_channel", usage="<#channel>")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Sets the channel for bot logs."""
        self.channels["log_channel"] = channel.id
        await ctx.send(f"Log channel set to {channel.mention}")

    @commands.command(name="show_channels")
    async def show_channels(self, ctx):
        """Shows the currently configured channels."""
        embed = discord.Embed(title="Configured Channels", color=discord.Color.og_blurple())
        for name, channel_id in self.channels.items():
            channel_mention = f"<#{channel_id}>" if channel_id else "Not set"
            embed.add_field(name=name.replace('_', ' ').title(), value=channel_mention, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot)) 