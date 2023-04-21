import discord, re, random
from discord.ext import commands
import json
import os
from os import listdir
from os.path import isfile, join
import sys
import asyncio
from commands.__commands__ import *
from commands.change_personality import change_personality

sys.path.append('E:/Coding/Discord-Bot')
from reply import generate_response, reply_to_message, reply_with_generated_image, reply_with_gif, should_reply
from utility import load_list_from_file, create_directory_if_not_exists, load_settings
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
    "settings": settings,
    "author_note": "",
}

print("Starting bot...")

########################################################################

bot_settings["use_greeting"] = settings["use_greeting"]
bot_settings["this_settings"] = load_settings(settings_file)
bot_settings["jsonFiles"] = jsonFiles

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!', intents=intents)

bot_settings["client"] = client

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

async def process_admin_commands(message, bot_settings):
    await process_input(message, bot_settings)

@bot_settings["client"].event
async def on_message(message):
    global bot_settings
    global admin_users

    # No reply to itself
    if message.author == bot_settings["client"].user:
        return

    if bot_settings["sleeping"]:
        return

    if should_reply(message, bot_settings):
        print(message.content)
        await handle_reply(message, bot_settings)
        await asyncio.sleep(5)
        bot_settings["sleeping"] = False
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
        await reply_with_gif(message, bot_settings)
    elif send_image_roll > bot_settings["settings"]["image_rate"] and bot_settings["settings"]["use_images"] == True:
        add_message_to_memory(message)
        await reply_with_generated_image(message, bot_settings)
    else:
        await reply_to_message(message, bot_settings)

########################################################################
      
@bot_settings["client"].event
async def on_ready():
    global file_index
    
    print(f'{bot_settings["client"].user} has connected to Discord!')
    await change_personality(file_index, bot_settings)

########################################################################

bot_settings["client"].run(settings["discord_token"])