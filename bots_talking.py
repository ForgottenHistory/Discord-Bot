import discord, re, random
from discord.ext import commands
import requests
import json
import os
from os import listdir
from os.path import isfile, join
import asyncio
import sys
sys.path.append('E:/Coding/Discord-Bot')
import func.fix_relations
import func.find_float_or_int
import func.check_response_text

########################################################################
# DISCORD BOT TALKING TO ITSELF WITH PYGMALION
# use their google collab for api server (or run locally)
########################################################################
########################################################################

# Make paths if they do not exist
if not os.path.exists("./json"):
    os.makedirs("./json")

# Load words that will NOT be said

class Character:
    def __init__(self):
        self.char_name = "Temp"
        print("Created new character")
        
    def add_values(self, name, personality, example_dialogue, char_greeting):
        self.char_name = name
        self.char_persona = personality
        self.example_dialogue = example_dialogue
        self.char_greeting = char_greeting
        
    def greet(self):
        print(f"Hi, I'm {self.name} and I am {self.personality}.")

with open('banned_words.txt', 'r') as file:
    word_list = file.readlines()

word_list = [x.strip() for x in word_list]

# Load character

counter = 0
jsonFiles = [f for f in listdir("./json/") if isfile(join("./json/", f))]
for f in jsonFiles:
    counter += 1
    print( str(counter) + ". " + str(f))

#print("Which file to load?")
#file_index = int(input())

# Values that need to global
characters = []
preprompt = ""
use_greeting = False

#Discord client setup

with open(f"./settings.json", "r") as f:
    settings = json.load(f)

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!!', intents=intents)

memory = []

sampler_order = [6,0,1,2,3,4,5]
this_settings = {}

print("Starting bots...")

previous_response = None

########################################################################

def load_settings():
    global settings
    with open(f"./settings_chat.json", "r") as f:
        settings = json.load(f)

    this_settings = { 
    "prompt": " ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": settings["max_context_length"],
    "max_length": settings["max_length"],
    "rep_pen": 1.12,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": settings["temperature"],
    "tfs": 0.9,
    "top_a": 0,
    "top_k": settings["top_k"],
    "top_p": settings["top_p"],
    "typical": 1,
    "sampler_order": sampler_order
}
    settings["this_settings"] = this_settings
    
########################################################################
    
load_settings()

########################################################################

async def send_message(text):
    global settings, client
    channel = client.get_channel(settings["channelID"])
    await channel.send(text)

########################################################################
# Change personality

async def change_personality(index, character):
    global jsonFiles
    global jsonFilePath
    global preprompt
    global memory
    global settings
    global characters

    if index > len(jsonFiles) or index < 0:
        return
    
    with open(f"./json/{jsonFiles[index - 1]}", "r") as f:
        data = json.load(f)
    # Access the values
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
    #world_scenario = data.get("world_scenario", None)
    
    #preprompt = f"{char_persona}"
    #if example_dialogue is not None:
        #preprompt +=  f"\nExample dialogue: {example_dialogue}" 
    #if world_scenario is not None and world_scenario != "":
        #preprompt += f"\n{char_name}: {world_scenario}"

    for char in characters:
        if char.char_name == char_name:
            char_name += "1"
    character.add_values(char_name, char_persona, example_dialogue, char_greeting)
    print("Loaded " + character.char_name)

########################################################################
    
def check_response_error(response):
    code = response.status_code
    # Response code check
    if code == 200:
        print(' ')
        #print('Valid response')
    elif code == 422:
        print('Validation error')
    elif code in [501, 503, 507]:
        print(response.json())
    else:
        print("something went wrong on the request")
    
########################################################################     
# Generate the response

def get_character(last_talker):
    global characters
    
    not_continous = True
    #print(last_talker)
    if not_continous:
        available_characters = [char for char in characters if char.char_name.lower() != last_talker.lower()]
        
    character = available_characters[random.randint(0, len(available_characters)-1)]
    return character

def generate_response(prompt, user):
    global previous_response
    global memory
    global settings
    global word_list
    
    character = get_character(user)
    
    if len(memory) == 0 or memory[-1] != f"{prompt}":
        memory.append(f"{prompt}")
    while len(memory) > settings["memory_length"]:
        memory.pop(0) # remove oldest message if memory is full

    ###################################################################

    preprompt = f"{character.char_persona}"
    if character.example_dialogue is not None:
        preprompt +=  f"\nExample dialogue: {character.example_dialogue}"
    if preprompt.endswith("<START>"):
        preprompt = preprompt.rstrip("<START>")
    
    new_prompt = "\n" + preprompt + "\n" + "\n".join(f"{mem}" for mem in memory) + f"\n{character.char_name}: "
    #print(f"\n {new_prompt}")
    
    this_settings["prompt"] = new_prompt
    args = {
            "data": this_settings,
            "headers": {"Content-Type": "application/json"}
        }

    headers = {"Content-Type": "application/json"}
    response = requests.post(settings["api_server"]+"/api/v1/generate", json=this_settings, headers=headers)

    # Response code check
    check_response_error(response)
    
    ###################################################################
    
    # Clean up response
    response_text = response.json()['results'][0]['text']
    response_lines = response_text.split("\n")
    #print("Character name: " + character.char_name)
    #print(f"Response lines: \n" + str(response_lines))

    for x in range(0, len(response_lines)):
        if response_lines[x].split(":")[-1] != '': #and response_lines[x].split(":")[0] == char_name:
            response_text = response_lines[x].split(":")[-1]
            break
        else:
            memory.pop(-1)
            response_text = generate_response(prompt, user)
        
    #if response_lines[0].split(":")[0].lower() == user.lower():
    #    response_text = generate_response(prompt, user)
    #elif response_lines[0].split(":")[-1] == '':
      #  response_text = generate_response(prompt, user)
    #elif response_lines[0].split(":")[-1] != '': #and response_lines[x].split(":")[0] == char_name:
     #   response_text = response_lines[0].split(":")[-1]
    
    ###################################################################
    # Replace bad words
    
    for word in word_list:
        response_text = response_text.replace(word, "%%%%")

    ###################################################################
    # Check if response text is not correct
    # Sends a default response if no
    func.check_response_text.check_response_text(prompt, response_text, previous_response, character.char_name, memory)

    response_text = re.sub(r'"', '', response_text)
    previous_response = response_text
    return f"{character.char_name}: {response_text}"

########################################################################
# REPLY TO MESSAGES
########################################################################
# TEXT

async def reply_to_message(message, user):
    global sleeping
    global message_counter
    global settings
    
    # Clean the message content
    prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
    #prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
    # Generate rating on user
    response_text = generate_response(prompt, user)
    await message.channel.send(response_text)
    
########################################################################

@client.event
async def on_message(message):
    global admin_users
    global settings

    channelID = settings["channelID"]

    # Generate a reply to user message
    if message.channel.id == channelID and message.author.id == client.user.id:
        await reply_to_message(message, message.content.split(":")[0])

    ########################################################################
      
@client.event
async def on_ready():
    global characters
    global settings

    for char_index in settings["characters"]:
        characters.append(Character())
        await change_personality(char_index, characters[-1])
    
    print(f'{client.user} has connected to Discord!')
    channel = client.get_channel(settings["channelID"])
    if characters[0].char_greeting != None:
        await channel.send( characters[0].char_name + ": " + characters[0].char_greeting)

########################################################################

client.run(settings["discord_token"])
