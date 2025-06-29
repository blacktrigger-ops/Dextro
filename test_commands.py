#!/usr/bin/env python3
"""
Test script to verify bot commands are working
"""

import asyncio
import discord
from discord.ext import commands
import config
from manager import ManagerBot

async def test_bot():
    """Test the bot setup and command loading"""
    bot = ManagerBot(
        command_prefix='dm.',
        intents=discord.Intents.all(),
        help_command=None
    )
    
    print("Testing bot setup...")
    
    # Test cog loading
    try:
        await bot.setup_hook()
        print("✅ Bot setup completed successfully")
        
        # Check loaded cogs
        print(f"Loaded cogs: {list(bot.extensions)}")
        
        # Check admin commands specifically
        admin_cog = bot.get_cog('Admin')
        if admin_cog:
            print("✅ Admin cog loaded successfully")
            admin_commands = [cmd.name for cmd in admin_cog.get_commands()]
            print(f"Admin commands: {admin_commands}")
            
            # Check for channel commands specifically
            channel_commands = [cmd for cmd in admin_commands if 'channel' in cmd]
            print(f"Channel-related commands: {channel_commands}")
        else:
            print("❌ Admin cog not loaded")
            
    except Exception as e:
        print(f"❌ Error during bot setup: {e}")
        import traceback
        traceback.print_exc()
    
    await bot.close()

if __name__ == "__main__":
    asyncio.run(test_bot()) 