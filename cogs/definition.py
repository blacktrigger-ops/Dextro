print("definition.py is being imported")

import discord
from discord.ext import commands
import mysql.connector

MYSQL_CONFIG = {
    'host': 'mysql.railway.internal',
    'port': 3306,
    'database': 'railway',
    'user': 'root',
    'password': 'UpXiofqjknhWmszqIqTxBcMlhLpZGGId',
}

ALLOWED_MOD_SERVER_ID = 1387399782724669470  # Only mods from this server can delete any definition

def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)

def ensure_table():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS definitions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            author VARCHAR(255) NOT NULL,
            author_id VARCHAR(32) NOT NULL,
            definition TEXT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    ''')
    conn.commit()
    c.close()
    conn.close()

ensure_table()

class DefinitionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", usage="definitions", help="Show help for the definitions system. Usage: dm.help definitions")
    async def help_definitions(self, ctx, *, arg: str = ""):
        if arg.lower() != "definitions":
            return  # Only respond to 'dm.help definitions'
        embed = discord.Embed(
            title="Definitions Help",
            color=discord.Color.blue(),
            description="How to use the Definitions system:"
        )
        embed.add_field(
            name="Add a Definition",
            value=(
                "1. **Reply** to the message you want to save as a definition.\n"
                "2. Mention the bot and type: `define <title>[/author]` or `definition <title>[/author]`\n"
                "   - Example: `@Bot define Python/Guido` (author is optional)\n"
                "3. The replied message's content will be saved as the definition."
            ),
            inline=False
        )
        embed.add_field(
            name="Get a Definition",
            value=(
                "Mention the bot and type: `define <title>` or `definition <title>`\n"
                "- Example: `@Bot define Python`\n"
                "- If multiple definitions exist, use ◀️ ▶️ reactions to navigate."
            ),
            inline=False
        )
        embed.add_field(
            name="Delete a Definition",
            value=(
                "Command: `dm.del_definition <serial> <title>`\n"
                "- Only the author or a moderator from the allowed server can delete.\n"
                "- Example: `dm.del_definition 2 Python`"
            ),
            inline=False
        )
        embed.set_footer(text="For more help, contact a moderator.")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith(self.bot.user.mention):
            cmd = message.content[len(self.bot.user.mention):].strip()
            lowered = cmd.lower()
            if lowered.startswith('define '):
                cmd = cmd[7:].strip()
            elif lowered.startswith('definition '):
                cmd = cmd[11:].strip()
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
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM definitions WHERE title = %s", (title,))
                serial = c.fetchone()[0] + 1
                c.execute(
                    "INSERT INTO definitions (title, author, author_id, definition) VALUES (%s, %s, %s, %s)",
                    (title, author, str(ref_msg.author.id), definition)
                )
                conn.commit()
                c.close()
                conn.close()
                await message.channel.send(f"Definition for **{title}** by **{author}** saved! Serial: `{serial}`")
                return
            # OUTPUT DEFINITIONS: If not a reply
            if cmd:
                title = cmd
                conn = get_db()
                c = conn.cursor(dictionary=True)
                c.execute("SELECT * FROM definitions WHERE title = %s ORDER BY id ASC", (title,))
                definitions = c.fetchall()
                c.close()
                conn.close()
                if not definitions:
                    await message.channel.send(f"No definitions found for **{title}**.")
                    return
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
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0, check=check)
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
        conn = get_db()
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM definitions WHERE title = %s ORDER BY id ASC", (title,))
        definitions = c.fetchall()
        if not definitions or serial < 1 or serial > len(definitions):
            await ctx.send(f"No definition with serial `{serial}` found for **{title}**.")
            c.close()
            conn.close()
            return
        entry = definitions[serial - 1]
        is_author = str(ctx.author.id) == entry['author_id']
        is_mod = (
            ctx.guild
            and ctx.guild.id == ALLOWED_MOD_SERVER_ID
            and ctx.author.guild_permissions.manage_messages
        )
        if not (is_author or is_mod):
            await ctx.send("You do not have permission to delete this definition. Only the author or a moderator from the allowed server can delete it.")
            c.close()
            conn.close()
            return
        c.execute("DELETE FROM definitions WHERE id = %s", (entry['id'],))
        conn.commit()
        c.close()
        conn.close()
        await ctx.send(f"Definition #{serial} for **{title}** deleted.")

async def setup(bot):
    print("DefinitionCog setup called")
    await bot.add_cog(DefinitionCog(bot)) 