from discord.ext import commands
import discord
import database

DEFAULT_TEAM_EMOJIS = ["🦁", "🐯", "🐻", "🦊", "🐸", "🐼", "🐨", "🦄", "🐙", "🐵"]

class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.section_embeds = {}  # Store embed message IDs for each section
        self.team_channel_embeds = {}  # Store embed message IDs for team channel

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

    async def check_mod_channel(self, ctx):
        """Check if command is being used in the mod channel"""
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            await ctx.send("❌ Admin cog not available.")
            return False
        return await admin_cog.check_mod_channel(ctx)

    @commands.command(name="create_section_embed", usage="<event_id> <sect_name>")
    @commands.has_permissions(administrator=True)
    async def create_section_embed(self, ctx, event_id: int, sect_name: str):
        """Create an embed for a section that allows reaction-based team joining (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
        import database
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not admin_cog:
            await ctx.send("Required cogs not available.")
            return
            
        event = event_cog.events.get(event_id)
        section_found = False
        section_data = None
        # Check in memory first
        if event and sect_name in event.get('sections', {}):
            section_found = True
            section_data = event['sections'][sect_name]
        else:
            # Fallback: check DB for section
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, db_sect_name, _ = section
                if str(db_sect_name) == str(sect_name):
                    section_found = True
                    # Load teams from DB
                    teams = database.get_teams(section_id)
                    section_data = {'teams': {}}
                    for team in teams:
                        team_id, team_name, leader_id, max_members, emoji = team
                        members = database.get_team_members_by_id(team_id)
                        section_data['teams'][team_name] = {
                            'emoji': emoji,
                            'leader': f"<@{leader_id}>",
                            'max_members': max_members,
                            'members': [f"<@{uid}>" for uid in members]
                        }
                    break
        if not section_found:
            await ctx.send(f"Section '**{sect_name}**' not found in event ID `{event_id}`.")
            return
            
        team_channel_id = admin_cog.get_channel_id("team_channel")
        if not team_channel_id:
            await ctx.send("Team channel not configured. Use `dm.set_channel team #channel` first.")
            return
            
        team_channel = self.bot.get_channel(team_channel_id)
        if not team_channel:
            await ctx.send("Team channel not found.")
            return
            
        # Create embed
        embed = discord.Embed(
            title=f"📋 {sect_name}",
            description=f"React with the team emoji to join!",
            color=discord.Color.blue()
        )
        
        teams = section_data.get('teams', {}) if section_data else {}
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
        
        # Send embed and store message ID
        embed_message = await team_channel.send(embed=embed)
        section_key = f"{event_id}_{sect_name}"
        self.section_embeds[section_key] = embed_message.id
        
        # Add reactions for each team emoji
        for team in teams.values():
            emoji = team.get('emoji')
            if emoji:
                try:
                    await embed_message.add_reaction(emoji)
                except Exception as e:
                    print(f"Error adding reaction {emoji}: {e}")
        
        await ctx.send(f"✅ Created section embed for '**{sect_name}**' in {team_channel.mention}")
        await ctx.send(f"Users can now react to join teams in {team_channel.mention}")

    @commands.command(name="create_section", usage="<event_id> (sect_name/Max_team)")
    async def create_section(self, ctx, event_id: int, *, section_info: str):
        if not await self.check_mod_channel(ctx):
            return
            
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
        
        # Update event data in memory
        event_cog = self.bot.get_cog('Event')
        if event_cog and event_id in event_cog.events:
            if 'sections' not in event_cog.events[event_id]:
                event_cog.events[event_id]['sections'] = {}
            event_cog.events[event_id]['sections'][sect_name] = {
                'max_teams': max_team,
                'teams': {}
            }
        # Always update the join embed after creating a section
        if event_cog:
            await event_cog.update_event_embed(event_id)
        
        await ctx.send(f"Section created: **{sect_name}** (ID: `{section_id}`), Max Teams: {max_team}")

    @commands.command(name="create_team", usage="<section_id> (team_name/@leader/Max_member)")
    async def create_team(self, ctx, section_id: int, *, team_info: str):
        if not await self.check_mod_channel(ctx):
            return
            
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
        
        # Get section info to find event_id
        sections = database.get_sections(section_id)
        if not sections:
            await ctx.send(f"Section with ID `{section_id}` not found.")
            return
        
        # Find the event_id for this section
        event_cog = self.bot.get_cog('Event')
        event_id = None
        for event_id_check, event in event_cog.events.items():
            for sect_name, section in event.get('sections', {}).items():
                if section.get('section_id') == section_id:
                    event_id = event_id_check
                    break
            if event_id:
                break
        
        if not event_id:
            await ctx.send("Could not find event for this section.")
            return
        
        emoji = "⚔️"  # Default emoji, you can customize this
        team_id = database.add_team(section_id, team_name, leader_id, max_member, emoji)
        database.add_team_member(team_id, leader_id)
        
        # Update event data in memory
        if event_cog and event_id in event_cog.events:
            # Find the section name
            sect_name = None
            for sect_name_check, section in event_cog.events[event_id].get('sections', {}).items():
                if section.get('section_id') == section_id:
                    sect_name = sect_name_check
                    break
            
            if sect_name:
                if 'teams' not in event_cog.events[event_id]['sections'][sect_name]:
                    event_cog.events[event_id]['sections'][sect_name]['teams'] = {}
                
                event_cog.events[event_id]['sections'][sect_name]['teams'][team_name] = {
                    'emoji': emoji,
                    'leader': f"<@{leader_id}>",
                    'max_members': max_member,
                    'members': [f"<@{leader_id}>"]
                }
                
                # Update the event embed
                await event_cog.update_event_embed(event_id)
                
                # Update team channel embed
                await self.update_team_channel_embed(event_id)
        
        await ctx.send(f"Team created: **{team_name}** (ID: `{team_id}`), Leader: <@{leader_id}>, Max Members: {max_member}")

    @commands.command(name="join_team", usage="<team_name>")
    async def join_team(self, ctx, *, team_name: str):
        """Joins a team for an event."""
        # Note: join_team can be used in any channel, not just mod channel
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
        
        # Assign event role
        await self.assign_event_role(ctx.author, event_id)
        
        # Update team channel embed
        await self.update_team_channel_embed(event_id)
        
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
        
        # Check if this is a reaction in the join channel
        join_channel_id = admin_cog.get_channel_id("join")
        if not join_channel_id or reaction.message.channel.id != join_channel_id:
            return
            
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return
            
        # Check if this is an event embed
        event_id = None
        for eid, embed_id in event_cog.event_embeds.items():
            if embed_id == reaction.message.id:
                event_id = eid
                break
                
        if not event_id:
            return
            
        event = event_cog.events.get(event_id)
        if not event:
            return
            
        # Find the team by emoji
        team_found = False
        for sect_name, section in event.get('sections', {}).items():
            for team_name, team_data in section.get('teams', {}).items():
                if team_data.get('emoji') == str(reaction.emoji):
                    team_found = True
                    break
            if team_found:
                break
                
        if not team_found:
            await reaction.remove(user)
            return
            
        team = section['teams'][team_name]
        
        # Check if user is already in the team
        if user.mention in team['members']:
            await reaction.remove(user)
            return
            
        # Check if team is full
        if len(team['members']) >= team.get('max_members', float('inf')):
            await reaction.remove(user)
            return
            
        # Add user to team
        team['members'].append(user.mention)
        
        # Assign event role
        await self.assign_event_role(user, event_id)
        
        # Update the event embed
        await event_cog.update_event_embed(event_id)
        
        # Update team channel embed
        await self.update_team_channel_embed(event_id)
        
        # Send notifications
        await self.send_join_notifications(user, team_name, sect_name, event['name'], "joined", method="reaction")
        await self.send_log_message(user, team_name, sect_name, event['name'], "joined", method="reaction")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle team leaving via reactions"""
        if user.bot:
            return
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
        
        # Check if this is a reaction in the join channel
        join_channel_id = admin_cog.get_channel_id("join")
        if not join_channel_id or reaction.message.channel.id != join_channel_id:
            return
            
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return
            
        # Check if this is an event embed
        event_id = None
        for eid, embed_id in event_cog.event_embeds.items():
            if embed_id == reaction.message.id:
                event_id = eid
                break
                
        if not event_id:
            return
            
        event = event_cog.events.get(event_id)
        if not event:
            return
            
        # Find the team by emoji
        team_found = False
        for sect_name, section in event.get('sections', {}).items():
            for team_name, team_data in section.get('teams', {}).items():
                if team_data.get('emoji') == str(reaction.emoji):
                    team_found = True
                    break
            if team_found:
                break
                
        if not team_found:
            return
            
        team = section['teams'][team_name]
        
        # Remove user from team
        if user.mention in team['members']:
            team['members'].remove(user.mention)
            
            # Remove event role if user is not in any other team
            await self.remove_event_role(user, event_id)
            
            # Update the event embed
            await event_cog.update_event_embed(event_id)
            
            # Update team channel embed
            await self.update_team_channel_embed(event_id)
            
            # Send notifications
            await self.send_join_notifications(user, team_name, sect_name, event['name'], "left", method="reaction")
            await self.send_log_message(user, team_name, sect_name, event['name'], "left", method="reaction")

    @commands.command(name="delete_team", usage="<event_id> <sect_name> <team_name>")
    @commands.has_permissions(administrator=True)
    async def delete_team(self, ctx, event_id: int, sect_name: str, team_name: str):
        """Delete a team from a section (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
        import database
        event_cog = self.bot.get_cog('Event')
        event = event_cog.events.get(event_id) if event_cog else None
        team_found = False
        # Check in memory first
        if event and sect_name in event.get('sections', {}) and team_name in event['sections'][sect_name].get('teams', {}):
            team_found = True
        else:
            # Fallback: check DB for team
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, db_sect_name, _ = section
                if str(db_sect_name) == str(sect_name):
                    teams = database.get_teams(section_id)
                    for team in teams:
                        team_id, db_team_name, _, _, _ = team
                        if str(db_team_name) == str(team_name):
                            team_found = True
                            # Remove from DB
                            database.remove_team(team_id)
                            await ctx.send(f"Team '**{team_name}**' has been deleted from section '**{sect_name}**' in event ID `{event_id}` (DB fallback).")
                            # Optionally, reload event into memory
                            if event_cog:
                                await event_cog.cog_load()
                            return
        if not team_found:
            await ctx.send(f"Team '**{team_name}**' not found in section '**{sect_name}**' of event ID `{event_id}`.")
            return
        # Remove from memory if event is in memory
        if event:
            del event['sections'][sect_name]['teams'][team_name]
            # Update section embed if it exists
            await self.update_section_embed(event_id, sect_name)
            await ctx.send(f"Team '**{team_name}**' has been deleted from section '**{sect_name}**'.")

    @commands.command(name="delete_section", usage="<event_id> <sect_name>")
    @commands.has_permissions(administrator=True)
    async def delete_section(self, ctx, event_id: int, sect_name: str):
        """Delete a section from an event (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
        import database
        event_cog = self.bot.get_cog('Event')
        event = event_cog.events.get(event_id) if event_cog else None
        section_found = False
        # Check in memory first
        if event and sect_name in event.get('sections', {}):
            section_found = True
        else:
            # Fallback: check DB for section
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, db_sect_name, _ = section
                if str(db_sect_name) == str(sect_name):
                    section_found = True
                    # Remove from DB
                    database.remove_section(section_id)
                    await ctx.send(f"Section '**{sect_name}**' has been deleted from event ID `{event_id}` (DB fallback).")
                    # Optionally, reload event into memory
                    if event_cog:
                        await event_cog.cog_load()
                    return
        if not section_found:
            await ctx.send(f"Section '**{sect_name}**' not found in event ID `{event_id}`.")
            return
        # Remove from memory if event is in memory
        if event:
            del event['sections'][sect_name]
            # Remove section embed if it exists
            section_key = f"{event_id}_{sect_name}"
            if section_key in self.section_embeds:
                del self.section_embeds[section_key]
            # Update event embed
            await event_cog.update_event_embed(event_id)
            await ctx.send(f"Section '**{sect_name}**' has been deleted from event '**{event['name']}**'.")

    @commands.command(name="disqualify_team", usage="<event_id> <team_name> [reason]")
    @commands.has_permissions(administrator=True)
    async def disqualify_team(self, ctx, event_id: int, team_name: str, *, reason: str = "No reason provided"):
        """Disqualify a team from an event (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
        import database
        event_cog = self.bot.get_cog('Event')
        event = event_cog.events.get(event_id) if event_cog else None
        found_team = None
        found_section = None
        # Check in memory first
        if event:
            for sect_name, section in event.get('sections', {}).items():
                if team_name in section.get('teams', {}):
                    found_team = section['teams'][team_name]
                    found_section = sect_name
                    break
        else:
            # Fallback: check DB for team
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, db_sect_name, _ = section
                teams = database.get_teams(section_id)
                for team in teams:
                    team_id, db_team_name, _, _, _ = team
                    if str(db_team_name) == str(team_name):
                        found_section = str(db_sect_name)
                        # Remove all team members from DB
                        members = database.get_team_members_by_id(team_id)
                        for member_id in members:
                            database.remove_team_member(team_id, member_id)
                        await ctx.send(f"Team '**{team_name}**' has been disqualified from event ID `{event_id}` (DB fallback).\nReason: {reason}")
                        # Optionally, reload event into memory
                        if event_cog:
                            await event_cog.cog_load()
                        return
        if not found_team:
            await ctx.send(f"Team '**{team_name}**' not found in event ID `{event_id}`.")
            return
        # Remove all members from the team (memory)
        members_to_remove = found_team.get('members', []).copy()
        for member_mention in members_to_remove:
            # Extract user ID from mention
            if member_mention.startswith('<@') and member_mention.endswith('>'):
                user_id = int(member_mention.strip('<@!>'))
                # Remove from memory
                if member_mention in found_team['members']:
                    found_team['members'].remove(member_mention)
        # Send notification to all removed members
        for member_mention in members_to_remove:
            if member_mention.startswith('<@') and member_mention.endswith('>'):
                user_id = int(member_mention.strip('<@!>'))
                user = ctx.guild.get_member(user_id)
                if user and event:
                    await self.send_join_notifications(user, team_name, found_section, event['name'], "disqualified", "admin")
        # Update section embed
        await self.update_section_embed(event_id, found_section)
        if event:
            await ctx.send(f"Team '**{team_name}**' has been disqualified from event '**{event['name']}**'.\nReason: {reason}")

    @commands.command(name="disqualify_member", usage="<event_id> <@member> [reason]")
    @commands.has_permissions(administrator=True)
    async def disqualify_member(self, ctx, event_id: int, member_mention: str, *, reason: str = "No reason provided"):
        """Disqualify a member from all teams in an event (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
        import database
        # Extract user ID from mention
        if not member_mention.startswith('<@') or not member_mention.endswith('>'):
            await ctx.send("Please mention the member to disqualify.")
            return
        user_id = int(member_mention.strip('<@!>'))
        user = ctx.guild.get_member(user_id)
        if not user:
            await ctx.send("User not found in this server.")
            return
        event_cog = self.bot.get_cog('Event')
        event = event_cog.events.get(event_id) if event_cog else None
        removed_teams = []
        # Check in memory first
        if event:
            # Remove user from all teams in the event
            for sect_name, section in event.get('sections', {}).items():
                for team_name, team_data in section.get('teams', {}).items():
                    if member_mention in team_data.get('members', []):
                        # Remove from memory
                        team_data['members'].remove(member_mention)
                        removed_teams.append((team_name, sect_name))
        else:
            # Fallback: check DB for user participation
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, db_sect_name, _ = section
                teams = database.get_teams(section_id)
                for team in teams:
                    team_id, db_team_name, _, _, _ = team
                    members = database.get_team_members_by_id(team_id)
                    if user_id in members:
                        # Remove from DB
                        database.remove_team_member(team_id, user_id)
                        removed_teams.append((str(db_team_name), str(db_sect_name)))
            if removed_teams:
                await ctx.send(f"User {user.mention} has been disqualified from the following teams in event ID `{event_id}` (DB fallback): {', '.join([f"'{team_name}' ({sect_name})" for team_name, sect_name in removed_teams])}\nReason: {reason}")
                # Optionally, reload event into memory
                if event_cog:
                    await event_cog.cog_load()
                return
        if not removed_teams:
            await ctx.send(f"User {user.mention} is not a member of any team in event ID `{event_id}`.")
            return
        # Send notification to the user
        for team_name, sect_name in removed_teams:
            if event:
                await self.send_join_notifications(user, team_name, sect_name, event['name'], "disqualified", "admin")
        # Update all affected section embeds
        affected_sections = set(sect_name for _, sect_name in removed_teams)
        for sect_name in affected_sections:
            await self.update_section_embed(event_id, sect_name)
        teams_list = ", ".join([f"'{team_name}' ({sect_name})" for team_name, sect_name in removed_teams])
        if event:
            await ctx.send(f"User {user.mention} has been disqualified from the following teams in event '**{event['name']}**': {teams_list}\nReason: {reason}")

    @commands.command(name="list_teams", usage="<event_id>", help="List all teams for an event, with their members.")
    async def list_teams(self, ctx, event_id: int):
        """List all teams for an event, with their members."""
        if not await self.check_mod_channel(ctx):
            return
        import database
        event_cog = self.bot.get_cog('Event')
        event = event_cog.events.get(event_id) if event_cog else None
        event_name = None
        # Check in memory first
        if event:
            event_name = event['name']
        else:
            # Fallback: check DB for event
            db_event = database.get_event(event_id)
            if not db_event:
                await ctx.send(f"Event with ID `{event_id}` not found.")
                return
            event_name = db_event[2]  # type: ignore
            # Load teams from DB for display
            embed = discord.Embed(title=f"Teams for {event_name}", color=discord.Color.blue())
            sections = database.get_sections(event_id)
            for section in sections:
                section_id, sect_name, _ = section
                teams_text = ""
                teams = database.get_teams(section_id)
                for team in teams:
                    team_id, team_name, _, max_members, _ = team
                    members = database.get_team_members_by_id(team_id)
                    member_mentions = [f"<@{uid}>" for uid in members]
                    teams_text += f"**{team_name}** ({len(members)}/{max_members}): {', '.join(member_mentions) if member_mentions else 'No members'}\n"
                if teams_text:
                    embed.add_field(name=f"📋 {sect_name}", value=teams_text, inline=False)
            if not embed.fields:
                embed.description = "No teams found for this event."
            await ctx.send(embed=embed)
            return
        # Display teams from memory
        embed = discord.Embed(title=f"Teams for {event_name}", color=discord.Color.blue())
        for sect_name, section in event.get('sections', {}).items():
            teams_text = ""
            for team_name, team_data in section.get('teams', {}).items():
                members = team_data.get('members', [])
                teams_text += f"**{team_name}** ({len(members)}/{team_data.get('max_members', 0)}): {', '.join(members) if members else 'No members'}\n"
            if teams_text:
                embed.add_field(name=f"📋 {sect_name}", value=teams_text, inline=False)
        if not embed.fields:
            embed.description = "No teams found for this event."
        await ctx.send(embed=embed)

    @commands.command(name="delete_section_embed", usage="<event_id> <sect_name>")
    @commands.has_permissions(administrator=True)
    async def delete_section_embed(self, ctx, event_id: int, sect_name: str):
        """Delete a section embed (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
            
        section_key = f"{event_id}_{sect_name}"
        if section_key not in self.section_embeds:
            await ctx.send(f"No section embed found for section '**{sect_name}**' in event ID `{event_id}`.")
            return

        # Try to delete the message
        admin_cog = self.bot.get_cog('Admin')
        if admin_cog:
            team_channel_id = admin_cog.get_channel_id("team")
            if team_channel_id:
                team_channel = self.bot.get_channel(team_channel_id)
                if team_channel:
                    try:
                        message = await team_channel.fetch_message(self.section_embeds[section_key])
                        await message.delete()
                        await ctx.send(f"✅ Section embed for '**{sect_name}**' has been deleted.")
                    except discord.NotFound:
                        await ctx.send(f"⚠️ Section embed message not found, but removed from tracking.")
                    except Exception as e:
                        await ctx.send(f"❌ Error deleting section embed: {e}")
                else:
                    await ctx.send("❌ Team channel not found.")
            else:
                await ctx.send("❌ Team channel not configured.")
        else:
            await ctx.send("❌ Admin cog not available.")

        # Remove from tracking
        del self.section_embeds[section_key]

    @commands.command(name="list_section_embeds", usage="", help="List all section embeds and their status")
    async def list_section_embeds(self, ctx):
        """List all section embeds and their status"""
        if not await self.check_mod_channel(ctx):
            return
            
        if not self.section_embeds:
            await ctx.send("No section embeds are currently active.")
            return

        embed = discord.Embed(title="Section Embeds Status", color=discord.Color.blue())
        for section_key, message_id in self.section_embeds.items():
            event_id, sect_name = section_key.split('_', 1)
            embed.add_field(
                name=f"📋 {sect_name}",
                value=f"Event ID: {event_id}\nMessage ID: {message_id}",
                inline=True
            )
        await ctx.send(embed=embed)

    async def assign_event_role(self, user, event_id):
        """Assign event role to user when they join a team"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or event_id not in event_cog.events:
            return
            
        event = event_cog.events[event_id]
        role_id = event.get('role_id')
        if not role_id:
            return
            
        try:
            role = user.guild.get_role(role_id)
            if role and role not in user.roles:
                await user.add_roles(role, reason=f"Joined tournament: {event['name']}")
        except Exception as e:
            print(f"Error assigning event role: {e}")

    async def remove_event_role(self, user, event_id):
        """Remove event role from user when they leave all teams in an event"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or event_id not in event_cog.events:
            return
            
        event = event_cog.events[event_id]
        role_id = event.get('role_id')
        if not role_id:
            return
            
        # Check if user is still in any team in this event
        for sect_name, section in event.get('sections', {}).items():
            for team_name, team_data in section.get('teams', {}).items():
                if user.mention in team_data.get('members', []):
                    return  # User is still in a team, don't remove role
        
        # User is not in any team, remove role
        try:
            role = user.guild.get_role(role_id)
            if role and role in user.roles:
                await user.remove_roles(role, reason=f"Left all teams in tournament: {event['name']}")
        except Exception as e:
            print(f"Error removing event role: {e}")

    async def update_team_channel_embed(self, event_id):
        """Update the team channel embed with clickable teams"""
        event_cog = self.bot.get_cog('Event')
        admin_cog = self.bot.get_cog('Admin')
        
        if not event_cog or not admin_cog:
            return
            
        event = event_cog.events.get(event_id)
        if not event:
            return
            
        team_channel_id = admin_cog.get_channel_id("team")
        if not team_channel_id:
            return
            
        team_channel = self.bot.get_channel(team_channel_id)
        if not team_channel:
            return
            
        # Create or update the main tournament embed
        embed = discord.Embed(
            title=f"🏆 {event['name']}",
            description="Click on a team name to get details via DM!",
            color=discord.Color.blue()
        )
        
        for sect_name, section in event.get('sections', {}).items():
            teams_text = ""
            for team_name, team_data in section.get('teams', {}).items():
                members = team_data.get('members', [])
                teams_text += f"**{team_name}** ({len(members)}/{team_data.get('max_members', 0)})\n"
            
            if teams_text:
                embed.add_field(name=f"📋 {sect_name}", value=teams_text, inline=False)
        
        if not embed.fields:
            embed.description = "No teams created yet."
        
        # Store or update the embed message
        if not hasattr(self, 'team_channel_embeds'):
            self.team_channel_embeds = {}
        
        if event_id in self.team_channel_embeds:
            try:
                message = await team_channel.fetch_message(self.team_channel_embeds[event_id])
                await message.edit(embed=embed)
            except:
                # Message not found, create new one
                message = await team_channel.send(embed=embed)
                self.team_channel_embeds[event_id] = message.id
        else:
            message = await team_channel.send(embed=embed)
            self.team_channel_embeds[event_id] = message.id

    async def send_team_details_dm(self, user, event_id, team_name):
        """Send team details to user via DM"""
        event_cog = self.bot.get_cog('Event')
        if not event_cog or event_id not in event_cog.events:
            return
            
        event = event_cog.events[event_id]
        
        # Find the team
        for sect_name, section in event.get('sections', {}).items():
            if team_name in section.get('teams', {}):
                team_data = section['teams'][team_name]
                members = team_data.get('members', [])
                
                embed = discord.Embed(
                    title=f"👥 Team Details: {team_name}",
                    description=f"**Event:** {event['name']}\n**Section:** {sect_name}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Leader", value=team_data.get('leader', 'Unknown'), inline=True)
                embed.add_field(name="Members", value=f"{len(members)}/{team_data.get('max_members', 0)}", inline=True)
                embed.add_field(name="Team Members", value=", ".join(members) if members else "No members", inline=False)
                
                try:
                    await user.send(embed=embed)
                except:
                    # User has DMs disabled
                    pass
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle team name clicks in team channel"""
        if message.author.bot:
            return
            
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
            
        # Check if this is in the team channel
        team_channel_id = admin_cog.get_channel_id("team")
        if not team_channel_id or message.channel.id != team_channel_id:
            return
            
        # Check if the message is just a team name
        team_name = message.content.strip()
        if not team_name:
            return
            
        event_cog = self.bot.get_cog('Event')
        if not event_cog:
            return
            
        # Find the team across all events
        for event_id, event in event_cog.events.items():
            for sect_name, section in event.get('sections', {}).items():
                if team_name in section.get('teams', {}):
                    await self.send_team_details_dm(message.author, event_id, team_name)
                    # Delete the message to keep channel clean
                    try:
                        await message.delete()
                    except:
                        pass
                    return

async def setup(bot):
    await bot.add_cog(Team(bot)) 