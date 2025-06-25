print("definition.py is being imported")

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
        if message.author.bot:
            return
        # Check if the bot is mentioned at the start of the message
        if message.content.startswith(self.bot.user.mention):
            cmd = message.content[len(self.bot.user.mention):].strip()
            # ADD DEFINITION: If this is a reply
            if message.reference:
                if not cmd:
                    return
                if '/' in cmd:
                    title, author = [x.strip() for x in cmd.split('/', 1)]
                else:
                    title, author = cmd.strip(), None
                if not title:
                    return
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                except Exception:
                    return
                definition = ref_msg.content
                if not definition:
                    return
                if not author:
                    author = ref_msg.author.display_name
                data = load_data()
                if title not in data:
                    data[title] = []
                serial = len(data[title]) + 1
                data[title].append({
                    "author": author,
                    "author_id": str(ref_msg.author.id),
                    "definition": definition,
                    "serial": serial
                })
                save_data(data)
                await message.channel.send(f"Definition for **{title}** by **{author}** saved! Serial: `{serial}`")
                return
            # OUTPUT DEFINITIONS: If not a reply
            if cmd:
                title = cmd
                data = load_data()
                if title not in data or not data[title]:
                    await message.channel.send(f"No definitions found for **{title}**.")
                    return
                definitions = data[title]
                current = 0
                def make_embed(idx):
                    entry = definitions[idx]
                    embed = discord.Embed(title="Definition", color=discord.Color.green())
                    embed.add_field(name=f"**{title}**", value=f"**Author:** {entry['author']}\n\n{entry['definition']}", inline=False)
                    embed.set_footer(text=f"Definition {idx+1}/{len(definitions)} | Use ◀️ ▶️ to navigate")
                    return embed
                msg = await message.channel.send(embed=make_embed(current))
                if len(definitions) > 1:
                    await msg.add_reaction("◀️")
                    await msg.add_reaction("▶️")
                def check(reaction, user):
                    return user == message.author and reaction.message.id == msg.id and str(reaction.emoji) in ["◀️", "▶️"]
                while True and len(definitions) > 1:
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if str(reaction.emoji) == "▶️":
                            current = (current + 1) % len(definitions)
                            await msg.edit(embed=make_embed(current))
                        elif str(reaction.emoji) == "◀️":
                            current = (current - 1) % len(definitions)
                            await msg.edit(embed=make_embed(current))
                        await msg.remove_reaction(reaction, user)
                    except Exception:
                        break
                return

    @commands.command(name="del_definition", usage="<serial number> <title>", help="Delete a definition by serial number (author or moderator from the allowed server only). Example: dm.del_definition 2 Python")
    async def del_definition(self, ctx, serial: int, *, title: str):
        """Delete a definition by serial number (author or moderator from the allowed server only)."""
        data = load_data()
        if title not in data or not data[title]:
            await ctx.send(f"No definitions found for **{title}**.")
            return
        entry = next((e for e in data[title] if e.get('serial') == serial), None)
        if not entry:
            await ctx.send(f"No definition with serial `{serial}` found for **{title}**.")
            return
        is_author = str(ctx.author.id) == entry.get('author_id')
        is_mod = (
            ctx.guild
            and ctx.guild.id == ALLOWED_MOD_SERVER_ID
            and ctx.author.guild_permissions.manage_messages
        )
        if not (is_author or is_mod):
            await ctx.send("You do not have permission to delete this definition. Only the author or a moderator from the allowed server can delete it.")
            return
        data[title] = [e for e in data[title] if e.get('serial') != serial]
        for idx, e in enumerate(data[title], 1):
            e['serial'] = idx
        save_data(data)
        await ctx.send(f"Definition #{serial} for **{title}** deleted.")

async def setup(bot):
    print("DefinitionCog setup called")
    await bot.add_cog(DefinitionCog(bot)) 