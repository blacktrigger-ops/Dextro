import discord
from discord.ext import commands
import database
from typing import Optional
from database import fetch_user_stats

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="user_stats", usage="[@user]", help="Show event participation, team, and rank for a user (default: yourself)")
    async def user_stats(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        participations = database.get_user_event_participation(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"Event Stats for {member.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        if not participations:
            embed.description = "No event participation recorded."
        else:
            for event_id, team_name in participations:
                team, rank = database.get_user_event_rank(ctx.guild.id, event_id, member.id)
                value = f"Team: {team_name or 'N/A'}\nRank: {rank if rank is not None else 'N/A'}"
                embed.add_field(name=f"Event ID: {event_id}", value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="team_stats", usage="<event_id> <team_name>", help="Show team stats for an event (score, rank, members)")
    async def team_stats(self, ctx, event_id: int, *, team_name: str):
        stats = database.get_team_stats(ctx.guild.id, event_id, team_name)
        if not stats:
            await ctx.send("Team or event not found.")
            return
        score, rank = stats
        member_ids = database.get_team_members(ctx.guild.id, event_id, team_name)
        members = []
        for uid in member_ids:
            member = ctx.guild.get_member(uid)
            members.append(member.mention if member else f"User {uid}")
        embed = discord.Embed(title=f"Team: {team_name} (Event ID: {event_id})", color=discord.Color.green())
        embed.add_field(name="Score", value=str(score), inline=True)
        embed.add_field(name="Rank", value=str(rank) if rank is not None else "N/A", inline=True)
        embed.add_field(name="Members", value=", ".join(members) if members else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="server_stats", help="Show server-wide event/team/member stats and top users")
    async def server_stats(self, ctx):
        stats = database.get_server_stats(ctx.guild.id)
        embed = discord.Embed(title=f"Server Stats for {ctx.guild.name}", color=discord.Color.green())
        if not stats:
            embed.description = "No server stats recorded yet."
        else:
            events, teams, members = stats
            embed.add_field(name="Events Created", value=str(events), inline=True)
            embed.add_field(name="Teams Created", value=str(teams), inline=True)
            embed.add_field(name="Members Joined", value=str(members), inline=True)
        # Top 5 users by command usage
        with database.get_db() as conn:
            c = conn.cursor()
            c.execute('''SELECT user_id, SUM(count) as total FROM user_usage WHERE guild_id = ? GROUP BY user_id ORDER BY total DESC LIMIT 5''', (ctx.guild.id,))
            top_users = c.fetchall()
        if top_users:
            desc = ""
            for uid, total in top_users:
                member = ctx.guild.get_member(uid)
                name = member.display_name if member else f"User {uid}"
                desc += f"**{name}**: {total} commands\n"
            embed.add_field(name="Top Users", value=desc, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="profile", usage="[@user]", help="Show user profile: events, rank, team, etc.")
    async def profile(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        stats = fetch_user_stats(member.id, ctx.guild.id)
        embed = discord.Embed(title=f"Profile: {member.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        if not stats:
            embed.description = "No profile data recorded. Participate in events to get started!"
        else:
            events_participated, rank, team_id = stats
            embed.add_field(name="Events Participated", value=str(events_participated), inline=True)
            embed.add_field(name="Rank", value=str(rank) if rank else "N/A", inline=True)
            if team_id:
                embed.add_field(name="Current Team ID", value=str(team_id), inline=True)
            else:
                embed.add_field(name="Current Team", value="N/A", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot)) 