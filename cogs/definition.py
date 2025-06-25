import discord
from discord.ext import commands
import json
import os

DATA_FILE = 'data.json'
ALLOWED_MOD_SERVER_ID = 1387399782724669470  # Only mods from this server can delete any definition

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class DefinitionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.reference:
            return
        if not message.content.startswith('@bot'):
            return
        # Parse command
        cmd = message.content[len('@bot'):].strip()
        if not cmd:
            return
        if '/' in cmd:
            title, author = [x.strip() for x in cmd.split('/', 1)]
        else:
            title, author = cmd.strip(), None
        if not title:
            return
        # Get the original message (the definition)
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
        except Exception:
            return
        definition = ref_msg.content
        if not definition:
            return
        if not author:
            author = ref_msg.author.display_name
        # Load, update, and save data
        data = load_data()
        if title not in data:
            data[title] = []
        # Assign serial number (1-based, unique per title)
        serial = len(data[title]) + 1
        data[title].append({
            "author": author,
            "author_id": str(ref_msg.author.id),
            "definition": definition,
            "serial": serial
        })
        save_data(data)
        await message.channel.send(f"Definition for **{title}** by **{author}** saved! Serial: `{serial}`")

    @commands.command(name="getdef", usage="<title>", help="Get all definitions for a title.")
    async def get_definition(self, ctx, *, title: str):
        """Get all definitions for a title."""
        data = load_data()
        if title not in data or not data[title]:
            await ctx.send(f"No definitions found for **{title}**.")
            return
        embed = discord.Embed(title=f"Definitions for {title}", color=discord.Color.green())
        for entry in data[title]:
            embed.add_field(name=f"#{entry['serial']} by {entry['author']}", value=entry['definition'], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="del_definition", usage="<serial number> <title>", help="Delete a definition by serial number (author or moderator from the allowed server only). Example: dm.del_definition 2 Python")
    async def del_definition(self, ctx, serial: int, *, title: str):
        """Delete a definition by serial number (author or moderator from the allowed server only)."""
        data = load_data()
        if title not in data or not data[title]:
            await ctx.send(f"No definitions found for **{title}**.")
            return
        # Find the definition with the given serial
        entry = next((e for e in data[title] if e.get('serial') == serial), None)
        if not entry:
            await ctx.send(f"No definition with serial `{serial}` found for **{title}**.")
            return
        # Permission check: author or moderator from allowed server
        is_author = str(ctx.author.id) == entry.get('author_id')
        is_mod = (
            ctx.guild
            and ctx.guild.id == ALLOWED_MOD_SERVER_ID
            and ctx.author.guild_permissions.manage_messages
        )
        if not (is_author or is_mod):
            await ctx.send("You do not have permission to delete this definition. Only the author or a moderator from the allowed server can delete it.")
            return
        # Remove the entry
        data[title] = [e for e in data[title] if e.get('serial') != serial]
        # Reassign serials to keep them 1-based and unique
        for idx, e in enumerate(data[title], 1):
            e['serial'] = idx
        save_data(data)
        await ctx.send(f"Definition #{serial} for **{title}** deleted.")

def setup(bot):
    bot.add_cog(DefinitionCog(bot)) 