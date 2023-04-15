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
from utility import load_list_from_file, create_directory_if_not_exists, load_settings, extract_keywords_POS, generate_image, check_response_text, fix_relations, find_float_or_int
from utility import check_response_error
from config import banned_words_file, admin_users_file, json_dir, settings_file

########################################################################
# DISCORD BOT USING KOBOLD AI
########################################################################

# Make paths if they do not exist
directories = ["./downloads", "./generated_images", "./json", "./relations"]
for dir_path in directories:
    create_directory_if_not_exists(dir_path)
    
# Load words that will NOT be said
word_list = load_list_from_file(banned_words_file)

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

########################################################################
# Change personality
    
########################################################################
        
async def post_request(url, json_data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data, headers=headers) as response:
            data = await response.json()
            return data

########################################################################     
# Generate the response

async def generate_response(prompt, user):
    global bot_settings
    global word_list

    char_name = bot_settings["char_name"]

    if len(bot_settings["memory"]) == 0 or bot_settings["memory"][-1] != f"{user}: {prompt}":
        bot_settings["memory"].append(f"{user}: {prompt}")
    while len(bot_settings["memory"]) > bot_settings["settings"]["memory_length"]:
        bot_settings["memory"].pop(0) # remove oldest message if memory is full

    prepromt_fixed = fix_relations(bot_settings["preprompt"], bot_settings["people_memory"])

    ###################################################################
    
    # Concatenate the most recent messages in memory to use as the prompt
    new_prompt = prepromt_fixed + "\n"
    new_prompt += "\n".join(f"{mem}" for mem in bot_settings["memory"]) + f"\n{char_name}: "
    #print(f"\n" + new_prompt)
    
    bot_settings["this_settings"]["prompt"] = new_prompt
    headers = {"Content-Type": "application/json"}
    url = settings["api_server"] + "/api/v1/generate"
    try:
        response = await post_request(url, bot_settings["this_settings"], headers)
        print(response)
    except Exception as e:
        print(f"Error while making a post request: {e}")
        return "I'm sorry, I couldn't generate a response."

    # Response code check
    #check_response_error(response)
    
    ###################################################################
    
    # Clean up response
    try:
        response_text = response['results'][0]['text']
        response_lines = response_text.split("\n")
    except KeyError:
        print("Error: Unexpected response format.")
        return "I'm sorry, I couldn't generate a response."
    
    print("Character name: " + char_name)
    print(f"Response lines: \n" + str(response_lines))
     
    if response_lines[0] == "":
        return "I'm sorry, I couldn't generate a response."
    
    print(user)
    if response_lines[0].split(":")[0].lower() == user.lower():
        response_text = generate_response(prompt, user)
    elif response_lines[0].split(":")[-1] == '':
        response_text = generate_response(prompt, user)
    elif response_lines[0].split(":")[-1] != '': #and response_lines[x].split(":")[0] == char_name:
        response_text = response_lines[0].split(":")[-1]
    
    ###################################################################
    
    for word in word_list:
        response_text = response_text.replace(word, "%%%%")

    ###################################################################
    # Check if response text is not correct
    # Sends a default response if no
    check_response_text(prompt, response_text, bot_settings["previous_response"], char_name, bot_settings["memory"])

    response_text = re.sub(r'"', '', response_text)
    bot_settings["previous_response"] = response_text
    return response_text

########################################################################
# REPLY TO MESSAGES
########################################################################
# TEXT

async def reply_to_message(message):
    global bot_settings
    
    # Clean the message content
    prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
    #prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
    # Generate rating on user
    response_text = await generate_response(prompt, message.author.name)
    bot_settings["message_counter"] += 1
    if bot_settings["message_counter"] >= 20:
        bot_settings["message_counter"] = 0
        rating_response = await generate_response(f"What would you rate the user {message.author.name} on a scale of 0 to 10", "SYSTEM")
        print(rating_response)
        # Remove SYSTEM and response from existance
        bot_settings["memory"].pop(-1)
        bot_settings["memory"].pop(-1)
        rating_value = find_float_or_int(rating_response)

        if rating_value != None:
            bot_settings["people_memory"][message.author.name] = rating_value
            char_name = bot_settings["char_name"]
            with open(f"./relations/{char_name}.json", "w") as outfile:
                json.dump(bot_settings["people_memory"], outfile)

    # Send response message
    bot_settings["sleeping"] = True
    await asyncio.sleep(settings["message_cooldown"])
    bot_settings["sleeping"] = False
    await message.channel.send(response_text, reference=message, mention_author=False)

########################################################################
# GIFS

async def reply_with_gif(message):
    global bot_settings
    reply = generate_response(f"{message.content}", message.author.name)
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

    reply = generate_response(message.content, message.author.name)
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
        await reply_to_message(message)

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
