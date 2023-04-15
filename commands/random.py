import random
async def random_values(message, bot_settings):
    temperature = round(random.uniform(0.6,2),2)
    top_k = random.randint(0, 40)
    #top_p = round(random.uniform(0.5,5.0),2)

    bot_settings["this_settings"]["temperature"] = temperature
    bot_settings["this_settings"]["top_k"] = top_k
    string = f"Temperature: {temperature} TopK: {top_k}"
    print(string)
    await message.channel.send(string, reference=message, mention_author=False)
