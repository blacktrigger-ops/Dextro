import discord
from discord.ext import commands
import os
import asyncio
import database
import traceback

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'Logged in as {self.user} ({self.user.id if self.user else ""})')
        print('------')

    async def on_command(self, ctx):
        # Optionally, add logging or hooks here
        print(f"Command executed: {ctx.command} by {ctx.author} in {ctx.guild}")

    async def on_command_error(self, ctx, error):
        """Handle command errors and provide helpful feedback"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Command not found. Use `{self.command_prefix}help` to see available commands.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided: {error}")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command can only be used in a server.")
        else:
            # Log the full error for debugging
            print(f"Unhandled command error: {error}")
            print(traceback.format_exc())
            await ctx.send("❌ An unexpected error occurred. Please try again or contact an administrator.")

def main():
    bot = MyBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )
    bot.run(os.getenv('DISCORD_TOKEN', ''))