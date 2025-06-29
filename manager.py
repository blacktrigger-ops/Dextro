import discord
from discord.ext import commands
import config
import os
from bot import MyBot

COGS_DEFINITION = [
    'cogs_definition.definition',
]

COGS_TOURNAMENT = [
    'cogs_tournament.event',
    'cogs_tournament.team',
    'cogs_tournament.leaderboard',
    'cogs_tournament.stats',
]

# Admin cog is always loaded regardless of mode
COGS_ADMIN = [
    'cogs_tournament.admin',
]

def get_cogs_for_mode(mode):
    if mode == 'definition':
        return COGS_DEFINITION + COGS_ADMIN
    elif mode == 'tournament':
        return COGS_TOURNAMENT + COGS_ADMIN
    else:
        return COGS_DEFINITION + COGS_TOURNAMENT + COGS_ADMIN

async def reload_cogs(bot, mode):
    # Unload all loaded cogs
    for cog in list(bot.extensions):
        await bot.unload_extension(cog)
    # Load new cogs
    for cog in get_cogs_for_mode(mode):
        print(f"Loading extension: {cog}")
        await bot.load_extension(cog)

class ManagerBot(MyBot):
    async def setup_hook(self):
        """Called when the bot is starting up."""
        mode = config.get_mode()
        await reload_cogs(self, mode)
    
    async def reload_cogs(self, mode):
        """Reload cogs for a specific mode."""
        await reload_cogs(self, mode)

def main():
    bot = ManagerBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )
    bot.run(config.DISCORD_TOKEN) 