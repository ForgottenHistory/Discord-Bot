import discord, re, random
from discord.ext import commands
import requests
import json
from os import listdir
from os.path import isfile, join

# Load words that will NOT be said

word_list = []
with open('banned_words.txt', 'r') as file:
    word_list = file.readlines()

word_list = [x.strip() for x in word_list]
#print(word_list)

# Load character

jsonFilePath = "./json/"
counter = 0
jsonFiles = [f for f in listdir(jsonFilePath) if isfile(join(jsonFilePath, f))]
for f in jsonFiles:
    counter += 1
    print( str(counter) + ". " + str(f))

print("Which file to load?")
file_index = int(input())
file_to_read = jsonFiles[ file_index - 1 ]
with open(f"{jsonFilePath}{file_to_read}", "r") as f:
    data = json.load(f)

# Access the values
char_name = data["char_name"]
char_persona = data["char_persona"]

# extract the example_dialogue if present
example_dialogue = data.get("example_dialogue", None)
world_scenario = data.get("world_scenario", None)

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

sampler_order = [6,0,1,2,3,4,5]
preprompt = f"{char_persona} \nExample dialogue: {example_dialogue}\nScenario: {world_scenario}"
print(preprompt)

this_settings = { 
    "prompt": " ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": 1500,
    "max_length": 80,
    "rep_pen": 1.08,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": 1.0,
    "tfs": 0.9,
    "top_a": 0,
    "top_k": 5,
    "top_p": 0.9,
    "typical": 1,
    "sampler_order": sampler_order
    }

api_server += "/api"
headers = {"Content-Type": "application/json"}

# Initialize the tokenizer and model

print("Starting bot...")

default_responses = [
    "I'm not sure what you mean.",
    "Can you please clarify?",
    "Can you rephrase the question?",
    "Sorry, I didn't understand that."
]

previous_response = None
memory = []

def change_personality(index):
    global jsonFiles
    global jsonFilePath
    global this_settings
    global preprompt
    global char_name
    
    with open(f"{jsonFilePath}{jsonFiles[index - 1]}", "r") as f:
        data = json.load(f)
    # Access the values
    char_name = data["char_name"]
    char_persona = data["char_persona"]

    # extract the example_dialogue if present
    example_dialogue = data.get("example_dialogue", None)
    world_scenario = data.get("world_scenario", None)

    preprompt = f"{char_persona} \nExample dialogue: {example_dialogue}\nScenario: {world_scenario}"
    print(preprompt)
    
# Define a function to generate the response
def generate_response(prompt, user):
    global previous_response
    global memory
    global char_name

    memory.append(f"{user}: {prompt}")
    while len(memory) > memory_length:
        memory.pop(0) # remove oldest message if memory is full
    # Concatenate the most recent messages in memory to use as the prompt
    prompt = preprompt + "\n"
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
        print('Valid response')
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
        if response_lines[x].split(":")[-1] is not '':
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

wait = False
@client.event
async def on_message(message):
    global channelID
    global previous_response
    global memory
    global wait

    # No reply to itself
    if message.author == client.user:
        return

    # Generate a reply to user message
    if message.channel.id == channelID and wait == False and message.content[0] != "!" and message.content != "" and message.content.startswith('<') == False and message.content.startswith('http') == False:
        # Clean the message content
        prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
        prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
        # Generate response
        response_text = generate_response(prompt, message.author.name)
        await message.channel.send(response_text, reference=message, mention_author=False)

    # Clean up memory
    if message.content.startswith('!!!reset') and message.author.id == 837454923364827206:
        memory = []
        await message.channel.send("Emptied memory", reference=message, mention_author=False)

    # Randomize generation variables
    if message.content.startswith('!!!random') and message.author.id == 837454923364827206:
        temperature = round(random.uniform(0.6,1.4),2)
        top_k = random.randint(0, 40)
        #top_p = round(random.uniform(0.5,5.0),2)

        this_settings["temperature"] = temperature
        this_settings["top_k"] = top_k
        string = f"Temperature: {temperature} TopK: {top_k}"
        print(string)
        await message.channel.send(string, reference=message, mention_author=False)

    if message.content.startswith('!!!personality') and message.author.id == 837454923364827206:
        match = re.search(r'\d+$', message.content)
        if match:
            number = int(match.group())
            print(number)
            change_personality(number)
        else:
            print("No match")
    
    # Change active channel
    if message.content.startswith('!!!channel') and message.author.id == 837454923364827206:
        channelID = message.channel.id
        await message.channel.send(f'Channel has been set.')
    
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(bot_token)
