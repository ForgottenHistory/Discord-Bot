import aiohttp, json

async def set_soft_prompt(selected, message):
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "value": selected
    }
    json_data = json.dumps(data)

    async with aiohttp.ClientSession() as session:
        async with session.put("http://127.0.0.1:5000/api/v1/config/soft_prompt", data=json_data, headers=headers) as response:
            print(f"Soft prompt set: {response.status}")

    await message.channel.send("Soft prompt set", reference=message, mention_author=False)