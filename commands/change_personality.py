import json, re
from os.path import isfile
from commands.send_message import send_message

async def change_personality(index, bot_settings):
    jsonFiles = bot_settings["jsonFiles"]
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
        await send_message(char_greeting, bot_settings)