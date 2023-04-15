import discord, re, random
from discord.ext import commands
import aiohttp
import json
import os
from os import listdir
from os.path import isfile, join
import asyncio
import sys
import requests
from commands.change_personality import change_personality

sys.path.append('E:/Coding/Discord-Bot')
from reply import generate_response, reply_to_message
from utility import load_list_from_file, create_directory_if_not_exists, load_settings, extract_keywords_POS, generate_image
from config import admin_users_file, json_dir, settings_file

########################################################################
# DISCORD BOT USING KOBOLD AI
########################################################################

# Make paths if they do not exist
directories = ["./downloads", "./generated_images", "./json", "./relations"]
for dir_path in directories:
    create_directory_if_not_exists(dir_path)

# Load admin users
admin_users = load_list_from_file(admin_users_file)
admin_users = [int(x) for x in admin_users]

# Load character
counter = 0
jsonFiles = [f for f in listdir(json_dir) if isfile(join(json_dir, f))]
for f in jsonFiles:
    counter += 1
    print( str(counter) + ". " + str(f))

print("Which file to load?")
file_index = int(input())

#Discord client setup
with open(f"./settings.json", "r") as f:
    settings = json.load(f)

sampler_order = [6,0,1,2,3,4,5]
this_settings = { 
    "prompt": " ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": 1600,
    "max_length": 50,
    "rep_pen": 1.08,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 1.0,
    "tfs": 0.9,
    "top_a": 0,
    "top_k": 0,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": sampler_order,
    "singleline": False
}

bot_settings = {
    "char_name": "",
    "preprompt": "",
    "use_greeting": True,
    "memory": [],
    "people_memory": {"meanie": 7.0},
    "message_counter": 0,
    "sleeping": False,
    "previous_response": None,
    "this_settings": this_settings,
    "settings": settings
}

print("Starting bot...")

########################################################################

bot_settings["use_greeting"] = settings["use_greeting"]
bot_settings["this_settings"] = load_settings(settings_file)
bot_settings["jsonFiles"] = jsonFiles

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!!', intents=intents)

bot_settings["client"] = client

########################################################################

async def reply_with_gif(message):
    global bot_settings
    reply = generate_response(f"{message.content}", message.author.name, bot_settings)
    #bot_settings["memory"].pop(-1)
        
    keywords = extract_keywords_POS(reply)
    if len(keywords) == 0:
        bot_settings["memory"].pop(-1)
        #await reply_to_message(message)
        await message.channel.send(reply, reference=message, mention_author=False)
        return
    
    print(keywords)

    string = ""
    counter = 0
    for word in keywords:
        string += f"{word} "
        counter += 1
        if counter >= 5:
            break

    api_key = bot_settings["settinfgs"]["tenor_api_key"]
    client_key = "discord_bot"
    url = f"https://tenor.googleapis.com/v2/search?q={string}&key={api_key}&client_key={client_key}&limit={1}"
    
    response = requests.get(url)

    if response.status_code == 200:
        gifs = json.loads(response.content)
        url = gifs["results"][0]["media_formats"]["gif"]["url"]
        print("Sent " + url)
        embed = discord.Embed()
        embed.url = url
        embed.set_image(url=url)
        await message.channel.send(f"{reply}\n {url}", reference=message, mention_author=False)
    else:
        print("Error")

########################################################################
# IMAGES

async def reply_with_generated_image(message):
    global bot_settings

    reply = generate_response(message.content, message.author.name, bot_settings)
    #bot_settings["memory"].pop(-1)

    keywords = extract_keywords_POS(message.content + " " + reply)
    if len(keywords) == 0:
        bot_settings["memory"].pop(-1)
        #await reply_to_message(message)
        await message.channel.send(reply, reference=message, mention_author=False)
        return
    
    print(keywords)

    string = ""
    for word in keywords:
        string += f"{word} "
        
    image_file = generate_image(string)
    print(image_file)
    await message.channel.send(f"{reply}", file=discord.File(image_file), reference=message, mention_author=False)

########################################################################
# ADD ONE MESSAGE TO MEMORY

def add_message_to_memory(message):
    global bot_settings
    
    # Clean the message content
    prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
    prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
    bot_settings["memory"].append(f"{message.author.name}: {prompt}")
    while len(bot_settings["memory"]) > bot_settings["settings"]["memory_length"]:
        bot_settings["memory"].pop(0) # remove oldest message if memory is full

    
########################################################################

def should_reply(message, bot_settings):
    return (
        message.channel.id == bot_settings["settings"]["channelID"]
        and bot_settings["sleeping"] == False
        and message.content
        and not message.content.startswith(("!", "<", "http"))
    )

async def process_admin_commands(message, bot_settings):
    print("test")

@bot_settings["client"].event
async def on_message(message):
    global bot_settings
    global admin_users

    # No reply to itself
    if message.author == bot_settings["client"].user:
        return

    if should_reply(message, bot_settings):
        await handle_reply(message, bot_settings)
    elif message.author.id in admin_users and message.content.startswith("!!"):
        await process_admin_commands(message, bot_settings)

async def handle_reply(message, bot_settings):
    if "make an image" in message.content.lower():
        send_gif_roll = 0.0
        send_image_roll = 1.1
    else:
        send_gif_roll = random.uniform(0, 1)
        send_image_roll = random.uniform(0, 1)

    if send_gif_roll > bot_settings["settings"]["gif_rate"] and bot_settings["settings"]["use_gifs"] == True:
        add_message_to_memory(message)
        await reply_with_gif(message)
    elif send_image_roll > bot_settings["settings"]["image_rate"] and bot_settings["settings"]["use_images"] == True:
        add_message_to_memory(message)
        await reply_with_generated_image(message)
    else:
        await reply_to_message(message, bot_settings)

def load_commands():
    for file in os.listdir("commands"):
        if file.endswith(".py"):
            command_name = file[:-3]
            bot_settings["client"].load_extension(f"commands.{command_name}")

########################################################################
      
@bot_settings["client"].event
async def on_ready():
    global file_index
    
    print(f'{bot_settings["client"].user} has connected to Discord!')
    load_commands()
    await change_personality(file_index, bot_settings)

########################################################################


bot_settings["client"].run(settings["discord_token"])
