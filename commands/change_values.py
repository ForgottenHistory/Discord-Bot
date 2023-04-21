import re
from commands.change_personality import change_personality

async def change_personality_command(message, bot_settings):
    match = re.search(r'\d+$', message.content)
    if match:
        number = int(match.group())
        await change_personality(number, bot_settings)
    else:
        print("No match")
        await message.channel.send(f'I have {len(bot_settings["jsonFiles"])} personalities')

async def change_top_k(message, bot_settings):
    match = re.search(r'\d+$', message.content)
    if match:
        number = int(match.group())
        bot_settings["this_settings"]["top_k"] = number
        await message.channel.send(f'Changed top_k')
    else:
        print("No match")
        await message.channel.send(f'Invalid input')

async def change_top_p(message, bot_settings):
    match = re.search(r'\d+$', message.content)
    if match:
        number = int(match.group())
        bot_settings["this_settings"]["top_p"] = number
        await message.channel.send(f'Changed top_p')
    else:
        print("No match")
        await message.channel.send(f'Invalid input')

async def change_temperature(message, bot_settings):
    match = re.search(r'\d+$', message.content)
    if match:
        number = int(match.group())
        bot_settings["this_settings"]["temperature"] = number
        await message.channel.send(f'Changed temperature')
    else:
        print("No match")
        await message.channel.send(f'Invalid input')

async def change_channel(message, bot_settings):
    bot_settings["settings"]["channelID"] = message.channel.id
    await message.channel.send(f'Channel has been set.')

async def change_author_note(message, bot_settings):
    command, *note_parts = message.content.split()
    author_note = " ".join(note_parts)
    bot_settings["author_note"] = author_note
    await message.channel.send(f'Author note has been set.')

async def change_jailbreak_prompt(message, bot_settings):
    command, *args = message.content.split()
    jailbreak_prompt = " ".join(args)
    bot_settings["jailbreak_prompt"] = jailbreak_prompt
    await message.channel.send(f'Jailbreak prompt has been set.')

async def change_nsfw_prompt(message, bot_settings):
    command, *args = message.content.split()
    nsfw_prompt = " ".join(args)
    bot_settings["nsfw_prompt"] = nsfw_prompt
    await message.channel.send(f'NSFW prompt has been set.')

async def change_main_prompt(message, bot_settings):
    command, *args = message.content.split()
    main_prompt = " ".join(args)
    bot_settings["main_prompt"] = main_prompt
    await message.channel.send(f'Main prompt has been set.')