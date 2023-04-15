async def reset_memory(message, bot_settings):
    bot_settings["memory"] = []
    await message.channel.send("Emptied memory", reference=message, mention_author=False)