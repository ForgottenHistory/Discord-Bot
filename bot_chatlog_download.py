import discord
import json

# Create a client object
intents = discord.Intents().all()
client = discord.Client(intents=intents)

with open(f"./settings.json", "r") as f:
    settings = json.load(f)
bot_token = settings["discord_token"]

# Set the target channel ID
print("Input channel ID:")
channel_id = input()

# Handle the 'ready' event
@client.event
async def on_ready():
    global channel_id
    channel = client.get_channel(channel_id)
    print("Downloading...")
    with open("./dataset/chatlog.txt", "w", encoding='utf-8') as file:
        async for message in channel.history(limit=10000000):
            file.write(f"{message.author}: {message.content}\n")
    print("Downloaded!")

# Start the client
client.run(bot_token)
