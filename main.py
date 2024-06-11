import discord
import discord.ext
import random
import math
from datetime import datetime, UTC
from dotenv import load_dotenv, dotenv_values
import os, json, re
from time import sleep
from tinydb import TinyDB, Query, operations
from io import StringIO
from conf.tickettranscripts import *

from html import escape

ignored_keys = {'role_id', 'category_id', 'ticket_count'}
with open('challenges.json','r') as f:
    CHALLENGES=json.load(f)
db = TinyDB('db.json')
query = Query()


def remove_ignored_keys(data, keys_to_ignore):
    if isinstance(data, list):
        return [i for i in [remove_ignored_keys(item, keys_to_ignore) for item in data] if i]
    elif isinstance(data, dict):
        return {k: remove_ignored_keys(v, keys_to_ignore) for k, v in data.items() if k not in keys_to_ignore}
    else:
        return data

challenges_data_cleaned = remove_ignored_keys(CHALLENGES, ignored_keys)
db_data_cleaned = remove_ignored_keys(db.all(), ignored_keys)

if not db.all():
    db.insert_multiple(CHALLENGES)
    db_data_cleaned = remove_ignored_keys(db.all(), ignored_keys)
if not challenges_data_cleaned == db_data_cleaned:
    print('---\n\nWARNING: If you have changed challenges.json and you have ran this bot before, delete db.json, there will be errors otherwise. This will also erase your current structure, ids and ticket count so make sure to run /rmsetup beforehand.\n\n---')

def sanitize_html(html_string):
    return escape(html_string, quote=True)

def convert_bytes_to_best_size(bytes_num):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    index = 0
    while bytes_num >= 1024 and index < len(suffixes) - 1:
        bytes_num /= 1024.0
        index += 1
    return "{:.1f} {}".format(bytes_num, suffixes[index])

def html_beautify(text):
    if '```' in text:
        code_blocks = text.split('```')
        
        formatted_text = ""
        for i in range(1, len(code_blocks), 2):
            lang = code_blocks[i].split('\n')[0].strip()
            code_content = code_blocks[i].split('\n')
            code_content[0] = ""
            code_content = '\n'.join(code_content).strip()
            if lang == "":
                formatted_code_block = f'<pre class="codeblock" is="message-codeblock"><div class="shitcode"><div class="lines"></div><code class="hljs">{code_content}</code></div><div class="copy">Copy</div></pre>'
            else:
                formatted_code_block = f'<pre class="codeblock" is="message-codeblock"><div class="lang">{lang}</div><div class="shitcode"><div class="lines"></div><code class="hljs {lang}">{code_content}</code></div><div class="copy">Copy</div></pre>'
            formatted_text += formatted_code_block
        text = formatted_text
    if '~~' in text:
        pattern = r'~~(.*?)~~'
        text = re.sub(pattern, r'<s>\1</s>', text, flags=re.DOTALL)
    if '**' in text:
        pattern = r'\*\*(.*?)\*\*'
        text = re.sub(pattern, r'<b>\1</b>', text, flags=re.DOTALL)
    if '__' in text:
        pattern = r'\_\_(.*?)\_\_'
        text = re.sub(pattern, r'<ins>\1</ins>', text, flags=re.DOTALL)
    if '*' in text:
        pattern = r'\*(.*?)\*'
        text = re.sub(pattern, r'<i>\1</i>', text, flags=re.DOTALL)
    if '_' in text:
        pattern = r'\_(.*?)\_'
        text = re.sub(pattern, r'<i>\1</i>', text, flags=re.DOTALL)
    if '`' in text:
        pattern = r'`(.*?)`'
        text = re.sub(pattern, r'<code>\1</code>', text, flags=re.DOTALL)
    return text

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ORGANISER_ROLE_ID = int(os.getenv("ORGANISER_ROLE_ID"))
DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY = bool(int(os.getenv("DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY")))
DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY_FORMAT = os.getenv("DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY_FORMAT")
BOT_ROLE_ID = 0

description = '''A CTF-specific Ticketing Bot.

Made by se.al / sealldeveloper'''

