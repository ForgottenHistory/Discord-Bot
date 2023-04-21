import re, json, asyncio, aiohttp, requests
import discord

from config import banned_words_file
from utility import find_float_or_int, fix_relations, load_list_from_file, check_response_text, extract_keywords_POS, generate_image

# Load words that will NOT be said
word_list = load_list_from_file(banned_words_file)

async def post_request(url, json_data, headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json_data, headers=headers) as response:
            data = await response.json()
            return data

def should_reply(message, bot_settings):
    return (
        message.channel.id == bot_settings["settings"]["channelID"]
        and bot_settings["sleeping"] == False
        and message.content
        and not message.content.startswith(("!", "<", "http"))
    )

async def reply_to_message(message, bot_settings):
    
    bot_settings["sleeping"] = True
    # Clean the message content
    prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
    #prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        
    # Generate rating on user
    response_text = await generate_response(prompt, message.author.name, bot_settings)
    bot_settings["message_counter"] += 1
    if bot_settings["message_counter"] >= 20:
        bot_settings["message_counter"] = 0
        rating_response = await generate_response(f"What would you rate the user {message.author.name} on a scale of 0 to 10", "SYSTEM", bot_settings)
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

    bot_settings["sleeping"] = False
    await message.channel.send(response_text, reference=message, mention_author=False)

########################################################################     
# Generate the response

async def update_memory(prompt, user, bot_settings):
    if len(bot_settings["memory"]) == 0 or bot_settings["memory"][-1] != f"{user}: {prompt}":
        bot_settings["memory"].append(f"{user}: {prompt}")
    while len(bot_settings["memory"]) > bot_settings["settings"]["memory_length"]:
        bot_settings["memory"].pop(0)  # remove oldest message if memory is full

    return "\n".join(f"{mem}" for mem in bot_settings["memory"])

async def fetch_response(url, prompt, headers):
    try:
        response = await post_request(url, prompt, headers)
    except Exception as e:
        print(f"Error while making a post request: {e}")
        return None

    return response

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

async def structure_prompt(prompt, user, bot_settings):
    # Structure up the prompt
    char_name = bot_settings["char_name"]

    memory_text = await update_memory(prompt, user, bot_settings)
    character_description = fix_relations(bot_settings["preprompt"], bot_settings["people_memory"])
    
    new_prompt = ""
    
    # Main prompt
    if bot_settings["main_prompt"] != "":
        main_prompt = bot_settings["main_prompt"].replace("*char*", char_name)
        main_prompt = main_prompt.replace("*user*", user)
        new_prompt = new_prompt +main_prompt + " "

    # NSFW prompt
    if bot_settings["nsfw_prompt"] != "":
        nsfw_prompt = bot_settings["nsfw_prompt"].replace("*char*", char_name)
        nsfw_prompt = nsfw_prompt.replace("*user*", user)
        new_prompt = new_prompt + nsfw_prompt + " "

    # Character description
    new_prompt = new_prompt + character_description

    # Author note
    if bot_settings["author_note"] != "":
        new_prompt = new_prompt + "\n" + bot_settings["author_note"]
    
    # Memory
    new_prompt = new_prompt + "\n" + memory_text

    # Jailbreak prompt
    if bot_settings["jailbreak_prompt"] != "":
        jailbreak_prompt = bot_settings["jailbreak_prompt"].replace("*char*", char_name)
        jailbreak_prompt = jailbreak_prompt.replace("*user*", user)
        new_prompt = new_prompt + "\n" + jailbreak_prompt + " "

    new_prompt = new_prompt + f"\n{char_name}: "
    #print(new_prompt)

    return prompt

async def generate_response(prompt, user, bot_settings):
    global word_list

    bot_settings["this_settings"]["prompt"] = await structure_prompt(prompt, user, bot_settings)

    # Generate the response
    headers = {"Content-Type": "application/json"}
    url = bot_settings["settings"]["api_server"] + "/api/v1/generate"

    response = await fetch_response(url, bot_settings["this_settings"], headers)
    if not response:
        return "I'm sorry, I couldn't generate a response."

    # Process the response
    response_text = await process_response(response, prompt, user, bot_settings)
    print(response_text)
    if not response_text:
        return "I'm sorry, I couldn't generate a response."

    for word in word_list:
        response_text = response_text.replace(word, "%%%%")

    response_text = re.sub(r'"', '', response_text)
    bot_settings["previous_response"] = response_text
    await update_memory(response_text, bot_settings["char_name"], bot_settings)

    return response_text

########################################################################     

async def reply_with_generated_image(message, bot_settings):

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

async def reply_with_gif(message, bot_settings):
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

    api_key = bot_settings["settings"]["tenor_api_key"]
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