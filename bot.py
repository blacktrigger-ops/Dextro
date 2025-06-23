import discord
from discord.ext import commands
import os
import asyncio
import database

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='dm.',
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                await self.load_extension(f'cogs.{filename[:-3]}')

        # If you have global slash commands, uncomment this
        # await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} ({self.user.id if self.user else ""})')
        print('------')

    async def on_command(self, ctx):
        # Log user command usage
        if ctx.guild:
            database.log_user_command(ctx.guild.id, ctx.author.id, ctx.command.qualified_name)
            # Increment server stats for certain commands
            if ctx.command.qualified_name == 'create_event':
                database.increment_server_stat(ctx.guild.id, 'events_created')
            elif ctx.command.qualified_name == 'create_team':
                database.increment_server_stat(ctx.guild.id, 'teams_created')
            elif ctx.command.qualified_name == 'join_team':
                database.increment_server_stat(ctx.guild.id, 'members_joined')

bot = MyBot()

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", description="Here are the available commands:", color=discord.Color.blue())
    
    # Get all cogs and their commands
    for cog_name, cog in bot.cogs.items():
        if cog_name.lower() in ['admin', 'event', 'team', 'leaderboard']:
            # Get commands from this cog
            cog_commands = [cmd for cmd in cog.get_commands() if not cmd.hidden]
            if cog_commands:
                # Add cog section header
                embed.add_field(name=f"**{cog_name.title()} Commands**", value="\u200b", inline=False)
                
                # Add each command
                for cmd in cog_commands:
                    # Format command usage
                    if cmd.usage:
                        usage = f"`dm.{cmd.name} {cmd.usage}`"
                    else:
                        usage = f"`dm.{cmd.name}`"
                    
                    # Get command description
                    description = cmd.help or "No description available."
                    
                    # Add admin indicator
                    if any(check.__qualname__ == 'has_permissions' for check in cmd.checks):
                        description += " (Admin only)"
                    
                    embed.add_field(name=usage, value=description, inline=False)
    
    # Add global commands (like help)
    embed.add_field(name="**Global Commands**", value="\u200b", inline=False)
    embed.add_field(name="`dm.help`", value="Shows this help message.", inline=False)
    embed.add_field(name="`dm.reload <cog>`", value="Reloads a cog (Admin only).", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, cog_name: str):
    """Reloads a cog (Admin only)"""
    try:
        await bot.reload_extension(f"cogs.{cog_name.lower()}")
        await ctx.send(f"✅ Cog `{cog_name}` has been reloaded successfully!")
    except Exception as e:
        await ctx.send(f"❌ Error reloading cog `{cog_name}`: {str(e)}")

async def main():
    from config import TOKEN
    async with bot:
        await bot.start(TOKEN)