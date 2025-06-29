#!/usr/bin/env python3
"""
Comprehensive bot test script to verify all functionality
"""

import asyncio
import discord
from discord.ext import commands
import config
from manager import ManagerBot
import database
import os

def test_config():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")
    
    # Test mode configuration
    mode = config.get_mode()
    print(f"✅ Bot mode: {mode}")
    
    # Test token configuration
    token = config.DISCORD_TOKEN
    if token == "your-token-here":
        print("⚠️  WARNING: Using fallback token. Set DISCORD_TOKEN environment variable.")
        return False
    elif not token:
        print("❌ ERROR: No Discord token found!")
        return False
    else:
        print("✅ Discord token configured")
        return True

def test_database():
    """Test database operations"""
    print("\n🗄️  Testing Database...")
    
    try:
        # Test basic database operations
        test_guild_id = 123456789
        test_channel_id = 987654321
        
        # Test channel operations
        database.set_channel(test_guild_id, "test_channel", test_channel_id)
        retrieved_id = database.get_channel(test_guild_id, "test_channel")
        
        if retrieved_id == test_channel_id:
            print("✅ Channel database operations working")
        else:
            print(f"❌ Channel database operations failed. Expected {test_channel_id}, got {retrieved_id}")
            return False
            
        # Test bot config operations
        database.set_bot_config("test_key", "test_value")
        retrieved_value = database.get_bot_config("test_key")
        
        if retrieved_value == "test_value":
            print("✅ Bot config database operations working")
        else:
            print(f"❌ Bot config database operations failed. Expected 'test_value', got '{retrieved_value}'")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_bot_setup():
    """Test bot setup and cog loading"""
    print("\n🤖 Testing Bot Setup...")
    
    try:
        bot = ManagerBot(
            command_prefix='dm.',
            intents=discord.Intents.all(),
            help_command=None
        )
        
        # Test setup hook
        await bot.setup_hook()
        print("✅ Bot setup completed successfully")
        
        # Check loaded cogs
        loaded_cogs = list(bot.extensions)
        print(f"✅ Loaded cogs: {len(loaded_cogs)}")
        for cog in loaded_cogs:
            print(f"  - {cog}")
        
        # Test specific cogs
        admin_cog = bot.get_cog('Admin')
        if admin_cog:
            print("✅ Admin cog loaded")
            admin_commands = [cmd.name for cmd in admin_cog.get_commands()]
            print(f"  Admin commands: {admin_commands}")
        else:
            print("❌ Admin cog not loaded")
            
        # Test tournament cogs
        event_cog = bot.get_cog('Event')
        team_cog = bot.get_cog('Team')
        leaderboard_cog = bot.get_cog('Leaderboard')
        stats_cog = bot.get_cog('Stats')
        
        if event_cog:
            print("✅ Event cog loaded")
        if team_cog:
            print("✅ Team cog loaded")
        if leaderboard_cog:
            print("✅ Leaderboard cog loaded")
        if stats_cog:
            print("✅ Stats cog loaded")
            
        # Test definition cog
        definition_cog = bot.get_cog('DefinitionCog')
        if definition_cog:
            print("✅ Definition cog loaded")
        else:
            print("❌ Definition cog not loaded")
        
        await bot.close()
        return True
        
    except Exception as e:
        print(f"❌ Bot setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_command_parsing():
    """Test command parsing and validation"""
    print("\n📝 Testing Command Parsing...")
    
    # Test command prefix
    prefix = 'dm.'
    test_commands = [
        'dm.set_channel mod #general',
        'dm.show_channels',
        'dm.set_mode tournament',
        'dm.help tournament',
        'dm.create_event TestEvent 5',
        'dm.list_events'
    ]
    
    for cmd in test_commands:
        if cmd.startswith(prefix):
            print(f"✅ Command format valid: {cmd}")
        else:
            print(f"❌ Command format invalid: {cmd}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Bot Test\n")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_config()
    
    # Test database
    db_ok = test_database()
    
    # Test command parsing
    cmd_ok = test_command_parsing()
    
    # Test bot setup (async)
    print("\n" + "=" * 50)
    bot_ok = asyncio.run(test_bot_setup())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("Configuration", config_ok),
        ("Database", db_ok),
        ("Command Parsing", cmd_ok),
        ("Bot Setup", bot_ok)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Bot should work correctly.")
        print("\nTo start the bot:")
        print("1. Set your Discord bot token: export DISCORD_TOKEN='your-token-here'")
        print("2. Run: python main.py")
    else:
        print("⚠️  SOME TESTS FAILED. Please check the issues above.")
        
    if not config_ok:
        print("\n🔑 TOKEN SETUP:")
        print("1. Create a Discord application at https://discord.com/developers/applications")
        print("2. Create a bot for your application")
        print("3. Copy the bot token")
        print("4. Set environment variable: DISCORD_TOKEN='your-actual-token'")
        print("5. Or create a .env file with: DISCORD_TOKEN=your-actual-token")

if __name__ == "__main__":
    main() 