import json, re
from os.path import isfile
from commands.send_message import send_message

#####################################################################################################

class Character:
    def __init__(self, char_name, char_persona, char_greeting, example_dialogue, world_scenario):
        self.char_name = char_name
        self.char_persona = char_persona
        self.char_greeting = char_greeting
        self.example_dialogue = example_dialogue
        self.world_scenario = world_scenario

#####################################################################################################
# 1. Load the json file

def load_json_data(index, bot_settings):
    jsonFiles = bot_settings["jsonFiles"]
    if index > len(jsonFiles) or index < 0:
        return
    
    with open(f"./json/{jsonFiles[index - 1]}", "r") as f:
        data = json.load(f)
    return data

#####################################################################################################
# 2. Extract the values

def extract_character(data):
    character = Character()

    # Access the values
    character.char_name = data["char_name"]
    character.char_persona = data["char_persona"]
    character.char_greeting = data.get("char_greeting", None)
    if character.char_greeting == None:
        character.char_greeting = data.get("first_mes", None)
    
    # Check for W++
    match = re.search("[\{\}]", character.char_persona)
    if match is None:
        character.char_persona += "[character(\"{}\")\n{{\n}}\n]".format(character.char_name)
    
    # extract the example_dialogue if present
    character.example_dialogue = data.get("example_dialogue", None)
    character.world_scenario = data.get("world_scenario", None)

    return character

#####################################################################################################
# 3. Set the preprompt & memory

def set_preprompt(character, bot_settings):
    bot_settings["preprompt"] = f"{character.char_persona}"
    if character.example_dialogue is not None:
        bot_settings["preprompt"] +=  f"\nExample dialogue: {character.example_dialogue}" 
    #if world_scenario is not None and world_scenario != "":
        #preprompt += f"\n{char_name}: {world_scenario}"
    
    bot_settings["memory"] = []
    if bot_settings["preprompt"].endswith("<START>") == False:
        bot_settings["memory"].append("<START>")
    if character.char_greeting is not None:
        bot_settings["memory"].append(character.char_greeting)

#####################################################################################################
# 4. Load the relations

def load_relations(character, bot_settings):
    if isfile(f"./relations/{character.char_name}.json"):
        with open(f"./relations/{character.char_name}.json", "r") as f:
            bot_settings["people_memory"] = json.load(f)
            print("Loaded relations.")
    else:
        print("No relations saved")
        with open(f"./relations/{character.char_name}.json", "w") as outfile:
            json.dump(bot_settings["people_memory"], outfile)

#####################################################################################################
# 5. Send the greeting if present

def send_greeting(character, bot_settings):
    if bot_settings["use_greeting"] and character.char_greeting != None:
        send_message(character.char_greeting, bot_settings)

#####################################################################################################

async def change_personality(index, bot_settings):
    character_data = load_json_data(index, bot_settings)

    # Access the values
    character = extract_character(character_data)
    
    set_preprompt(character, bot_settings)
    load_relations(character, bot_settings)
    send_greeting(character, bot_settings)

#####################################################################################################
