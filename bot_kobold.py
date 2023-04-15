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

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!!', intents=intents)

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

########################################################################

async def send_message(text):
    global client
    global bot_settings
    print(bot_settings["settings"]["channelID"])
    channel = client.get_channel(bot_settings["settings"]["channelID"])
    if text == "":
        text = "Sorry, I could not generate a response"
    await channel.send(text)

########################################################################
# Change personality

async def change_personality(index):
    global jsonFiles
    global bot_settings

    if index > len(jsonFiles) or index < 0:
        return
    
    with open(f"./json/{jsonFiles[index - 1]}", "r") as f:
        data = json.load(f)
    # Access the values
    bot_settings["char_name"] = data["char_name"]
    char_name = data["char_name"]
    char_persona = data["char_persona"]
    char_greeting = data.get("char_greeting", None)
    if char_greeting == None:
        char_greeting = data.get("first_mes", None)
    
    # Check for W++
    match = re.search("[\{\}]", char_persona)
    if match is None:
        char_persona += "[character(\"{}\")\n{{\n}}\n]".format(char_name)
    
    # extract the example_dialogue if present
    example_dialogue = data.get("example_dialogue", None)
    world_scenario = data.get("world_scenario", None)
    
    bot_settings["preprompt"] = f"{char_persona}"
    if example_dialogue is not None:
        bot_settings["preprompt"] +=  f"\nExample dialogue: {example_dialogue}" 
    #if world_scenario is not None and world_scenario != "":
        #preprompt += f"\n{char_name}: {world_scenario}"
    
    bot_settings["memory"] = []
    if bot_settings["preprompt"].endswith("<START>") == False:
        bot_settings["memory"].append("<START>")
    if char_greeting is not None:
        bot_settings["memory"].append(char_greeting)
        
    if isfile(f"./relations/{char_name}.json"):
        with open(f"./relations/{char_name}.json", "r") as f:
            bot_settings["people_memory"] = json.load(f)
            print("Loaded relations.")
    else:
        print("No relations saved")
        with open(f"./relations/{char_name}.json", "w") as outfile:
             json.dump(bot_settings["people_memory"], outfile)
    
    print(bot_settings["preprompt"])
    if bot_settings["use_greeting"] and char_greeting != None:
        await send_message(char_greeting)
    
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

@client.event
async def on_message(message):
    global bot_settings
    global admin_users

    channelID = bot_settings["settings"]["channelID"]
    
    # No reply to itself
    if message.author == client.user:
        return

    # Generate a reply to user message
    if message.channel.id == channelID and bot_settings["sleeping"] == False and message.content[0] != "!" and message.content != "" and message.content.startswith('<') == False and message.content.startswith('http') == False:
        send_gif_roll = random.uniform(0, 1)
        send_image_roll = random.uniform(0, 1)

        if "make an image" in message.content.lower():
            send_image_roll = 1.1
            send_gif_roll = 0.0
        
        if send_gif_roll > bot_settings["settings"]["gif_rate"] and bot_settings["settings"]["use_gifs"] == True:
            add_message_to_memory(message)
            await reply_with_gif(message)
        elif send_image_roll > bot_settings["settings"]["image_rate"] and bot_settings["settings"]["use_images"] == True:
            add_message_to_memory(message)
            await reply_with_generated_image(message)
        else:
            await reply_to_message(message)

    ########################################################################
    # If sleeping add user message to memory without sending a response
    
    elif bot_settings["sleeping"] == True and message.channel.id == channelID and message.content[0] != "!" and message.content != "" and message.content.startswith('<') == False and message.content.startswith('http') == False:
        add_message_to_memory(message)

    ########################################################################
    # ADMIN COMMANDS

    if message.author.id in admin_users:

        # Clean memory
        if message.content.startswith('!!reset'):
            bot_settings["memory"] = []
            await message.channel.send("Emptied memory", reference=message, mention_author=False)
            
        # Randomize generation variables
        if message.content.startswith('!!random'):
            temperature = round(random.uniform(0.6,2),2)
            top_k = random.randint(0, 40)
            #top_p = round(random.uniform(0.5,5.0),2)

            bot_settings["this_settings"]["temperature"] = temperature
            bot_settings["this_settings"]["top_k"] = top_k
            string = f"Temperature: {temperature} TopK: {top_k}"
            print(string)
            await message.channel.send(string, reference=message, mention_author=False)

        if message.content.startswith('!!personality'):
            match = re.search(r'\d+$', message.content)
            if match:
                number = int(match.group())
                await change_personality(number)
                #if change_nickname_with_personality:
                    #server = message.guild
                    #await server.me.edit(nick=settings["char_name"])
            else:
                print("No match")
                await message.channel.send(f'I have {len(jsonFiles)} personalities')

        if message.content.startswith('!!temperature'):
            match = re.search(r"[-+]?(?:\d*\.*\d+)", message.content)
            if match:
                number = float(match.group())
                bot_settings["this_settings"]["temperature"] = number
                await message.channel.send(f'Changed temperature')
            else:
                print("No match")
                await message.channel.send(f'Invalid input')
        if message.content.startswith('!!top_k'):
            match = re.search(r"[-+]?(?:\d*\.*\d+)", message.content)
            if match:
                number = int(match.group())
                bot_settings["this_settings"]["top_k"] = number
                await message.channel.send(f'Changed top_k')
            else:
                print("No match")
                await message.channel.send(f'Invalid input')

        
        # Change active channel
        if message.content.startswith('!!channel'):
            bot_settings["settings"]["channelID"] = message.channel.id
            await message.channel.send(f'Channel has been set.')

        if message.content.startswith('!!reload'):
            load_settings()
            await message.channel.send(f'Loaded settings')
            
        if message.content.startswith('!!help'):
            print("My commands are reset, personality, temperature, top_k, reload and random")
        
########################################################################
      
@client.event
async def on_ready():
    global file_index
    
    print(f'{client.user} has connected to Discord!')
    await change_personality(file_index)

########################################################################

client.run(settings["discord_token"])
