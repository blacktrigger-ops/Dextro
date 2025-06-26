from discord.ext import commands
import discord
import database

DEFAULT_TEAM_EMOJIS = ["🦁", "🐯", "🐻", "🦊", "🐸", "🐼", "🐨", "🦄", "🐙", "🐵"]

class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.section_embeds = {}  # Store embed message IDs for each section

    async def send_join_notifications(self, user, team_name, sect_name, event_name, join_type="joined", method="command"):
        """Send DM to user when they join/leave a team"""
        try:
            embed = discord.Embed(
                title=f"Team {join_type.title()}",
                description=(
                    f"You have {join_type} **{team_name}**\n"
                    f"Section: **{sect_name}**\n"
                    f"Event: **{event_name}**\n"
                    f"Method: `{method}`"
                ),
                color=discord.Color.green() if join_type == "joined" else discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"If this wasn't you, contact a moderator.")
            await user.send(embed=embed)
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Error sending DM to {user.name}: {e}")

    async def send_log_message(self, user, team_name, sect_name, event_name, join_type="joined", method="command"):
        """Send log message to log channel for join/leave actions"""
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
        log_channel_id = admin_cog.get_channel_id("log_channel")
        if not log_channel_id:
            return
        log_channel = self.bot.get_channel(log_channel_id)
        if not log_channel:
            return
        embed = discord.Embed(
            title=f"Team {join_type.title()} ({method})",
            description=(
                f"**User:** {user.mention} (`{user}`)\n"
                f"**Team:** {team_name}\n"
                f"**Section:** {sect_name}\n"
                f"**Event:** {event_name}\n"
                f"**Action:** {join_type.title()}\n"
                f"**Method:** `{method}`"
            ),
            color=discord.Color.green() if join_type == "joined" else discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"User ID: {user.id}")
        await log_channel.send(embed=embed)

    async def update_section_embed(self, event_id, sect_name):
        """Updates the embed for a specific section"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not admin_cog:
            return
            
        event = event_cog.events.get(event_id)
        if not event or sect_name not in event.get('sections', {}):
            return
            
        section = event['sections'][sect_name]
        embed_message_id = self.section_embeds.get(f"{event_id}_{sect_name}")
        
        if not embed_message_id:
            return
            
        team_channel_id = admin_cog.get_channel_id("team_channel")
        if not team_channel_id:
            return
            
        team_channel = self.bot.get_channel(team_channel_id)
        if not team_channel:
            return
            
        try:
            embed_message = await team_channel.fetch_message(embed_message_id)
        except:
            return
            
        # Create updated embed
        embed = discord.Embed(
            title=f"📋 {sect_name}",
            color=discord.Color.blue()
        )
        
        teams = section.get('teams', {})
        if not teams:
            embed.description = "No teams created yet."
        else:
            for team_name, team_data in teams.items():
                emoji = team_data.get('emoji', '❓')
                leader = team_data.get('leader', 'Unknown')
                current_members = len(team_data.get('members', []))
                max_members = team_data.get('max_members', 0)
                embed.add_field(
                    name=f"{emoji} {team_name}",
                    value=f"**Leader:** {leader}\n**Members:** {current_members}/{max_members}",
                    inline=False
                )
        
        await embed_message.edit(embed=embed)
        # Add reactions for each team emoji
        try:
            for team in teams.values():
                emoji = team.get('emoji')
                if emoji:
                    await embed_message.add_reaction(emoji)
        except Exception:
            pass

    @commands.command(name="create_section", usage="<event_id> (sect_name/Max_team)")
    async def create_section(self, ctx, event_id: int, *, section_info: str):
        import re
        # Debug: print all events in DB for this guild
        all_events = database.list_events(ctx.guild.id)
        print(f"[DEBUG] All events in DB for guild {ctx.guild.id}: {all_events}")

        event = database.get_event(event_id)
        print(f"[DEBUG] Lookup for event_id {event_id}: {event}")
        if not event:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        match = re.match(r"\(([^/]+)/([0-9]+)\)", section_info.strip())
        if not match:
            await ctx.send("Invalid format. Use: (Section Name/Max Teams)")
            return
        sect_name, max_team = match.group(1).strip(), int(match.group(2))
        section_id = database.add_section(event_id, sect_name, max_team)
        await ctx.send(f"Section created: **{sect_name}** (ID: `{section_id}`), Max Teams: {max_team}")

    @commands.command(name="create_team", usage="<section_id> (team_name/@leader/Max_member)")
    async def create_team(self, ctx, section_id: int, *, team_info: str):
        import re
        match = re.match(r"\(([^/]+)/([^/]+)/([0-9]+)\)", team_info.strip())
        if not match:
            await ctx.send("Invalid format. Use: (Team Name/@Leader/Max Members)")
            return
        team_name, leader_mention, max_member = match.group(1).strip(), match.group(2).strip(), int(match.group(3))
        leader_id = None
        if leader_mention.startswith('<@') and leader_mention.endswith('>'):
            leader_id = int(leader_mention.strip('<@!>'))
        else:
            await ctx.send("Please mention the leader user.")
            return
        emoji = None  # You can add emoji selection logic here if needed
        team_id = database.add_team(section_id, team_name, leader_id, max_member, emoji)
        database.add_team_member(team_id, leader_id)
        await ctx.send(f"Team created: **{team_name}** (ID: `{team_id}`), Leader: <@{leader_id}>, Max Members: {max_member}")

    @commands.command(name="join_team", usage="<team_name>")
    async def join_team(self, ctx, *, team_name: str):
        """Joins a team for an event."""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return
        found_teams = []
        for event_id, event in event_cog.events.items():
            for sect_name, sect in event.get('sections', {}).items():
                if team_name in sect.get('teams', {}):
                    found_teams.append({'event_id': event_id, 'event_name': event['name'], 'section_name': sect_name})
        if not found_teams:
            await ctx.send(f"Team '**{team_name}**' not found.")
            return
        if len(found_teams) > 1:
            response = f"Found multiple teams with the name '**{team_name}**'. Please be more specific.\n"
            for team_info in found_teams:
                response += f"- Event: '**{team_info['event_name']}**' (`{team_info['event_id']}`), Section: '**{team_info['section_name']}**'\n"
            await ctx.send(response)
            return
        team_info = found_teams[0]
        event_id = team_info['event_id']
        sect_name = team_info['section_name']
        team = event_cog.events[event_id]['sections'][sect_name]['teams'][team_name]
        if ctx.author.mention in team['members']:
            await ctx.send(f"You are already in team '**{team_name}**'.")
            return
        if len(team['members']) >= team.get('max_members', float('inf')):
            await ctx.send(f"Team '**{team_name}**' is full (Max members: {team.get('max_members', 'unknown')}).")
            return
        team['members'].append(ctx.author.mention)
        await self.update_section_embed(event_id, sect_name)
        await self.send_join_notifications(ctx.author, team_name, sect_name, event_cog.events[event_id]['name'], "joined", method="command")
        await self.send_log_message(ctx.author, team_name, sect_name, event_cog.events[event_id]['name'], "joined", method="command")
        await ctx.send(f"You have joined team '**{team_name}**' in section '**{sect_name}**' for event '**{event_cog.events[event_id]['name']}**'.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle team joining via reactions"""
        if user.bot:
            return
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
        team_channel_id = admin_cog.get_channel_id("team_channel")
        if not team_channel_id or reaction.message.channel.id != team_channel_id:
            return
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return
        section_key = None
        for key, embed_id in self.section_embeds.items():
            if embed_id == reaction.message.id:
                section_key = key
                break
        if not section_key:
            return
        event_id, sect_name = section_key.split('_', 1)
        event_id = int(event_id)
        event = event_cog.events.get(event_id)
        if not event or sect_name not in event.get('sections', {}):
            return
        section = event['sections'][sect_name]
        emoji_to_team = {team_data.get('emoji'): name for name, team_data in section['teams'].items()}
        team_name = emoji_to_team.get(str(reaction.emoji))
        if not team_name:
            return
        team = section['teams'][team_name]
        if user.mention in team['members']:
            await reaction.remove(user)
            return
        if len(team['members']) >= team.get('max_members', float('inf')):
            await reaction.remove(user)
            return
        team['members'].append(user.mention)
        await self.send_join_notifications(user, team_name, sect_name, event['name'], "joined", method="reaction")
        await self.send_log_message(user, team_name, sect_name, event['name'], "joined", method="reaction")
        await self.update_section_embed(event_id, sect_name)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle team leaving via reactions"""
        if user.bot:
            return
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
        team_channel_id = admin_cog.get_channel_id("team_channel")
        if not team_channel_id or reaction.message.channel.id != team_channel_id:
            return
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return
        section_key = None
        for key, embed_id in self.section_embeds.items():
            if embed_id == reaction.message.id:
                section_key = key
                break
        if not section_key:
            return
        event_id, sect_name = section_key.split('_', 1)
        event_id = int(event_id)
        event = event_cog.events.get(event_id)
        if not event or sect_name not in event.get('sections', {}):
            return
        section = event['sections'][sect_name]
        emoji_to_team = {team_data.get('emoji'): name for name, team_data in section['teams'].items()}
        team_name = emoji_to_team.get(str(reaction.emoji))
        if not team_name:
            return
        team = section['teams'][team_name]
        if user.mention in team['members']:
            team['members'].remove(user.mention)
            await self.send_join_notifications(user, team_name, sect_name, event['name'], "left", method="reaction")
            await self.send_log_message(user, team_name, sect_name, event['name'], "left", method="reaction")
            await self.update_section_embed(event_id, sect_name)

    @commands.command(name="delete_team", usage="<event_id> <sect_name> <team_name>")
    @commands.has_permissions(administrator=True)
    async def delete_team(self, ctx, event_id: int, sect_name: str, team_name: str):
        """Deletes a team from a section (Admin only)"""
        event_cog = self.bot.get_cog('Event')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]

        if sect_name not in event.get('sections', {}):
            await ctx.send(f"Section '**{sect_name}**' not found in event '**{event['name']}**'.")
            return

        section = event['sections'][sect_name]

        if team_name not in section.get('teams', {}):
            await ctx.send(f"Team '**{team_name}**' not found in section '**{sect_name}**'.")
            return

        # Delete the team
        del section['teams'][team_name]
        
        # Update the section embed
        await self.update_section_embed(event_id, sect_name)
        
        # Remove from leaderboard if exists
        leaderboard_cog = self.bot.get_cog('Leaderboard')
        if leaderboard_cog and event_id in leaderboard_cog.scores:
            if team_name in leaderboard_cog.scores[event_id]:
                del leaderboard_cog.scores[event_id][team_name]
                await leaderboard_cog.update_leaderboard_embed(event_id)
        
        await ctx.send(f"Team '**{team_name}**' has been deleted from section '**{sect_name}**' in event '**{event['name']}**'.")

    @commands.command(name="delete_section", usage="<event_id> <sect_name>")
    @commands.has_permissions(administrator=True)
    async def delete_section(self, ctx, event_id: int, sect_name: str):
        """Deletes an entire section and all its teams (Admin only)"""
        event_cog = self.bot.get_cog('Event')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]

        if sect_name not in event.get('sections', {}):
            await ctx.send(f"Section '**{sect_name}**' not found in event '**{event['name']}**'.")
            return

        # Delete the section
        del event['sections'][sect_name]
        
        # Remove section embed
        section_key = f"{event_id}_{sect_name}"
        if section_key in self.section_embeds:
            del self.section_embeds[section_key]
        
        # Remove teams from leaderboard if exists
        leaderboard_cog = self.bot.get_cog('Leaderboard')
        if leaderboard_cog and event_id in leaderboard_cog.scores:
            teams_to_remove = []
            for team_name in leaderboard_cog.scores[event_id].keys():
                team_details = leaderboard_cog.get_team_details(event_id, team_name)
                if team_details and team_details['section'] == sect_name:
                    teams_to_remove.append(team_name)
            
            for team_name in teams_to_remove:
                del leaderboard_cog.scores[event_id][team_name]
            
            if teams_to_remove:
                await leaderboard_cog.update_leaderboard_embed(event_id)
        
        await ctx.send(f"Section '**{sect_name}**' and all its teams have been deleted from event '**{event['name']}**'.")

    @commands.command(name="disqualify_team", usage="<event_id> <team_name> [reason]")
    @commands.has_permissions(administrator=True)
    async def disqualify_team(self, ctx, event_id: int, team_name: str, *, reason: str = "No reason provided"):
        """Disqualifies a team from an event (Admin only)"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        
        # Find the team
        team_found = False
        sect_name = None
        for sect, section in event.get('sections', {}).items():
            if team_name in section.get('teams', {}):
                team_found = True
                sect_name = sect
                break
        
        if not team_found:
            await ctx.send(f"Team '**{team_name}**' not found in event '**{event['name']}**'.")
            return

        # Remove team from section
        del event['sections'][sect_name]['teams'][team_name]
        
        # Update section embed
        await self.update_section_embed(event_id, sect_name)
        
        # Remove from leaderboard if exists
        leaderboard_cog = self.bot.get_cog('Leaderboard')
        if leaderboard_cog and event_id in leaderboard_cog.scores:
            if team_name in leaderboard_cog.scores[event_id]:
                del leaderboard_cog.scores[event_id][team_name]
                await leaderboard_cog.update_leaderboard_embed(event_id)
        
        # Send log message
        log_channel_id = admin_cog.get_channel_id("log_channel")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="🚫 Team Disqualified",
                    description=f"**{team_name}** has been disqualified from event **{event['name']}**\n**Reason:** {reason}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Disqualified by {ctx.author.name}")
                await log_channel.send(embed=embed)
        
        await ctx.send(f"Team '**{team_name}**' has been disqualified from event '**{event['name']}**'. Reason: {reason}")

    @commands.command(name="disqualify_member", usage="<event_id> <@member> [reason]")
    @commands.has_permissions(administrator=True)
    async def disqualify_member(self, ctx, event_id: int, member_mention: str, *, reason: str = "No reason provided"):
        """Disqualifies a member from all teams in an event (Admin only)"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return

        if event_id not in event_cog.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = event_cog.events[event_id]
        
        # Find and remove member from all teams
        removed_from_teams = []
        for sect_name, section in event.get('sections', {}).items():
            for team_name, team in section.get('teams', {}).items():
                if member_mention in team.get('members', []):
                    team['members'].remove(member_mention)
                    removed_from_teams.append(f"{team_name} ({sect_name})")
        
        if not removed_from_teams:
            await ctx.send(f"Member {member_mention} not found in any team in event '**{event['name']}**'.")
            return
        
        # Update all section embeds
        for sect_name in event.get('sections', {}).keys():
            await self.update_section_embed(event_id, sect_name)
        
        # Send log message
        log_channel_id = admin_cog.get_channel_id("log_channel")
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="🚫 Member Disqualified",
                    description=f"{member_mention} has been disqualified from event **{event['name']}**\n**Reason:** {reason}\n**Removed from teams:** {', '.join(removed_from_teams)}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Disqualified by {ctx.author.name}")
                await log_channel.send(embed=embed)
        
        await ctx.send(f"Member {member_mention} has been disqualified from event '**{event['name']}**'. Removed from teams: {', '.join(removed_from_teams)}")

    @commands.command(name="list_teams", usage="<event_id>", help="List all teams for an event, with their members.")
    async def list_teams(self, ctx, event_id: int):
        event_cog = self.bot.get_cog('Event')
        if not event_cog or not hasattr(event_cog, 'events'):
            await ctx.send("Event data is not available.")
            return
        event = event_cog.events.get(event_id)
        if not event:
            await ctx.send("Event not found.")
            return
        if not event.get('sections'):
            await ctx.send("No sections/teams found for this event.")
            return
        embed = discord.Embed(title=f"Teams for Event: {event['name']} (ID: {event_id})", color=discord.Color.blue())
        for sect_name, section in event['sections'].items():
            for team_name, team in section['teams'].items():
                members = ', '.join(team['members']) if team['members'] else 'No members yet'
                embed.add_field(name=f"{team_name} (Section: {sect_name})", value=members, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Team(bot)) 