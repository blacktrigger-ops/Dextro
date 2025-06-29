# cogs/leaderboard.py (rebuilt version)
import discord
from discord.ext import commands
import database
from typing import List, Tuple, Optional, Dict, Any

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_embeds: Dict[int, int] = {}  # Store embed message IDs for each event

    def _get_section_name_for_team(self, event_id: int, team_id: int) -> str:
        """Helper function to get section name for a team"""
        try:
            sections = database.get_sections(event_id)
            for section in sections:
                section_id = section[0]  # section_id is first element
                teams = database.get_teams(section_id)
                for team in teams:
                    if team[0] == team_id:  # team_id is first element
                        return section[1]  # section name is second element
        except Exception:
            pass
        return "Unknown"

    def _find_team_id_by_name(self, event_id: int, team_name: str) -> Optional[int]:
        """Helper function to find team_id by team name"""
        try:
            sections = database.get_sections(event_id)
            for section in sections:
                section_id = section[0]  # section_id is first element
                teams = database.get_teams(section_id)
                for team in teams:
                    if team[1] == team_name:  # team[1] is team name
                        return team[0]  # team[0] is team_id
        except Exception:
            pass
        return None

    async def update_leaderboard_embed(self, event_id: int) -> None:
        """Updates the leaderboard embed for a specific event"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not admin_cog:
            return
            
        event = event_cog.events.get(event_id)
        if not event:
            return
            
        embed_message_id = self.leaderboard_embeds.get(event_id)
        if not embed_message_id:
            return
            
        event_channel_id = admin_cog.get_channel_id("event")
        if not event_channel_id:
            return
            
        event_channel = self.bot.get_channel(event_channel_id)
        if not event_channel:
            return
            
        try:
            embed_message = await event_channel.fetch_message(embed_message_id)
        except Exception:
            return
            
        # Create updated leaderboard embed
        embed = discord.Embed(
            title=f"🏆 Leaderboard - {event['name']}",
            color=discord.Color.gold()
        )
        
        # Use database-backed leaderboard
        try:
            db_scores = database.get_leaderboard(event_id)
            if not db_scores:
                embed.description = "No scores recorded yet."
            else:
                # Sort teams by score (already sorted in SQL)
                for i, score_data in enumerate(db_scores, 1):
                    team_id, score = score_data
                    team_details = database.get_team_info(team_id)
                    if team_details:
                        team_name = team_details['name']
                        leader_id = team_details['leader']
                        max_members = team_details['max_members']
                        
                        # Get member count
                        try:
                            member_count = len(database.get_team_members_by_id(team_id))
                        except Exception:
                            member_count = 0
                        
                        # Get section info
                        section_name = self._get_section_name_for_team(event_id, team_id)
                        
                        # Add medal emojis for top 3
                        medal = ""
                        if i == 1:
                            medal = "🥇 "
                        elif i == 2:
                            medal = "🥈 "
                        elif i == 3:
                            medal = "🥉 "
                        
                        embed.add_field(
                            name=f"{medal}#{i} {team_name}",
                            value=f"**Score:** {score}\n**Section:** {section_name}\n**Leader:** <@{leader_id}>\n**Members:** {member_count}/{max_members}",
                            inline=False
                        )
        except Exception as e:
            embed.description = f"Error loading scores: {str(e)}"
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        await embed_message.edit(embed=embed)

    @commands.command(name="create_leaderboard", usage="<event_id>")
    async def create_leaderboard(self, ctx, event_id: int):
        """Creates a leaderboard for an event"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        
        # Check if leaderboard already exists
        if event_id in self.leaderboard_embeds:
            await ctx.send(f"Leaderboard for event '**{event['name']}**' already exists.")
            return
        
        # Send leaderboard embed to event channel
        event_channel_id = admin_cog.get_channel_id("event")
        if not event_channel_id:
            await ctx.send("Event channel not configured. Use `dm.set_channel event #channel` first.")
            return
            
        event_channel = self.bot.get_channel(event_channel_id)
        if not event_channel:
            await ctx.send("Event channel not found.")
            return
            
        embed = discord.Embed(
            title=f"🏆 Leaderboard - {event['name']}",
            description="No scores recorded yet.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        embed_message = await event_channel.send(embed=embed)
        self.leaderboard_embeds[event_id] = embed_message.id
        
        await ctx.send(f"Leaderboard created for event '**{event['name']}**' in {event_channel.mention}")

    @commands.command(name="set_score", usage="<event_id> <team_name> <score>")
    async def set_score(self, ctx, event_id: int, team_name: str, score: int):
        """Sets the score for a team manually (database-backed)"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return
        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return
            
        # Find team_id by event_id and team_name
        team_id = self._find_team_id_by_name(event_id, team_name)
        if not team_id:
            await ctx.send(f"Team '**{team_name}**' not found in event '**{event_cog.events[event_id]['name']}**'.")
            return
            
        try:
            database.set_leaderboard_score(event_id, team_id, score)
            await self.update_leaderboard_embed(event_id)
            await ctx.send(f"Score for team '**{team_name}**' set to **{score}** in event '**{event_cog.events[event_id]['name']}**'")
        except Exception as e:
            await ctx.send(f"Error setting score: {str(e)}")

    @commands.command(name="add_score", usage="<event_id> <team_name> <points>")
    async def add_score(self, ctx, event_id: int, team_name: str, points: int):
        """Adds points to a team's current score (database-backed)"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return
        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return
            
        # Find team_id by event_id and team_name
        team_id = self._find_team_id_by_name(event_id, team_name)
        if not team_id:
            await ctx.send(f"Team '**{team_name}**' not found in event '**{event_cog.events[event_id]['name']}**'.")
            return
            
        try:
            # Get current score
            leaderboard_data = database.get_leaderboard(event_id)
            leaderboard = {tid: s for tid, s in leaderboard_data}
            current_score = leaderboard.get(team_id, 0)
            new_score = current_score + points
            database.set_leaderboard_score(event_id, team_id, new_score)
            await self.update_leaderboard_embed(event_id)
            await ctx.send(f"Added **{points}** points to team '**{team_name}**'. New score: **{new_score}**")
        except Exception as e:
            await ctx.send(f"Error adding score: {str(e)}")

    @commands.command(name="show_scores", usage="<event_id>")
    async def show_scores(self, ctx, event_id: int):
        """Shows all scores for an event (database-backed)"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return
        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return
            
        event = event_cog.events[event_id]
        try:
            db_scores = database.get_leaderboard(event_id)
            if not db_scores:
                await ctx.send(f"No scores recorded for event '**{event['name']}**' yet.")
                return
                
            embed = discord.Embed(
                title=f"📊 Scores - {event['name']}",
                color=discord.Color.blue()
            )
            
            for score_data in db_scores:
                team_id, score = score_data
                team_details = database.get_team_info(team_id)
                if team_details:
                    # Get section name
                    section_name = self._get_section_name_for_team(event_id, team_id)
                    
                    embed.add_field(
                        name=team_details['name'],
                        value=f"**Score:** {score}\n**Section:** {section_name}",
                        inline=True
                    )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error showing scores: {str(e)}")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot)) 