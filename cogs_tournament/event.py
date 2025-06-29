from discord.ext import commands
import discord
import re
import database

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events = {}
        self.next_event_id = 1
        print('[DEBUG] Event cog initialized')

    async def check_mod_channel(self, ctx):
        """Check if command is being used in the mod channel"""
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            await ctx.send("❌ Admin cog not available.")
            return False
        return await admin_cog.check_mod_channel(ctx)

    @commands.command(name="create_event", usage="(event_name/Max_sect)", help="Create a new event.")
    async def create_event(self, ctx, *, event_info: str):
        if not await self.check_mod_channel(ctx):
            return
        print('[DEBUG] create_event called')
        match = re.match(r"\(([^/]+)/([0-9]+)\)", event_info.strip())
        if not match:
            await ctx.send("Invalid format! Use: (Event Name/Max Sections)")
            return
        name, max_sections = match.group(1).strip(), int(match.group(2))
        # Duplicate event name check
        existing_events = database.list_events(ctx.guild.id)
        for eid, ename, _ in existing_events:
            if isinstance(ename, str) and ename.lower() == name.lower():
                await ctx.send(f"❌ An event with the name **{name}** already exists (ID: {eid}).")
                return
        event_id = database.add_event(ctx.guild.id, name, max_sections)
        self.events[event_id] = {
            'name': name,
            'max_sections': max_sections,
            'sections': {}
        }
        role_name = f"🏆 {name}"
        try:
            event_role = await ctx.guild.create_role(
                name=role_name,
                color=discord.Color.gold(),
                reason=f"Auto-created role for tournament: {name}"
            )
            self.events[event_id]['role_id'] = event_role.id
        except Exception as e:
            await ctx.send(f"⚠️ Could not create event role: {e}")
            event_role = None
        admin_cog = self.bot.get_cog('Admin')
        game_channel = None
        if admin_cog:
            mod_channel_id = admin_cog.get_channel_id("mod", ctx.guild.id)
            if mod_channel_id:
                mod_channel = ctx.guild.get_channel(mod_channel_id)
                if mod_channel and mod_channel.category:
                    try:
                        game_channel = await ctx.guild.create_text_channel(
                            name=f"🎮 {name.lower().replace(' ', '-')}",
                            category=mod_channel.category,
                            reason=f"Auto-created game channel for tournament: {name}"
                        )
                        self.events[event_id]['game_channel_id'] = game_channel.id
                        if event_role:
                            await game_channel.set_permissions(event_role, 
                                read_messages=True, 
                                send_messages=True,
                                reason=f"Granting access to {name} participants"
                            )
                        await game_channel.set_permissions(ctx.guild.default_role, 
                            read_messages=False, 
                            send_messages=False,
                            reason="Restricting access to tournament participants only"
                        )
                    except Exception as e:
                        await ctx.send(f"⚠️ Could not create game channel: {e}")
        if admin_cog:
            event_channel_id = admin_cog.get_channel_id("event", ctx.guild.id)
            if event_channel_id:
                event_channel = self.bot.get_channel(event_channel_id)
                if event_channel:
                    embed = discord.Embed(
                        title=f"🎯 Tournament Announcement: {name}",
                        description=f"A new tournament has been created!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Event ID", value=str(event_id), inline=True)
                    embed.add_field(name="Max Sections", value=str(max_sections), inline=True)
                    embed.add_field(name="Status", value="🟡 Open for Registration", inline=True)
                    if event_role:
                        embed.add_field(name="Event Role", value=f"{event_role.mention}\n*Join teams to get this role automatically*", inline=False)
                    if game_channel:
                        embed.add_field(name="Game Channel", value=f"{game_channel.mention}\n*Only participants can access*", inline=False)
                    embed.add_field(name="How to Join", value="React to the join embed in the join channel to join teams!", inline=False)
                    role_mention = f"{event_role.mention} " if event_role else ""
                    await event_channel.send(f"{role_mention}🎯 **NEW TOURNAMENT!** 🎯", embed=embed)
        if admin_cog:
            join_channel_id = admin_cog.get_channel_id("join", ctx.guild.id)
            if join_channel_id:
                join_channel = self.bot.get_channel(join_channel_id)
                if join_channel:
                    embed = discord.Embed(
                        title=f"🎯 {name}",
                        description="React with section emojis to join teams!\n\n**Sections:**\nNo sections created yet.",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Event ID", value=str(event_id), inline=True)
                    embed.add_field(name="Max Sections", value=str(max_sections), inline=True)
                    embed.add_field(name="Status", value="🟡 Open for Registration", inline=True)
                    embed_message = await join_channel.send(embed=embed)
                    if not hasattr(self, 'event_embeds'):
                        self.event_embeds = {}
                    self.event_embeds[event_id] = embed_message.id
                    await ctx.send(f"✅ Event created: **{name}** (ID: `{event_id}`)\n📋 Join embed posted in {join_channel.mention}")
                else:
                    await ctx.send(f"Event created: **{name}** (ID: `{event_id}`), Max Sections: {max_sections}\n⚠️ Join channel not found.")
            else:
                await ctx.send(f"Event created: **{name}** (ID: `{event_id}`), Max Sections: {max_sections}\n⚠️ Join channel not configured. Use `dm.set_channel join #channel`")
        else:
            await ctx.send(f"Event created: **{name}** (ID: `{event_id}`), Max Sections: {max_sections}")

    @commands.command(name="list_events", usage="", help="List all events.")
    async def list_events(self, ctx):
        if not await self.check_mod_channel(ctx):
            return
            
        print('[DEBUG] list_events command called')
        events = database.list_events(ctx.guild.id)
        print(f'[DEBUG] Events from DB: {events}')
        if not events:
            await ctx.send("No events found.")
            return
        embed = discord.Embed(title="Events", color=discord.Color.green())
        for event_id, name, max_sections in events:
            embed.add_field(name=f"{name} (ID: {event_id})", value=f"Max Sections: {max_sections}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="close_event", usage="<event_id>")
    @commands.has_permissions(administrator=True)
    async def close_event(self, ctx, event_id: int):
        """Hard deletes everything related to an event (Admin only, DB + memory)"""
        if not await self.check_mod_channel(ctx):
            return

        admin_cog = self.bot.get_cog('Admin')
        team_cog = self.bot.get_cog('Team')
        leaderboard_cog = self.bot.get_cog('Leaderboard')

        if event_id not in self.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = self.events[event_id]
        event_name = event['name']

        # Delete all section embeds (memory)
        if team_cog:
            for sect_name in event.get('sections', {}).keys():
                section_key = f"{event_id}_{sect_name}"
                if section_key in team_cog.section_embeds:
                    del team_cog.section_embeds[section_key]

        # Delete leaderboard embed (memory)
        if leaderboard_cog and event_id in getattr(leaderboard_cog, 'leaderboard_embeds', {}):
            del leaderboard_cog.leaderboard_embeds[event_id]
        if leaderboard_cog and event_id in getattr(leaderboard_cog, 'scores', {}):
            del leaderboard_cog.scores[event_id]

        # Remove from DB (event, sections, teams, team_members, leaderboard, user_event_participation, team_event_stats)
        try:
            with database.get_db() as conn:
                c = conn.cursor()
                c.execute('DELETE FROM leaderboard WHERE event_id = %s', (event_id,))
                c.execute('DELETE FROM team_event_stats WHERE event_id = %s', (event_id,))
                c.execute('DELETE FROM user_event_participation WHERE event_id = %s', (event_id,))
                # Remove teams and members
                c.execute('SELECT section_id FROM sections WHERE event_id = %s', (event_id,))
                # IDs in these tables are always integers; suppress linter warning if needed
                section_rows = c.fetchall()
                section_ids = [int(row[0]) for row in section_rows]  # type: ignore
                for section_id in section_ids:
                    c.execute('SELECT team_id FROM teams WHERE section_id = %s', (int(section_id),))
                    team_rows = c.fetchall()
                    team_ids = [int(row[0]) for row in team_rows]  # type: ignore
                    for team_id in team_ids:
                        c.execute('DELETE FROM team_members WHERE team_id = %s', (int(team_id),))
                    c.execute('DELETE FROM teams WHERE section_id = %s', (int(section_id),))
                c.execute('DELETE FROM sections WHERE event_id = %s', (event_id,))
                c.execute('DELETE FROM events WHERE event_id = %s', (event_id,))
                conn.commit()
        except Exception as e:
            await ctx.send(f"⚠️ Error deleting event from database: {e}")
            return

        # Delete the event (memory)
        del self.events[event_id]
        if hasattr(self, 'event_embeds') and event_id in self.event_embeds:
            del self.event_embeds[event_id]

        # Send log message
        log_channel_id = admin_cog.get_channel_id("log", ctx.guild.id) if admin_cog else None
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="🗑️ Event Closed",
                    description=f"Event **{event_name}** has been permanently closed and all data deleted.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Closed by {ctx.author.name}")
                await log_channel.send(embed=embed)

        await ctx.send(f"Event '**{event_name}**' has been permanently closed and all related data deleted.")

    @commands.command(name="end_event", usage="<event_id> [event_role]")
    @commands.has_permissions(administrator=True)
    async def end_event(self, ctx, event_id: int, *, event_role: str = ""):
        """Declares winners, tags event role, resets leaderboard, logs, and closes event (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return

        admin_cog = self.bot.get_cog('Admin')
        leaderboard_cog = self.bot.get_cog('Leaderboard')

        if event_id not in self.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = self.events[event_id]
        event_name = event['name']

        # Get leaderboard data
        event_scores = {}
        if leaderboard_cog and event_id in getattr(leaderboard_cog, 'scores', {}):
            event_scores = leaderboard_cog.scores[event_id].copy()

        if not event_scores:
            await ctx.send(f"No scores recorded for event '**{event_name}**'. Cannot declare winners.")
            return

        # Sort teams by score
        sorted_teams = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)

        # Create winners embed
        embed = discord.Embed(
            title=f"🏆 Event Results - {event_name}",
            color=discord.Color.gold()
        )

        winners = []
        for i, (team_name, score) in enumerate(sorted_teams[:3], 1):  # Top 3
            team_details = leaderboard_cog.get_team_details(event_id, team_name) if leaderboard_cog else None
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            winners.append(f"**{i}st Place:** {team_name} ({score} points)" if i == 1 else f"**{i}nd Place:** {team_name} ({score} points)" if i == 2 else f"**{i}rd Place:** {team_name} ({score} points)")
            if team_details:
                embed.add_field(
                    name=f"{medal} {team_name}",
                    value=f"**Score:** {score}\n**Section:** {team_details['section']}\n**Leader:** {team_details['leader']}",
                    inline=False
                )

        embed.description = "\n".join(winners)
        embed.set_footer(text=f"Event ended by {ctx.author.name}")

        # Send to event channel
        event_channel_id = admin_cog.get_channel_id("event", ctx.guild.id) if admin_cog else None
        if event_channel_id:
            event_channel = self.bot.get_channel(event_channel_id)
            if event_channel:
                # Tag event role if provided
                role_mention = f"{event_role} " if event_role else ""
                await event_channel.send(f"{role_mention}🏆 **EVENT ENDED!** 🏆", embed=embed)

        # Reset leaderboard (memory and DB)
        if leaderboard_cog and event_id in getattr(leaderboard_cog, 'scores', {}):
            leaderboard_cog.scores[event_id] = {}
            await leaderboard_cog.update_leaderboard_embed(event_id)
        try:
            with database.get_db() as conn:
                c = conn.cursor()
                c.execute('DELETE FROM leaderboard WHERE event_id = %s', (event_id,))
                c.execute('DELETE FROM team_event_stats WHERE event_id = %s', (event_id,))
                conn.commit()
        except Exception as e:
            await ctx.send(f"⚠️ Error resetting leaderboard in database: {e}")

        # Send log message
        log_channel_id = admin_cog.get_channel_id("log", ctx.guild.id) if admin_cog else None
        if log_channel_id:
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="🏁 Event Ended",
                    description=f"Event **{event_name}** has ended.\n**Winners:**\n" + "\n".join(winners),
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                log_embed.set_footer(text=f"Ended by {ctx.author.name}")
                await log_channel.send(embed=log_embed)

        await ctx.send(f"Event '**{event_name}**' has ended! Winners have been declared and leaderboard has been reset.")

    async def update_event_embed(self, event_id):
        """Update the event embed with current sections and teams"""
        if not hasattr(self, 'event_embeds') or event_id not in self.event_embeds:
            return
            
        event = self.events.get(event_id)
        if not event:
            return
            
        admin_cog = self.bot.get_cog('Admin')
        if not admin_cog:
            return
            
        join_channel_id = admin_cog.get_channel_id("join")
        if not join_channel_id:
            return
            
        join_channel = self.bot.get_channel(join_channel_id)
        if not join_channel:
            return
            
        try:
            embed_message = await join_channel.fetch_message(self.event_embeds[event_id])
        except:
            return
            
        # Create updated embed
        embed = discord.Embed(
            title=f"🎯 {event['name']}",
            description="React with section emojis to join teams!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Event ID", value=str(event_id), inline=True)
        embed.add_field(name="Max Sections", value=str(event['max_sections']), inline=True)
        
        # Determine status
        sections = event.get('sections', {})
        if not sections:
            embed.add_field(name="Status", value="🟡 Open for Registration", inline=True)
            embed.description = "React with section emojis to join teams!\n\n**Sections:**\nNo sections created yet."
        else:
            total_teams = sum(len(sect.get('teams', {})) for sect in sections.values())
            total_members = sum(
                len(team.get('members', [])) 
                for sect in sections.values() 
                for team in sect.get('teams', {}).values()
            )
            embed.add_field(name="Status", value="🟢 Active", inline=True)
            embed.add_field(name="Sections", value=str(len(sections)), inline=True)
            embed.add_field(name="Teams", value=str(total_teams), inline=True)
            embed.add_field(name="Members", value=str(total_members), inline=True)
            
            # Add sections with teams
            for sect_name, section in sections.items():
                teams = section.get('teams', {})
                if teams:
                    section_text = ""
                    for team_name, team_data in teams.items():
                        emoji = team_data.get('emoji', '❓')
                        current_members = len(team_data.get('members', []))
                        max_members = team_data.get('max_members', 0)
                        status = "🟢" if current_members < max_members else "🔴"
                        section_text += f"{status} {emoji} **{team_name}** ({current_members}/{max_members})\n"
                    embed.add_field(
                        name=f"📋 {sect_name}",
                        value=section_text or "No teams",
                        inline=False
                    )
        
        await embed_message.edit(embed=embed)
        
        # Update reactions
        try:
            # Clear existing reactions
            await embed_message.clear_reactions()
            
            # Add section emojis
            for sect_name, section in sections.items():
                teams = section.get('teams', {})
                for team_name, team_data in teams.items():
                    emoji = team_data.get('emoji')
                    if emoji:
                        await embed_message.add_reaction(emoji)
        except Exception as e:
            print(f"Error updating reactions: {e}")

    @commands.command(name="announce", usage="<event_id> [announcement]", help="Send a tournament announcement to the event channel")
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, event_id: int, *, announcement_text: str):
        """Send a manual tournament announcement to the event channel (Admin only)"""
        if not await self.check_mod_channel(ctx):
            return
            
        if event_id not in self.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = self.events[event_id]
        event_name = event['name']
        
        # Get event role for mention
        event_role = None
        role_id = event.get('role_id')
        if role_id:
            event_role = ctx.guild.get_role(role_id)
        
        # Send announcement to event channel
        admin_cog = self.bot.get_cog('Admin')
        if admin_cog:
            event_channel_id = admin_cog.get_channel_id("event")
            if event_channel_id:
                event_channel = self.bot.get_channel(event_channel_id)
                if event_channel:
                    embed = discord.Embed(
                        title=f"📢 Tournament Announcement: {event_name}",
                        description=announcement_text,
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Event ID", value=str(event_id), inline=True)
                    embed.add_field(name="Announced by", value=ctx.author.mention, inline=True)
                    embed.set_footer(text=f"Tournament: {event_name}")
                    
                    # Mention the event role if it exists
                    role_mention = f"{event_role.mention} " if event_role else ""
                    await event_channel.send(f"{role_mention}📢 **TOURNAMENT ANNOUNCEMENT!** 📢", embed=embed)
                    
                    await ctx.send(f"✅ Announcement sent to {event_channel.mention}")
                else:
                    await ctx.send("❌ Event channel not found.")
            else:
                await ctx.send("❌ Event channel not configured. Use `dm.set_channel event #channel` first.")
        else:
            await ctx.send("❌ Admin cog not available.")

async def setup(bot):
    await bot.add_cog(Event(bot)) 