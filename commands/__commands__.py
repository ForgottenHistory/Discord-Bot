import re
from commands.reset import reset_memory
from commands.random import random_values
from commands.reload_settings import reload_settings
from commands.change_values import change_personality_command, change_temperature, change_top_k, change_top_p, change_channel
from commands.softprompt import set_soft_prompt
from config import soft_prompt_file

async def process_input(message, bot_settings):
    if message.content.startswith("!!") == False:
        return

    if message.content.startswith('!!personality'):
        await change_personality_command(message, bot_settings)
    
    elif message.content.startswith('!!reset'):
        await reset_memory(message, bot_settings)

    elif message.content.startswith('!!random'):
        await random_values(message, bot_settings)

    elif message.content.startswith('!!temperature'):
        await change_temperature(message, bot_settings)

    elif message.content.startswith('!!top_k'):
        await change_top_k(message, bot_settings)
    
    elif message.content.startswith('!!top_p'):
        await change_top_p(message, bot_settings)

    elif message.content.startswith('!!channel'):
        await change_channel(message, bot_settings)

    elif message.content.startswith('!!reload'):
        await reload_settings(message, bot_settings)
        
    elif message.content.startswith('!!help'):
        print("My commands are reset, personality, temperature, top_k, reload and random")

    elif message.content.startswith('!!softprompt'):
        await set_soft_prompt(soft_prompt_file, message)