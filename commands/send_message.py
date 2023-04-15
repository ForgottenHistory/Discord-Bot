
async def send_message(text, bot_settings):
    print(bot_settings["settings"]["channelID"])
    channel = bot_settings["client"].get_channel(bot_settings["settings"]["channelID"])
    if text == "":
        text = "Sorry, I could not generate a response"
    await channel.send(text)