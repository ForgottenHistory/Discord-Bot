from utility import load_settings
async def reload_settings(message, bot_settings):
    load_settings("settings.json")
    await message.channel.send(f'Loaded settings')