def clean_string(input_string):
    cleaned_string = re.sub(r'[^a-z0-9- ]+', '', input_string)
    return cleaned_string

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@tree.command(name="setup", description="Using the configuration provided, create all required roles/categories and setup DB.",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction):    
    await interaction.response.defer(ephemeral=True)
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    guild = interaction.guild
    organiserrole = discord.utils.get(guild.roles, id=ORGANISER_ROLE_ID)
    if interaction.user.guild_permissions.administrator or organiserrole in interaction.user.roles:
        botrole = discord.utils.get(guild.roles, id=BOT_ROLE_ID)
        for cat in range(len(CHALLENGES)):
            await interaction.edit_original_response(content=f'Working on {CHALLENGES[cat]["name"]}...')
            database_element = db.all()[cat]
            if 'role_id' in database_element or 'category_id' in database_element:
                return await interaction.edit_original_response(content=f'Run `/rmsetup` first before re-running setup!')
            try:
                
                role = await guild.create_role(name=CHALLENGES[cat]["name"])
                col = discord.Color(5860729)
                await role.edit(color=col)
                db.update({'role_id':role.id},doc_ids=[database_element.doc_id])
                
            except:
                return await interaction.edit_original_response(content=f'Could not create/manage new role for challenge category `{CHALLENGES[cat]["name"]}`!')
            if DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY and DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY_FORMAT:
                catname = DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY_FORMAT.replace('<CATEGORY>',CHALLENGES[cat]["name"],1)
                try:
                    category = await guild.create_category(catname)
                    db.update({'category_id':category.id},doc_ids=[database_element.doc_id])
                except:
                    return await interaction.edit_original_response(content=f'Could not create the new category for challenge category `{catname}`!')
                try:
                    await category.set_permissions(botrole, read_messages=True, send_messages=True)
                    await category.set_permissions(guild.default_role, read_messages=False)
                    await category.set_permissions(organiserrole, read_messages=True, send_messages=True)
                except:
                    return await interaction.edit_original_response(content=f'Could not configure permissions for the new category for challenge category `{catname}`!')
        if not DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY:
            await interaction.edit_original_response(content=f'Creating Tickets category...')
            try:
                for d in db.all():
                    if 'category_id' in d:
                        return await interaction.edit_original_response(content=f'Run `/rmsetup` first before re-running setup!')
                category = await guild.create_category('Tickets')
                for d in db.all():
                    db.update({'category_id':category.id},doc_ids=[d.doc_id])
            except:
                return await interaction.edit_original_response(content=f'Could not create the new category `Tickets`!')
        view = Ticket()
        await interaction.edit_original_response(content=f'Setup complete!')
        await interaction.followup.send(content="Press the button to open the modal with dropdown menus!", view=view)
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

@tree.command(name="rmsetup", description="Remove the current setup.",guild=discord.Object(id=GUILD_ID))
async def slash_command(interaction: discord.Interaction): 
    await interaction.response.defer(ephemeral=True)   
    print(f'[{interaction.user.id}] - ran {interaction.command.name}')
    guild = interaction.guild
    organiserrole = discord.utils.get(guild.roles, id=ORGANISER_ROLE_ID)
    if interaction.user.guild_permissions.administrator or organiserrole in interaction.user.roles:
        for d in db.all():
            if "name" in d.keys():
                await interaction.edit_original_response(content=f'Working on {d["name"]}...')
                if 'category_id' in d.keys():
                    category = discord.utils.get(guild.categories, id=d['category_id'])
                    if category:
                        for channel in category.channels:
                            try:
                                await channel.delete()
                            except:
                                return await interaction.edit_original_response(content=f'Ticket Category `{d["category_id"]}` could not delete the channel <#{channel.id}>.')
                        try:
                            await category.delete()
                        except:
                            return await interaction.edit_original_response(content=f'Ticket Category `{d["category_id"]}` could not be deleted.')
                    db.update(operations.delete('category_id'),doc_ids=[d.doc_id])
                if 'role_id' in d.keys():
                    role = discord.utils.get(guild.roles, id=d['role_id'])
                    if role:
                        try:
                            await role.delete()
                        except:
                            return await interaction.edit_original_response(content=f'Ticket Role `{d["role_id"]}` could not be deleted.')
                    db.update(operations.delete('role_id'),doc_ids=[d.doc_id])
        db.update({'ticket_count': 0})
        await interaction.edit_original_response(content=f'Setup removal complete!')
    else:
        return await interaction.edit_original_response(content='You are not an admin!')

