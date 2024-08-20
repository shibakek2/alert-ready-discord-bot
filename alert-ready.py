import socket
import xml.etree.ElementTree as ET
import discord
from discord.ext import commands
import json
import os
import logging
import threading
import asyncio

logging.basicConfig(level=logging.INFO)
SERVER_ADDRESS = 'streaming.naad-adna.pelmorex.com'
PORT = 8080
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
NUM_SHARDS = 3
OWNER_ID = 876913688924266607
test_alert_channel_id = 1272032783329398965
bot_token = 'put token here'
client =commands.Bot(command_prefix='!', intents=intents)

DM_FILE = 'dms.json'

def load_dm_data():
    if os.path.exists(DM_FILE):
        with open(DM_FILE, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_dm_data(data):
    with open(DM_FILE, 'w') as f:
        json.dump(data, f, indent=4)

if not os.path.exists('servers.json'):
    with open('servers.json', 'w') as f:
        json.dump({}, f)

def save_server_data(server_id, heartbeat_channel_id, alerts_channel_id):
    with open('servers.json', 'r+') as f:
        data = json.load(f)
        data[server_id] = {
            'heartbeat_channel_id': heartbeat_channel_id,
            'alerts_channel_id': alerts_channel_id
        }
        f.seek(0)
        json.dump(data, f)
        f.truncate()

async def create_and_save_channels(guild):
    heartbeat_channel = discord.utils.get(guild.channels, name='heartbeat')
    alerts_channel = discord.utils.get(guild.channels, name='alerts')

    if not heartbeat_channel:
        heartbeat_channel = await guild.create_text_channel('heartbeat')
    if not alerts_channel:
        alerts_channel = await guild.create_text_channel('alerts')

    save_server_data(str(guild.id), str(heartbeat_channel.id), str(alerts_channel.id))
    return heartbeat_channel, alerts_channel

@client.event
async def on_guild_join(guild):
    logging.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    await create_and_save_channels(guild)

@client.command()
async def setup(ctx):
    logging.info(f"Setup command invoked by {ctx.author}")
    server_id = str(ctx.guild.id)
    with open('servers.json', 'r') as f:
        data = json.load(f)

    if server_id in data:
        await ctx.send("Channels are already set up for this server.")
        return

    logging.info(f"Setting up channels for guild: {ctx.guild.name} (ID: {ctx.guild.id})")
    await create_and_save_channels(ctx.guild)
    await ctx.send("Channels `heartbeat` and `alerts` have been created and set up.")


def parse_xml_data(xml_str):
    try:
        namespaces = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        root = ET.fromstring(xml_str)
        print(xml_str)
        identifier = root.find('cap:identifier', namespaces).text
        sender = root.find('cap:sender', namespaces).text
        sent = root.find('cap:sent', namespaces).text
        status = root.find('cap:status', namespaces).text
        msg_type = root.find('cap:msgType', namespaces).text
        source = root.find('cap:source', namespaces).text
        scope = root.find('cap:scope', namespaces).text
        code = root.find('cap:code', namespaces).text
        if sender == 'NAADS-Heartbeat':
            channel_name = 'heartbeat'
        else:
            channel_name = 'alerts'
        embed = discord.Embed(title=f"Alert: {identifier}", color=0x00ff00)
        embed.add_field(name="Sender", value=sender, inline=False)
        embed.add_field(name="Sent", value=sent, inline=False)
        embed.add_field(name="Status", value=status, inline=False)
        embed.add_field(name="Message Type", value=msg_type, inline=False)
        embed.add_field(name="Source", value=source, inline=False)
        embed.add_field(name="Scope", value=scope, inline=False)
        embed.add_field(name="Code", value=code, inline=False)
        for guild in client.guilds:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel:
                client.loop.create_task(channel.send(embed=embed))

        logging.info(f"Processed message from sender: {sender}")
    except ET.ParseError as e:
        logging.error(f"XML parsing error: {e}")

def connect_to_tcp_stream():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((SERVER_ADDRESS, PORT))
            logging.info(f"Connected to {SERVER_ADDRESS}:{PORT}")
            while True:
                data = sock.recv(4096)
                if not data:
                    break
                xml_str = data.decode('utf-8', errors='replace')
                logging.info("Received XML data:")
                parse_xml_data(xml_str)

        except socket.error as e:
            logging.error(f"Socket error: {e}")

def start_tcp_stream_thread():
    tcp_thread = threading.Thread(target=connect_to_tcp_stream, daemon=True)
    tcp_thread.start()

@client.command()
async def customhelp(ctx):
    embed = discord.Embed(title="Alert Ready Help", color=0x00ff00)
    embed.add_field(name="Discord Server", value="For Questions/Support join our discord server > discord.gg/EB694pE2ht", inline=False)
    await ctx.send(embed=embed)

async def status_loop():
    while True:
        try:
            activity = discord.Activity(type=discord.ActivityType.watching, name="NAADS")
            await client.change_presence(activity=activity)
            await asyncio.sleep(5)
            num_servers = len(client.guilds)
            activity = discord.Activity(type=discord.ActivityType.watching, name=f"{num_servers} Servers")
            await client.change_presence(activity=activity)
        except Exception as e:
            logging.error(f"Status loop error: {e}")

@client.command(name="test_alert", description="Send a test alert to all 'alerts' channels.")
async def test_alert(ctx, *, message: str):
    if ctx.author.id != OWNER_ID:
        await ctx.send("You do not have permission to use this command.")
        return
    embed = discord.Embed(title="Test Alert", color=0x00ff00)
    embed.add_field(name="Message", value=message, inline=False)
    embed.add_field(name="Authorized User", value=str(ctx.author), inline=False)
    try:
        with open('servers.json', 'r') as f:
            data = json.load(f)
    except Exception as e:
        await ctx.send("An error occurred while loading server data.")
        logging.error(f"Failed to load servers.json: {e}")
        return
    channel_ids = [details['alerts_channel_id'] for details in data.values()]

    if not channel_ids:
        await ctx.send("No alerts channels found.")
        logging.info("No alerts channels found in servers.json.")
        return

    for channel_id in channel_ids:
        guild_id = next((k for k, v in data.items() if v['alerts_channel_id'] == channel_id), None)
        if guild_id:
            guild = client.get_guild(int(guild_id))
            if guild:
                logging.info(f"Found guild: {guild.name} (ID: {guild.id})")
                channel = guild.get_channel(int(channel_id))
                if channel:
                    logging.info(f"Found channel: {channel.name} (ID: {channel.id})")
                    try:
                        await channel.send(embed=embed)
                        logging.info(f"Sent test alert to channel {channel_id} in guild {guild.name} (ID: {guild.id})")
                        await asyncio.sleep(3)
                    except discord.Forbidden:
                        await ctx.send(f"Permission denied when sending message to channel {channel_id}.")
                        logging.error(f"Permission denied when sending message to channel {channel_id}.")
                    except discord.HTTPException as e:
                        await ctx.send(f"Failed to send message to channel {channel_id}: {e}")
                        logging.error(f"Failed to send message to channel {channel_id}: {e}")
                    except Exception as e:
                        await ctx.send(f"Unexpected error when sending message to channel {channel_id}: {e}")
                        logging.error(f"Unexpected error when sending message to channel {channel_id}: {e}")
                else:
                    await ctx.send(f"Channel with ID {channel_id} not found.")
                    logging.warning(f"Channel with ID {channel_id} not found in guild {guild.name}.")
            else:
                await ctx.send(f"Guild with ID {guild_id} not found.")
                logging.warning(f"Guild with ID {guild_id} not found.")
        else:
            await ctx.send(f"No guild found for Channel ID {channel_id}.")
            logging.warning(f"No guild found for Channel ID {channel_id}.")

    await ctx.send("Test alerts have been sent.")



@client.command(name="test_single_alert")
async def test_single_alert(ctx, *, message: str):
    channel_id = test_alert_channel_id
    channel = client.get_channel(channel_id)
    if channel:
        try:
            await channel.send(message)
            await ctx.send(f"Message sent to channel ID {channel_id}.")
        except Exception as e:
            await ctx.send(f"Failed to send message: {e}")
    else:
        await ctx.send("Channel not found.")

@client.event
async def on_ready():
    logging.info(f"Logged in as {client.user}")
    start_tcp_stream_thread()
    await status_loop()

@client.command(name="view_conversations")
async def view_conversations(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("You do not have permission to use this command.")
        return
    dm_data = load_dm_data()
    if not dm_data:
        await ctx.send("No conversations found.")
        return
    MAX_EMBED_FIELDS = 25
    FIELD_VALUE_LENGTH = 1024

    def split_into_chunks(text, chunk_size):
        """Utility function to split a long text into chunks."""
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    embeds = []
    current_embed = discord.Embed(title="Saved Conversations", color=0x00ff00)
    current_field_count = 0
    for user_id, conversation in dm_data.items():
        try:
            user = await client.fetch_user(int(user_id))
            messages = ""
            for msg in conversation['messages']:
                role = msg['role'].capitalize()
                content = msg['content']
                messages += f"{role}: {content}\n"
            message_chunks = split_into_chunks(messages, FIELD_VALUE_LENGTH)
            for chunk in message_chunks:
                if current_field_count >= MAX_EMBED_FIELDS:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(title="Saved Conversations", color=0x00ff00)
                    current_field_count = 0
                current_embed.add_field(name=f"Conversation with {user}", value=chunk, inline=False)
                current_field_count += 1
        except discord.NotFound:
            continue

    if len(current_embed.fields) > 0:
        embeds.append(current_embed)

    for embed in embeds:
        await ctx.send(embed=embed)



@client.event
async def on_message(message):
    if message.author == client.user:
        return  
    dm_data = load_dm_data()
    if isinstance(message.channel, discord.DMChannel):
        user_id = str(message.author.id)
        if user_id not in dm_data:
            dm_data[user_id] = {'messages': []}
        dm_data[user_id]['messages'].append({
            'role': f'{message.author}',
            'content': message.content,
            'timestamp': str(message.created_at)
        })

        save_dm_data(dm_data)
        if message.author.id != OWNER_ID:
            owner = await client.fetch_user(OWNER_ID)
            if owner:
                try:
                    await owner.send(f"Message from {message.author} ({message.author.id}): {message.content}")
                    logging.info(f"Forwarded DM from {message.author} to owner.")
                except Exception as e:
                    logging.error(f"Failed to forward DM: {e}")
        if message.reference:
            ref_message = message.reference.cached_message
            if ref_message:
                ref_user_id = str(ref_message.author.id)
                if ref_user_id in dm_data:
                    dm_data[ref_user_id]['messages'].append({
                        'role': 'bot',
                        'content': message.content,
                        'timestamp': str(message.created_at)
                    })
                    save_dm_data(dm_data)
    await client.process_commands(message)

@client.event
async def on_message_edit(before, after):
    if before.author == client.user:
        return
    if isinstance(after.channel, discord.DMChannel) and before.author.id == OWNER_ID:
        original_message = before.content
        if original_message:
            try:
                await after.author.send(f"Your message was edited:\n{original_message}\n\nNew content:\n{after.content}")
                logging.info(f"Forwarded edited DM to {after.author}.")
            except Exception as e:
                logging.error(f"Failed to forward edited DM: {e}")


@client.event
async def on_command_error(ctx, error):
    logging.error(f"Error occurred: {error}")
    await ctx.send(f"An error occurred: {error}")

if __name__ == "__main__":
    client.run(bot_token)

