import discord, re, random
from discord.ext import commands
import requests
import json
from os import listdir
from os.path import isfile, join
import asyncio

# Load words that will NOT be said

word_list = []
with open('banned_words.txt', 'r') as file:
    word_list = file.readlines()

admin_users = []
with open('admin_users.txt', 'r') as file:
    admin_users = file.readlines()
    
admin_users = [int(x.strip()) for x in admin_users]
word_list = [x.strip() for x in word_list]
#print(word_list)

# Load character

counter = 0
jsonFiles = [f for f in listdir("./json/") if isfile(join("./json/", f))]
for f in jsonFiles:
    counter += 1
    print( str(counter) + ". " + str(f))

print("Which file to load?")
file_index = int(input())

# Values that need to global
char_name = ""
preprompt = ""
use_greeting = False

#Discord client setup

with open(f"./settings.json", "r") as f:
    settings = json.load(f)

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!!', intents=intents)

api_server = settings["api_server"]
bot_token = settings["discord_token"]
channelID = settings["channelID"]
memory_length = settings["memory_length"]
use_greeting = settings["use_greeting"]
change_nickname_with_personality = settings["change_nickname_with_personality"]

memory = []
people_memory = { "meanie":7.0 }

sampler_order = [6,0,1,2,3,4,5]
this_settings = { 
    "prompt": " ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": settings["max_context_length"],
    "max_length": settings["max_length"],
    "rep_pen": 1.08,
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

# Misc values

api_server += "/api"
headers = {"Content-Type": "application/json"}

print("Starting bot...")

default_responses = [
    "I'm not sure what you mean.",
    "Can you please clarify?",
    "Can you rephrase the question?",
    "Sorry, I didn't understand that."
]

previous_response = None

####################################

async def send_message(text):
    global channelID, client
    channel = client.get_channel(channelID)
    await channel.send(text)

# Change personality

async def change_personality(index):
    global jsonFiles
    global jsonFilePath
    global this_settings
    global preprompt
    global char_name
    global people_memory
    global use_greeting
    global memory

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
    world_scenario = data.get("world_scenario", None)
    
    preprompt = f"{char_persona} \nExample dialogue: {example_dialogue}\nScenario: {world_scenario}"
    if isfile(f"./relations/{char_name}.json"):
        with open(f"./relations/{char_name}.json", "r") as f:
            people_memory = json.load(f)
            print("Loaded relations.")
    else:
        print("No relations saved")
        with open(f"./relations/{char_name}.json", "w") as outfile:
             json.dump(people_memory, outfile)
    
    print(preprompt)
    memory = []
    if use_greeting and char_greeting != None:
        memory.append(char_greeting)
        await send_message(char_greeting)

##############################

# For finding a rating about a user the bot returns
def find_float_or_int(string):
    match = re.search("[-+]?\d*\.\d+|\d+", string)
    if match:
        return float(match.group())
    else:
        return None

# Define a function to generate the response
def generate_response(prompt, user):
    global previous_response
    global memory, people_memory
    global char_name

    memory.append(f"{user}: {prompt}")
    while len(memory) > memory_length:
        memory.pop(0) # remove oldest message if memory is full

    # Add relationships
    prepromt_fixed = preprompt
    relations = "Relations("
    for person in people_memory:
        value = people_memory[person]
        if value >= 5.5 and value < 9.5:
            relations += f"\"You like {person}\"+"
        elif value >= 9.5:
            relations += f"\"You love {person}\"+"
        elif value > 2.0 and value <= 4.5:
            relations += f"\"You dislike {person}\"+"
        elif value <= 2.0:
            relations += f"\"You hate {person}\"+"

    relations = relations[:-1] + ")"
    
    # Find the index of the closing curly bracket
    index = prepromt_fixed.find("}")

    # Insert the relations before the closing bracket
    prepromt_fixed = prepromt_fixed[:index] + f"{relations}" + prepromt_fixed[index:]
    
    # Concatenate the most recent messages in memory to use as the prompt
    prompt = prepromt_fixed + "\n"
    prompt += "\n".join(f"{mem}" for mem in memory) + f"\n{char_name}: "
    #print(f"\n" + prompt)
    
    this_settings["prompt"] = prompt
    args = {
            "data": this_settings,
            "headers": {"Content-Type": "application/json"}
        }

    response = requests.post(api_server+"/v1/generate", json=this_settings, headers=headers)

    # Response code check
    if response.status_code == 200:
        print(' ')
        #print('Valid response')
    elif response.status_code == 422:
        print('Validation error')
    elif response.status_code in [501, 503, 507]:
        print(response.json())
    else:
        print("something went wrong on the request")

    # Clean up response
    response_text = response.json()['results'][0]['text']
    response_lines = response_text.split("\n")
    print(response_lines)
    for x in range(0, len(response_lines)):
        if response_lines[x].split(":")[-1] != '':
            response_text = response_lines[x].split(":")[-1]
            break

    # Replace bad words
    for word in word_list:
        response_text = response_text.replace(word, "%%%%")

    # Check if response text is not correct
    # Sends a default response if no
    if response_text == "":
        response_text = random.choice(default_responses)
    elif response_text == prompt:
        response_text = random.choice(default_responses)
    elif response_text == previous_response:
        response_text = random.choice(default_responses)
    else:
        memory.append(f"{char_name}: " + response_text)

    response_text = re.sub(r'"', '', response_text)
    previous_response = response_text
    return response_text

message_counter = 0
sleeping = False
@client.event
async def on_message(message):
    global channelID
    global memory, people_memory
    global message_counter
    global char_name
    global sleeping
    global change_nickname_with_personality
    global admin_users
    
    # No reply to itself
    if message.author == client.user:
        return

    # Generate a reply to user message
    if message.channel.id == channelID and sleeping == False and message.content[0] != "!" and message.content != "" and message.content.startswith('<') == False and message.content.startswith('http') == False:
        # Clean the message content
        prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
        prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
        # Generate rating on user
        response_text = generate_response(prompt, message.author.name)
        message_counter += 1
        if message_counter >= 20:
            message_counter = 0
            rating_response = generate_response(f"What would you rate the user {message.author.name} on a scale of 0 to 10", "SYSTEM")
            print(rating_response)
            # Remove SYSTEM and response from existance
            memory.pop(-1)
            memory.pop(-1)
            rating_value = find_float_or_int(rating_response)

            if rating_value != None:
                people_memory[message.author.name] = rating_value
                with open(f"./relations/{char_name}.json", "w") as outfile:
                    json.dump(people_memory, outfile)

        # Send response message
        sleeping = True
        await asyncio.sleep(1)
        sleeping = False
        await message.channel.send(response_text, reference=message, mention_author=False)

    elif sleeping == True and message.channel.id == channelID and message.content[0] != "!" and message.content != "" and message.content.startswith('<') == False and message.content.startswith('http') == False:
        # Clean the message content
        prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
        prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
        memory.append(f"{message.author.name}: {prompt}")
        while len(memory) > memory_length:
            memory.pop(0) # remove oldest message if memory is full
        
    # Clean up memory
    if message.content.startswith('!!!reset') and message.author.id in admin_users:
        memory = []
        await message.channel.send("Emptied memory", reference=message, mention_author=False)
        
    # Randomize generation variables
    if message.content.startswith('!!!random') and message.author.id in admin_users:
        temperature = round(random.uniform(0.6,2),2)
        top_k = random.randint(0, 40)
        #top_p = round(random.uniform(0.5,5.0),2)

        this_settings["temperature"] = temperature
        this_settings["top_k"] = top_k
        string = f"Temperature: {temperature} TopK: {top_k}"
        print(string)
        await message.channel.send(string, reference=message, mention_author=False)

    if message.content.startswith('!!!personality') and message.author.id in admin_users:
        match = re.search(r'\d+$', message.content)
        if match:
            number = int(match.group())
            await change_personality(number)
            if change_nickname_with_personality:
                server = message.guild
                await server.me.edit(nick=char_name)
        else:
            print("No match")
            await message.channel.send(f'I have {len(jsonFiles)} personalities')
    
    # Change active channel
    if message.content.startswith('!!!channel') and message.author.id in admin_users:
        channelID = message.channel.id
        await message.channel.send(f'Channel has been set.')

    if message.content.startswith('!!!help') and message.author.id in admin_users:
        print("My commands are reset, personality and random")
        
@client.event
async def on_ready():
    global file_index
    
    print(f'{client.user} has connected to Discord!')
    await change_personality(file_index)

client.run(bot_token)
