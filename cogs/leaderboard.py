import discord
from discord.ext import commands
from database import get_leaderboard, get_team_info, get_team_members_by_id

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_embeds = {}  # Store embed message IDs for each event
        self.scores = {}  # Store scores: {event_id: {team_name: score}}

    async def update_leaderboard_embed(self, event_id):
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
            
        event_channel_id = admin_cog.get_channel_id("event_channel")
        if not event_channel_id:
            return
            
        event_channel = self.bot.get_channel(event_channel_id)
        if not event_channel:
            return
            
        try:
            embed_message = await event_channel.fetch_message(embed_message_id)
        except:
            return
            
        # Create updated leaderboard embed
        embed = discord.Embed(
            title=f"🏆 Leaderboard - {event['name']}",
            color=discord.Color.gold()
        )
        
        event_scores = self.scores.get(event_id, {})
        
        if not event_scores:
            embed.description = "No scores recorded yet."
        else:
            # Sort teams by score (highest first)
            sorted_teams = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)
            
            for i, (team_name, score) in enumerate(sorted_teams, 1):
                # Find team details
                team_details = self.get_team_details(event_id, team_name)
                if team_details:
                    sect_name = team_details['section']
                    leader = team_details['leader']
                    member_count = team_details['member_count']
                    max_members = team_details['max_members']
                    
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
                        value=f"**Score:** {score}\n**Section:** {sect_name}\n**Leader:** {leader}\n**Members:** {member_count}/{max_members}",
                        inline=False
                    )
        
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        await embed_message.edit(embed=embed)

    def get_team_details(self, event_id, team_name):
        """Get team details from event data"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return None
            
        event = event_cog.events.get(event_id)
        if not event:
            return None
            
        for sect_name, section in event.get('sections', {}).items():
            if team_name in section.get('teams', {}):
                team = section['teams'][team_name]
                return {
                    'section': sect_name,
                    'leader': team.get('leader', 'Unknown'),
                    'member_count': len(team.get('members', [])),
                    'max_members': team.get('max_members', 0)
                }
        return None

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
        event_channel_id = admin_cog.get_channel_id("event_channel")
        if not event_channel_id:
            await ctx.send("Event channel not configured. Use `dm.set_event_channel` first.")
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
        self.scores[event_id] = {}
        
        await ctx.send(f"Leaderboard created for event '**{event['name']}**' in {event_channel.mention}")

    @commands.command(name="set_score", usage="<event_id> <team_name> <score>")
    async def set_score(self, ctx, event_id: int, team_name: str, score: int):
        """Sets the score for a team manually"""
        event_cog = self.bot.get_cog('Event')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        
        # Check if team exists
        team_found = False
        for sect_name, section in event.get('sections', {}).items():
            if team_name in section.get('teams', {}):
                team_found = True
                break
        
        if not team_found:
            await ctx.send(f"Team '**{team_name}**' not found in event '**{event['name']}**'.")
            return
        
        # Check if leaderboard exists
        if event_id not in self.leaderboard_embeds:
            await ctx.send(f"Leaderboard for event '**{event['name']}**' not found. Create it first with `dm.create_leaderboard {event_id}`")
            return
        
        # Set the score
        if event_id not in self.scores:
            self.scores[event_id] = {}
        
        self.scores[event_id][team_name] = score
        
        # Update the leaderboard embed
        await self.update_leaderboard_embed(event_id)
        
        await ctx.send(f"Score for team '**{team_name}**' set to **{score}** in event '**{event['name']}**'")

    @commands.command(name="add_score", usage="<event_id> <team_name> <points>")
    async def add_score(self, ctx, event_id: int, team_name: str, points: int):
        """Adds points to a team's current score"""
        event_cog = self.bot.get_cog('Event')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        
        # Check if team exists
        team_found = False
        for sect_name, section in event.get('sections', {}).items():
            if team_name in section.get('teams', {}):
                team_found = True
                break
        
        if not team_found:
            await ctx.send(f"Team '**{team_name}**' not found in event '**{event['name']}**'.")
            return
        
        # Check if leaderboard exists
        if event_id not in self.leaderboard_embeds:
            await ctx.send(f"Leaderboard for event '**{event['name']}**' not found. Create it first with `dm.create_leaderboard {event_id}`")
            return
        
        # Add to the score
        if event_id not in self.scores:
            self.scores[event_id] = {}
        
        current_score = self.scores[event_id].get(team_name, 0)
        new_score = current_score + points
        self.scores[event_id][team_name] = new_score
        
        # Update the leaderboard embed
        await self.update_leaderboard_embed(event_id)
        
        await ctx.send(f"Added **{points}** points to team '**{team_name}**'. New score: **{new_score}**")

    @commands.command(name="show_scores", usage="<event_id>")
    async def show_scores(self, ctx, event_id: int):
        """Shows all scores for an event"""
        event_cog = self.bot.get_cog('Event')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        event_scores = self.scores.get(event_id, {})
        
        if not event_scores:
            await ctx.send(f"No scores recorded for event '**{event['name']}**' yet.")
            return
        
        embed = discord.Embed(
            title=f"📊 Scores - {event['name']}",
            color=discord.Color.blue()
        )
        
        for team_name, score in event_scores.items():
            team_details = self.get_team_details(event_id, team_name)
            if team_details:
                embed.add_field(
                    name=team_name,
                    value=f"**Score:** {score}\n**Section:** {team_details['section']}",
                    inline=True
                )
        
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", usage="<event_id>", help="Show advanced leaderboard for an event.")
    async def leaderboard(self, ctx, event_id: int):
        # Get leaderboard from DB
        leaderboard = get_leaderboard(event_id)
        if not leaderboard:
            await ctx.send("No leaderboard data found for this event.")
            return
        embed = discord.Embed(title=f"🏆 Leaderboard - Event {event_id}", color=discord.Color.gold())
        for i, (team_id, score) in enumerate(leaderboard, 1):
            team = get_team_info(team_id)
            if not team:
                continue
            team_name = team['name']
            section_id = team['section_id']
            leader_id = team['leader_id']
            max_members = team['max_members']
            # Get members
            member_ids = get_team_members_by_id(team_id)
            members = []
            for uid in member_ids:
                member = ctx.guild.get_member(uid)
                members.append(member.mention if member else f"User {uid}")
            # Medal emoji
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            embed.add_field(
                name=f"{medal}#{i} {team_name}",
                value=f"**Score:** {score}\n**Section ID:** {section_id}\n**Leader:** <@{leader_id}>\n**Members:** {len(members)}/{max_members}\n{', '.join(members)}",
                inline=False
            )
        embed.set_footer(text=f"Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot)) 