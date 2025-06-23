import discord
from discord.ext import commands
import database
from typing import Optional

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="user_stats", usage="[@user]", help="Show command usage stats for a user (default: yourself)")
    async def user_stats(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        stats = database.get_user_stats(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"User Stats for {member.display_name}", color=discord.Color.blurple())
        if not stats:
            embed.description = "No command usage recorded."
        else:
            for command, count in stats:
                embed.add_field(name=command, value=f"Used {count} times", inline=True)
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

async def setup(bot):
    await bot.add_cog(Stats(bot)) 