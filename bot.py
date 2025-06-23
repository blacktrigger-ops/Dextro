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
    embed = discord.Embed(title="Bot Commands", description="React to navigate categories!", color=discord.Color.blue())
    categories = {}
    # Gather commands by cog
    for cog_name, cog in bot.cogs.items():
        cog_commands = [cmd for cmd in cog.get_commands() if not cmd.hidden]
        if cog_commands:
            categories[cog_name] = []
            for cmd in cog_commands:
                usage = f"`dm.{cmd.name} {cmd.usage}`" if cmd.usage else f"`dm.{cmd.name}`"
                description = cmd.help or "No description available."
                if any(check.__qualname__ == 'has_permissions' for check in cmd.checks):
                    description += " (Admin only)"
                # Mark new/updated commands
                if cmd.name in ["user_stats", "team_stats"]:
                    description = "🆕 " + description
                categories[cog_name].append((usage, description))
    # Prepare category list
    category_list = list(categories.keys())
    if not category_list:
        await ctx.send("No commands available.")
        return
    # Show first category by default
    current = 0
    def make_embed(idx):
        cat = category_list[idx]
        e = discord.Embed(title=f"{cat.title()} Commands", color=discord.Color.blue())
        for usage, desc in categories[cat]:
            e.add_field(name=usage, value=desc, inline=False)
        e.set_footer(text=f"Category {idx+1}/{len(category_list)} | Use ◀️ ▶️ to navigate | 🏠 for all categories")
        return e
    msg = await ctx.send(embed=make_embed(current))
    await msg.add_reaction("◀️")
    await msg.add_reaction("▶️")
    await msg.add_reaction("🏠")
    def check(reaction, user):
        return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["◀️", "▶️", "🏠"]
    while True:
        try:
            print("[DEBUG] Waiting for help command reaction...")
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            print(f"[DEBUG] Reaction received: {reaction.emoji} by {user}")
            if str(reaction.emoji) == "▶️":
                current = (current + 1) % len(category_list)
                await msg.edit(embed=make_embed(current))
            elif str(reaction.emoji) == "◀️":
                current = (current - 1) % len(category_list)
                await msg.edit(embed=make_embed(current))
            elif str(reaction.emoji) == "🏠":
                home_embed = discord.Embed(title="Bot Command Categories", description="\n".join(f"{i+1}. {cat.title()}" for i, cat in enumerate(category_list)), color=discord.Color.blue())
                home_embed.set_footer(text="React with ◀️ ▶️ to browse categories.")
                await msg.edit(embed=home_embed)
            await msg.remove_reaction(reaction, user)
        except Exception as e:
            print(f"[DEBUG] Exiting help command reaction loop: {e}")
            break

@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, cog_name: str):
    """Reloads a cog (Admin only)"""
    try:
        await bot.reload_extension(f"cogs.{cog_name.lower()}")
        await ctx.send(f"✅ Cog `{cog_name}` has been reloaded successfully!")
    except Exception as e:
        await ctx.send(f"❌ Error reloading cog `{cog_name}`: {str(e)}")

import os

bot.run(os.getenv('TOKEN', ''))