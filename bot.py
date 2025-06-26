import discord
from discord.ext import commands
import os
import asyncio
import database

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} ({self.user.id if self.user else ""})')
        print('------')

    async def on_command(self, ctx):
        # Optionally, add logging or hooks here
        pass

def main():
    bot = MyBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )
    bot.run(os.getenv('TOKEN', ''))