# test_tournament.py - Quick test script
# Run this to test tournament functionality

import asyncio
import discord
from discord.ext import commands

# Test bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='dm.', intents=intents)

@bot.event
async def on_ready():
    print(f'Test bot logged in as {bot.user}')
    print('Bot is ready for testing!')
    print('\nTest Commands:')
    print('1. dm.set_channel mod #moderation')
    print('2. dm.set_channel event #announcements')
    print('3. dm.set_channel team #teams')
    print('4. dm.set_channel join #team-join')
    print('5. dm.set_channel log #bot-logs')
    print('6. dm.create_event (Test Tournament/3)')
    print('7. dm.announce 1 This is a test announcement!')

# Run the test bot
if __name__ == "__main__":
    bot.run('your-test-token-here') 