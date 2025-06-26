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
    'cogs_tournament.admin',
    'cogs_tournament.leaderboard',
    'cogs_tournament.stats',
]

def get_cogs_for_mode(mode):
    if mode == 'definition':
        return COGS_DEFINITION
    elif mode == 'tournament':
        return COGS_TOURNAMENT
    else:
        return COGS_DEFINITION + COGS_TOURNAMENT

async def reload_cogs(bot, mode):
    # Unload all loaded cogs
    for cog in list(bot.extensions):
        await bot.unload_extension(cog)
    # Load new cogs
    for cog in get_cogs_for_mode(mode):
        print(f"Loading extension: {cog}")
        await bot.load_extension(cog)


def main():
    bot = MyBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )

    async def setup():
        mode = config.get_mode()
        await reload_cogs(bot, mode)

    bot.setup_hook = setup
    bot.reload_cogs = lambda mode: reload_cogs(bot, mode)  # Attach for admin command
    bot.run(config.DISCORD_TOKEN) 