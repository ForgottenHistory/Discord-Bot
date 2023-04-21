import discord, re, random, os, json, asyncio, aiohttp, sys
from discord.ext import commands
from os import listdir
from os.path import isfile, join
from commands.__commands__ import *
from commands.change_personality import change_personality

sys.path.append('E:/Coding/Discord-Bot')
from reply import reply_with_generated_image, reply_with_gif, should_reply
from utility import load_list_from_file, create_directory_if_not_exists, load_settings, fix_relations, find_float_or_int
from config import admin_users_file, json_dir, settings_file, banned_words_file
from secret import openai_api_key

########################################################################
# DISCORD BOT USING OPENAI GPT-3
########################################################################

# Load words that will NOT be said
word_list = load_list_from_file(banned_words_file)

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
with open(f"./settings_openai.json", "r") as f:
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
    "main_prompt": "",
    "author_note": "",
    "jailbreak_prompt": "",
    "nsfw_prompt": ""
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

bot_settings["main_prompt"] = settings["main_prompt"]
bot_settings["author_note"] = settings["author_note"]
bot_settings["nsfw_prompt"] = settings["nsfw_prompt"]
bot_settings["jailbreak_prompt"] = settings["jailbreak_prompt"]

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
# Generate the response

async def update_memory(prompt, user, bot_settings):
    if len(bot_settings["memory"]) == 0 or bot_settings["memory"][-1] != f"{user}: {prompt}":
        bot_settings["memory"].append(f"{user}: {prompt}")
    while len(bot_settings["memory"]) > bot_settings["settings"]["memory_length"]:
        bot_settings["memory"].pop(0)  # remove oldest message if memory is full

    return "\n".join(f"{mem}" for mem in bot_settings["memory"])

async def fetch_openai_response(data, headers):
    url = "https://api.openai.com/v1/chat/completions"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                response_json = await response.json()
                return response_json
    except Exception as e:
        print(f"Error while making a post request: {e}")
        return None

async def process_response(response, prompt, user, bot_settings):
    try:
        response_text = response['results'][0]['text']
        response_lines = response_text.split("\n")
    except KeyError:
        print("Error: Unexpected response format.")
        return None

    if response_lines[0] == "":
        return None

    if response_lines[0].split(":")[0].lower() == user.lower():
        response_text = await generate_response(prompt, user, bot_settings)
    elif response_lines[0].split(":")[-1] == '':
        response_text = await generate_response(prompt, user, bot_settings)
    elif response_lines[0].split(":")[-1] != '':
        response_text = response_lines[0].split(":")[-1]

    return response_text

def split_character_description(character_description):
    split_description = character_description.split("<START>")
    messages = []
    for desc in split_description:
        desc = desc.strip()
        if not desc:
            continue

        if desc == "<START>":
            messages.append({"role": "system", "content": "[Start a new chat]"})
        else:
            messages.append({"role": "assistant", "content": desc})

    return messages

def split_dialogue(message):
    content = message['content']
    char_name = re.escape(bot_settings["char_name"])

    # Split the content by "You:" and the character name followed by a colon
    dialogue_parts = re.split(f"You:|{char_name}:", content)

    messages = []
    current_role = None

    for part in dialogue_parts:
        if not part.strip():
            continue

        if "You:" in part:
            current_role = "user"
            content = part.replace("You:", "").strip()
        else:
            current_role = "assistant"
            content = f"{char_name}:{part.strip()}"

        messages.append({"role": current_role, "content": content})

    return messages

async def structure_prompt(prompt, user, bot_settings):
    # Structure up the prompt
    char_name = bot_settings["char_name"]

    messages = []

    # Main prompt
    if bot_settings["main_prompt"] != "":
        main_prompt = bot_settings["main_prompt"].replace("*char*", char_name)
        main_prompt = main_prompt.replace("*user*", user)
        messages.append({"role": "system", "content": main_prompt})

    # NSFW prompt
    if bot_settings["nsfw_prompt"] != "":
        nsfw_prompt = bot_settings["nsfw_prompt"].replace("*char*", char_name)
        nsfw_prompt = nsfw_prompt.replace("*user*", user)
        messages.append({"role": "system", "content": nsfw_prompt})
    
    character_description = fix_relations(bot_settings["preprompt"], bot_settings["people_memory"])
    messages.append({"role": "system", "content": character_description})

    # Author note
    if bot_settings["author_note"] != "":
        messages.append({"role": "system", "content": bot_settings["author_note"]})

    # Memory
    memory_text = await update_memory(prompt, user, bot_settings)
    for mem in memory_text.split("\n"):
        if mem.strip():  # Added check to exclude empty strings
            messages.append({"role": "user", "content": mem})

    # Jailbreak prompt
    if bot_settings["jailbreak_prompt"] != "":
        jailbreak_prompt = bot_settings["jailbreak_prompt"].replace("*char*", char_name)
        jailbreak_prompt = jailbreak_prompt.replace("*user*", user)
        messages.append({"role": "system", "content": jailbreak_prompt})

    return messages

first = True
async def generate_response(prompt, user, bot_settings):
    global word_list, first

    messages = await structure_prompt(prompt, user, bot_settings)
    messages.append({"role": "user", "content": f"{user}: {prompt}"})

    # Generate the response using OpenAI API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}",  # Add your OpenAI API key to the bot_settings dictionary
    }
    data = {
        "messages": messages,
        "model": "gpt-3.5-turbo-0301",
        "temperature": bot_settings["settings"]["temperature"],
        "max_tokens": 50,
        "frequency_penalty": 1,
        "presence_penalty": 0.9,
        "stream": False,
        "stop": ["\n"]
    }

    data["messages"].remove(data["messages"][-3])
        #data["messages"].remove(data["messages"][-4])

    print("data: " + str(messages))
    response = await fetch_openai_response(data, headers)
    print(response)
    response_text = extract_response(response)

    # Process the response
    #response_text = await process_response(response, prompt, user, bot_settings)

    print("response: " + response_text)
    for word in word_list:
        response_text = response_text.replace(word, "%%%%")

    response_text = re.sub(r'"', '', response_text)
    response_text = response_text.replace(bot_settings["char_name"] + ": ", "")
    bot_settings["previous_response"] = response_text
    await update_memory(response_text, bot_settings["char_name"], bot_settings)

    return response_text

def extract_response(api_output):
    response_message = api_output['choices'][0]['message']['content']
    return response_message

########################################################################

async def reply_to_message(message, bot_settings):
    
    bot_settings["sleeping"] = True
    # Clean the message content
    prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
    #prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
    # Generate rating on user
    response_text = await generate_response(prompt, message.author.name, bot_settings)

    bot_settings["sleeping"] = False
    await message.channel.send(response_text, reference=message, mention_author=False)

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
    bot_settings["memory"][-1] = "[Start a new chat]"

########################################################################

bot_settings["client"].run(settings["discord_token"])