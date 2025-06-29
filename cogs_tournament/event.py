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

    @commands.command(name="create_event", usage="(event_name/Max_sect)", help="Create a new event.")
    async def create_event(self, ctx, *, event_info: str):
        print('[DEBUG] create_event called')
        import re
        match = re.match(r"\(([^/]+)/([0-9]+)\)", event_info.strip())
        if not match:
            await ctx.send("Invalid format! Use: (Event Name/Max Sections)")
            return
        name, max_sections = match.group(1).strip(), int(match.group(2))
        event_id = database.add_event(ctx.guild.id, name, max_sections)
        
        # Store event data in memory
        self.events[event_id] = {
            'name': name,
            'max_sections': max_sections,
            'sections': {}
        }
        
        # Create embed in join channel
        admin_cog = self.bot.get_cog('Admin')
        if admin_cog:
            join_channel_id = admin_cog.get_channel_id("join")
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
                    
                    # Store the embed message ID
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
        """Hard deletes everything related to an event (Admin only)"""
        admin_cog = self.bot.get_cog('Admin')
        team_cog = self.bot.get_cog('Team')
        leaderboard_cog = self.bot.get_cog('Leaderboard')
        
        if event_id not in self.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = self.events[event_id]
        event_name = event['name']
        
        # Delete all section embeds
        if team_cog:
            for sect_name in event.get('sections', {}).keys():
                section_key = f"{event_id}_{sect_name}"
                if section_key in team_cog.section_embeds:
                    del team_cog.section_embeds[section_key]
        
        # Delete leaderboard embed
        if leaderboard_cog and event_id in leaderboard_cog.leaderboard_embeds:
            del leaderboard_cog.leaderboard_embeds[event_id]
        
        # Delete scores
        if leaderboard_cog and event_id in leaderboard_cog.scores:
            del leaderboard_cog.scores[event_id]
        
        # Delete the event
        del self.events[event_id]
        
        # Send log message
        log_channel_id = admin_cog.get_channel_id("log_channel") if admin_cog else None
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
        """Declares winners and tags event role members, then resets leaderboard (Admin only)"""
        admin_cog = self.bot.get_cog('Admin')
        leaderboard_cog = self.bot.get_cog('Leaderboard')
        
        if event_id not in self.events:
            await ctx.send(f"Event with ID `{event_id}` not found.")
            return

        event = self.events[event_id]
        event_name = event['name']
        
        # Get leaderboard data
        event_scores = {}
        if leaderboard_cog and event_id in leaderboard_cog.scores:
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
            
            if i == 1:
                medal = "🥇"
                winners.append(f"**1st Place:** {team_name} ({score} points)")
            elif i == 2:
                medal = "🥈"
                winners.append(f"**2nd Place:** {team_name} ({score} points)")
            elif i == 3:
                medal = "🥉"
                winners.append(f"**3rd Place:** {team_name} ({score} points)")
            
            if team_details:
                embed.add_field(
                    name=f"{medal} {team_name}",
                    value=f"**Score:** {score}\n**Section:** {team_details['section']}\n**Leader:** {team_details['leader']}",
                    inline=False
                )
        
        embed.description = "\n".join(winners)
        embed.set_footer(text=f"Event ended by {ctx.author.name}")
        
        # Send to event channel
        event_channel_id = admin_cog.get_channel_id("event_channel") if admin_cog else None
        if event_channel_id:
            event_channel = self.bot.get_channel(event_channel_id)
            if event_channel:
                # Tag event role if provided
                role_mention = ""
                if event_role:
                    role_mention = f"{event_role} "
                
                await event_channel.send(f"{role_mention}🏆 **EVENT ENDED!** 🏆", embed=embed)
        
        # Reset leaderboard
        if leaderboard_cog and event_id in leaderboard_cog.scores:
            leaderboard_cog.scores[event_id] = {}
            await leaderboard_cog.update_leaderboard_embed(event_id)
        
        # Send log message
        log_channel_id = admin_cog.get_channel_id("log_channel") if admin_cog else None
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

async def setup(bot):
    await bot.add_cog(Event(bot)) 