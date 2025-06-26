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

def main():
    bot = MyBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )

    async def setup():
        if config.BOT_MODE == 'definition':
            for cog in COGS_DEFINITION:
                print(f"Loading extension: {cog}")
                await bot.load_extension(cog)
        elif config.BOT_MODE == 'tournament':
            for cog in COGS_TOURNAMENT:
                print(f"Loading extension: {cog}")
                await bot.load_extension(cog)
        else:  # both
            for cog in COGS_DEFINITION + COGS_TOURNAMENT:
                print(f"Loading extension: {cog}")
                await bot.load_extension(cog)

    bot.setup_hook = setup
    bot.run(config.DISCORD_TOKEN) 