import discord, re, random
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json

with open(f"./settings.json", "r") as f:
    settings = json.load(f)

intents = discord.Intents().all()
client = discord.Client(intents=intents)
channelID = settings["channelID"]
memory_length = settings["memory_length"]

# Initialize the tokenizer and model

print("Loading model...")

#tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m")
#model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m")

tokenizer = AutoTokenizer.from_pretrained("facebook/opt-350m")
model = AutoModelForCausalLM.from_pretrained("facebook/opt-350m")

#tokenizer = AutoTokenizer.from_pretrained("facebook/opt-1.3b")
#model = AutoModelForCausalLM.from_pretrained("facebook/opt-1.3b")

#tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
#model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B")

default_responses = [
    "I'm not sure what you mean.",
    "Can you please clarify?",
    "Can you rephrase the question?",
    "Sorry, I didn't understand that."
]

previous_response = None
memory = []
# Define a function to generate the response
def generate_response(prompt):
    global previous_response
    prompt = f"Reply to this message as a chatbot: {prompt}"
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    response = model.generate(input_ids, max_length=60, num_beams=1, do_sample=True, temperature=1, repetition_penalty=1.2, top_k=40, top_p=0.9, bos_token_id=0, eos_token_id=2, pad_token_id=1, attention_mask=None, decoder_start_token_id=None, use_cache=False, num_return_sequences=1)
    response_text = tokenizer.decode(response[0], skip_special_tokens=True)
    response_text = response_text.replace(prompt, "") # remove prompt from response
    if response_text == "":
        response_text = random.choice(default_responses)
    elif response_text == prompt:
        response_text = random.choice(default_responses)

    if response_text == previous_response:
        response_text = random.choice(default_responses)
    previous_response = response_text
    return response_text

@client.event
async def on_message(message):
    global channelID
    global previous_response
    global memory
    if message.author == client.user:
        return
    if message.channel.id == channelID:
        # Clean the message content
        prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
        prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        prompt = prompt.lower() # lowercase the text
        memory.append(prompt)
        if len(memory) > memory_length:
            memory.pop(0) # remove oldest message if memory is full
        # Concatenate the most recent messages in memory to use as the prompt
        prompt = ' '.join(memory[-memory_length:])
        print(prompt)
        # Generate response
        response_text = generate_response(prompt)
        await message.channel.send(response_text)

    # Change author id to the one who runs this bot
    if message.content.startswith('!channel') and message.author.id == 837454923364827206:
        channelID = message.channel.id
        await message.channel.send(f'Channel has been set.')

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(settings["discord_token"])
