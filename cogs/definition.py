import discord
from discord.ext import commands
import json
import os

DATA_FILE = 'data.json'

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
        data[title].append({
            "author": author,
            "definition": definition
        })
        save_data(data)
        await message.channel.send(f"Definition for **{title}** by **{author}** saved!")

    @commands.command(name="getdef", usage="<title>", help="Get all definitions for a title.")
    async def get_definition(self, ctx, *, title: str):
        """Get all definitions for a title."""
        data = load_data()
        if title not in data or not data[title]:
            await ctx.send(f"No definitions found for **{title}**.")
            return
        embed = discord.Embed(title=f"Definitions for {title}", color=discord.Color.green())
        for entry in data[title]:
            embed.add_field(name=entry['author'], value=entry['definition'], inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(DefinitionCog(bot)) 