@client.event
async def on_ready():
    print(f'Syncing trees...')
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f'Finding the bots role...')
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    for role in guild.roles:
        if len(role.members) == 1 and role.members[0].id == client.user.id and role.permissions.administrator:
            global BOT_ROLE_ID
            BOT_ROLE_ID = role.id
            break
    if BOT_ROLE_ID == 0:
        print('---\n\nWARNING: No bot role found! Please make sure there is a role unique to the bot with Admin permissions! Things will break!\n\n---')
    print('Registering modal views...')
    client.add_view(Ticket())
    client.add_view(CategorySelectView())
    client.add_view(CloseTicketView())
    client.add_view(SubOptionSelectView([discord.SelectOption(label="placeholder", description="placeholder")],""))
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        transcript = StringIO()
        transcript.write(f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta http-equiv="X-UA-Compatible" content="ie=edge"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><title>#{interaction.channel.name} Transcript</title>""")
        transcript.write(TICKET_HEADER)
        transcript.write(f"""<span class="name">{interaction.channel.name}</span><theme-switch></theme-switch></header><main><div class="placeholder"></div><div class="welcome"><h1>Welcome to <b>#{interaction.channel.name}</b>!</h1><div>This is the start of the #{interaction.channel.name} channel.</div></div><discord-messages>""")
        messages = []
        async for message in interaction.channel.history(limit=None):
            timestamp = datetime.fromtimestamp(message.created_at.timestamp(), UTC)
            message.content = html_beautify(sanitize_html(message.content)).replace('\n','<br>')
            to_append = ""
            to_append += f"""<discord-message data-id="0" data-author="{message.author.id}" class="group-start"><img is="message-avatar" src="{message.author.display_avatar.with_size(512).url}" data-discriminator="0000" alt="avatar" class="avatar" onerror="this.onerror=null;this.src='https://cdn.discordapp.com/embed/avatars/0.png';"><message-date class="time" data-type="time" data-timestamp="{message.created_at}">{timestamp.strftime('%H:%M')}</message-date><div class="contents"><message-header><span class="name">{message.author.display_name}</span><span class="badge"></span><message-date class="date" data-type="date" data-timestamp="{message.created_at}">{timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')}</message-date></message-header><message-markup>{message.content}</message-markup>"""
            if len(message.attachments) > 0:
                for attachment in message.attachments:
                    to_append += f"""<message-attachment class><div class="data"><img src="https://discord.com/assets/985ea67d2edab4424c62009886f12e44.svg" alt class="icon"><div class="details"><a href="{attachment.url}" target="_blank">{attachment.filename}</a><span>{convert_bytes_to_best_size(attachment.size)}</span></div><a href="{attachment.url}" target="_blank" class="download"><svg width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" /></svg></a></div></message-attachment>"""
                to_append += """</div>"""
            to_append += """</div></discord-message>"""
            messages.append(to_append)
        for x in reversed(messages):
            transcript.write(x)
        createdtimestamp = datetime.fromtimestamp(message.created_at.timestamp(), UTC)
        transcript.write(f"""</discord-messages></main><footer><span>This archive was generated on the&nbsp;<message-date data-type="full" data-timestamp="{interaction.created_at}">{createdtimestamp.strftime('%d %b %Y at %H:%M:%S Coordinated Universal Time')}</message-date></span></footer></body></html>""")
        transcript.seek(0)
        file = discord.File(transcript, filename="ticket_transcript.html")
        overwrites = interaction.channel.overwrites
        user = None
        for target, overwrite in overwrites.items():
            if isinstance(target,discord.object.Object):
                user = await interaction.guild.fetch_member(target.id)
                await user.send("Here is the transcript of your ticket:", file=file)
        await interaction.response.send_message("Transcript of the ticket sent to your DMs! Deleting channel in 10 seconds...", ephemeral=True)
        sleep(10)
        return await interaction.channel.delete()
        

        

class Ticket(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Create a ticket", style=discord.ButtonStyle.primary, custom_id="ticket_create",emoji="🎫")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select a challenge category:", view=CategorySelectView(), ephemeral=True)


class CategorySelectView(discord.ui.View):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(timeout=None)
        self.add_item(CategorySelect())

    async def on_timeout(self):
        pass

class CategorySelect(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        options = []
        for cat in CHALLENGES:
            options.append(discord.SelectOption(label=cat["name"], description=f"The challenges in the {cat['name']} category."))
        super().__init__(placeholder="Challenge Category", options=options, custom_id="category_select", *args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        challenge_options = []
        for cat in CHALLENGES:
            if cat['name'] == selected_option:
                for chal in cat['challenges']:
                    challenge_options.append(
                        discord.SelectOption(label=chal['name'], description=f"The challenge {chal['name']} in the {cat['name']} category.")
                    )
                break

        await interaction.response.edit_message(content=f"Selected Category: `{selected_option}`.", view=SubOptionSelectView(challenge_options, selected_option))

class SubOptionSelectView(discord.ui.View):
    def __init__(self, options, selected_category, *args, **kwargs) -> None:
        super().__init__(timeout=None)
        self.add_item(SubOptionSelect(options, selected_category))
        self.add_item(GoBackButton(selected_category))
    async def on_timeout(self):
        pass

class GoBackButton(discord.ui.Button):
    def __init__(self, selected_category):
        super().__init__(label="Go Back", style=discord.ButtonStyle.secondary, custom_id="go_back", row=1)
        self.selected_category = selected_category

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"Select a challenge category:", view=CategorySelectView())

class SubOptionSelect(discord.ui.Select):
    def __init__(self, options, selected_category, *args, **kwargs):
        super().__init__(placeholder="Select a challenge:", options=options, custom_id="challenge_select", *args, **kwargs)
        self.selected_category = selected_category

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        selected_category = self.selected_category
        await interaction.response.edit_message(content=f"You selected: `{selected_option}` from the category `{selected_category}`. Creating ticket...", view=None)
        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        for cat in range(len(CHALLENGES)):
            if selected_category == CHALLENGES[cat]['name']:
                db_elem = db.all()[cat]
                category = discord.utils.get(guild.categories, id=db_elem['category_id'])
                if not db.search(query.ticket_count.exists()):
                    db.insert({'ticket_count': 0})
                db.update({'ticket_count': db.get(query.ticket_count.exists())['ticket_count'] + 1})
                ticket_number = db.get(query.ticket_count.exists())['ticket_count']
                ticket = await category.create_text_channel(name=f'ticket-{ticket_number}')

                await ticket.set_permissions(interaction.user, read_messages=True, send_messages=True)

                initial_message = f"Ticket about challenge `{selected_option}` from the category `{selected_category}`. The ticket belongs to <@{interaction.user.id}> (`{interaction.user.id}`)."
                if 'ping_creators' in db_elem.keys() or 'ping_category' in db_elem.keys():
                    initial_message+="\n\nPing(s): "
                if 'ping_creators' in db_elem.keys():
                    if db_elem['ping_creators'] == True:
                        for chal in db_elem['challenges']:
                            if chal['name'] == selected_option:
                                if 'creators' in chal.keys():
                                    if len(chal['creators']) == 0:
                                        initial_message += "Nobody to ping!"
                                    else:
                                        for creator in chal['creators']:
                                            initial_message += f"<@{creator}> "
                if 'ping_category' in db_elem.keys():
                    if db_elem['ping_category'] == True:
                        role_id = db_elem['role_id']
                        initial_message += f"<@&{role_id}>"
                close_ticket = CloseTicketView()
                await ticket.send(initial_message,view=close_ticket)
                
                await interaction.edit_original_response(content=f"Your ticket has been made! See it here: <#{ticket.id}>")
                sleep(5)
                return await interaction.delete_original_response()
                

# run the bot
client.run(TOKEN)

