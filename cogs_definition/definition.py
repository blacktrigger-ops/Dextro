print("definition.py is being imported")

import discord
from discord.ext import commands
import database

ALLOWED_MOD_SERVER_ID = 1387399782724669470  # Only mods from this server can delete any definition

def ensure_table():
    with database.get_db() as conn:
        c = conn.cursor()
        if database.USE_MYSQL:
            c.execute('''
                CREATE TABLE IF NOT EXISTS definitions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    author_id VARCHAR(32) NOT NULL,
                    definition TEXT NOT NULL,
                    reference VARCHAR(255) DEFAULT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
            try:
                c.execute('ALTER TABLE definitions ADD COLUMN reference VARCHAR(255) DEFAULT NULL')
            except Exception:
                pass
        else:
            c.execute('''
                CREATE TABLE IF NOT EXISTS definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    reference TEXT DEFAULT NULL
                )
            ''')
            try:
                c.execute('ALTER TABLE definitions ADD COLUMN reference TEXT DEFAULT NULL')
            except Exception:
                pass
        conn.commit()

ensure_table()

class DefinitionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                # Parse title, author, reference
                parts = [x.strip() for x in cmd.split('/')]
                title = parts[0] if len(parts) > 0 else None
                author = parts[1] if len(parts) > 1 else None
                reference = parts[2] if len(parts) > 2 else None
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
                with database.get_db() as conn:
                    c = conn.cursor()
                    if database.USE_MYSQL:
                        c.execute("SELECT COUNT(*) FROM definitions WHERE title = %s", (title,))
                    else:
                        c.execute("SELECT COUNT(*) FROM definitions WHERE title = ?", (title,))
                    serial = c.fetchone()[0] + 1
                    if database.USE_MYSQL:
                        c.execute(
                            "INSERT INTO definitions (title, author, author_id, definition, reference) VALUES (%s, %s, %s, %s, %s)",
                            (title, author, str(ref_msg.author.id), definition, reference)
                        )
                    else:
                        c.execute(
                            "INSERT INTO definitions (title, author, author_id, definition, reference) VALUES (?, ?, ?, ?, ?)",
                            (title, author, str(ref_msg.author.id), definition, reference)
                        )
                    conn.commit()
                await message.channel.send(f"Definition for **{title}** by **{author}** saved! Serial: `{serial}`")
                return
            # OUTPUT DEFINITIONS: If not a reply
            if cmd:
                title = cmd
                with database.get_db() as conn:
                    c = conn.cursor()
                    if database.USE_MYSQL:
                        c.execute("SELECT * FROM definitions WHERE title = %s ORDER BY id ASC", (title,))
                    else:
                        c.execute("SELECT * FROM definitions WHERE title = ? ORDER BY id ASC", (title,))
                    definitions = c.fetchall()
                if not definitions:
                    await message.channel.send(f"No definitions found for **{title}**.")
                    return
                current = 0
                def make_embed(idx):
                    entry = definitions[idx]
                    embed = discord.Embed(title="Definition", color=discord.Color.green())
                    if database.USE_MYSQL:
                        embed.add_field(name=f"**{title}**", value=f"**Author:** {entry[2]}\n**Reference:** {entry[5] or 'None'}\n\n{entry[4]}", inline=False)
                    else:
                        embed.add_field(name=f"**{title}**", value=f"**Author:** {entry[2]}\n**Reference:** {entry[5] or 'None'}\n\n{entry[4]}", inline=False)
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
        with database.get_db() as conn:
            c = conn.cursor()
            if database.USE_MYSQL:
                c.execute("SELECT * FROM definitions WHERE title = %s ORDER BY id ASC", (title,))
            else:
                c.execute("SELECT * FROM definitions WHERE title = ? ORDER BY id ASC", (title,))
            definitions = c.fetchall()
            if not definitions or serial < 1 or serial > len(definitions):
                await ctx.send(f"No definition with serial `{serial}` found for **{title}**.")
                return
            entry = definitions[serial - 1]
            is_author = str(ctx.author.id) == entry[3]  # author_id is at index 3
            is_mod = (
                ctx.guild
                and ctx.guild.id == ALLOWED_MOD_SERVER_ID
                and ctx.author.guild_permissions.manage_messages
            )
            if not (is_author or is_mod):
                await ctx.send("You do not have permission to delete this definition. Only the author or a moderator from the allowed server can delete it.")
                return
            if database.USE_MYSQL:
                c.execute("DELETE FROM definitions WHERE id = %s", (entry[0],))
            else:
                c.execute("DELETE FROM definitions WHERE id = ?", (entry[0],))
            conn.commit()
        await ctx.send(f"Definition #{serial} for **{title}** deleted.")

async def setup(bot):
    await bot.add_cog(DefinitionCog(bot)) 