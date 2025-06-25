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
        # Only load the definition cog
        print("Loading extension: definition.py")
        await self.load_extension('cogs.definition')

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

    async def on_message(self, message):
        await self.process_commands(message)

bot = MyBot()

bot.run(os.getenv('TOKEN', ''))