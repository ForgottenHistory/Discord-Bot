import discord, re, random
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
from discord.ext import commands

#input_ids: The input token IDs to the model, typically obtained by encoding a prompt string using a tokenizer.
#max_new_tokens : Maximum number of tokens to generate in the sequence.
#num_beams: Number of beams for beam search. 1 means no beam search.
#do_sample: If set to True, generates text using sampling, otherwise using beam search
#temperature : The value used to sample the next token. Higher values means the model will take more risks.
#               Try 0.9 for more creative applications, and 0 (argmax sampling) for ones with a well-defined answer.
#repetition_penalty: Penalty for repeating n-grams during decoding.
#top_k : the number of highest probability vocabulary tokens to keep for top-k-filtering. Between 1 and infinity.
#top_p : the cumulative probability of parameter highest probability vocabulary tokens to keep for nucleus sampling. Must be between 0 and 1.
#bos_token_id : ID of the token to start decoding with.
#eos_token_id : ID of the token to stop decoding with.
#pad_token_id : ID of the token that was used for padding, for instance when batching sequences of different lengths.
#attention_mask : Mask to avoid performing attention on padding token indices.
#decoder_start_token_id : If an encoder-decoder model starts generating tokens with a different token than BOS.
#use_cache : if set to True, the model will use the cache, when set to False it will not use the cache.
#num_return_sequences : The number of independently computed generated sequences to generate.

with open(f"./settings.json", "r") as f:
    settings = json.load(f)

intents = discord.Intents().all()
client = discord.Client(intents=intents)
client = commands.Bot(command_prefix='!!!', intents=intents)

channelID = settings["channelID"]
memory_length = settings["memory_length"]
tokens = 50

# Initialize the tokenizer and model

print("Loading model...")

#tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m")
#model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m")

#tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
#model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

tokenizer = AutoTokenizer.from_pretrained("facebook/opt-350m")
model = AutoModelForCausalLM.from_pretrained("facebook/opt-350m")

#tokenizer = AutoTokenizer.from_pretrained("facebook/opt-1.3b")
#model = AutoModelForCausalLM.from_pretrained("facebook/opt-1.3b")

#tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-j-6B")
#model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-j-6B")
#model = torch.load("E:/Torrents/gpt4chan_model/pytorch_model.bin")

default_responses = [
    "I'm not sure what you mean.",
    "Can you please clarify?",
    "Can you rephrase the question?",
    "Sorry, I didn't understand that."
]

previous_response = None
memory = []
# Define a function to generate the response
def generate_response(prompt, user):
    global previous_response
    global memory
    
    #prompt = "Human: " + prompt + "\nBot: "
    memory.append(f"{user}: {prompt}")
    while len(memory) > memory_length:
        memory.pop(0) # remove oldest message if memory is full
    # Concatenate the most recent messages in memory to use as the prompt
    prompt = "\n".join(f"{mem}" for mem in memory) + "\nBot:"
    print(f"\n {len(memory)} \n" + prompt)
    
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    response = model.generate(input_ids, max_new_tokens=25, num_beams=1, do_sample=True, temperature=0.9, repetition_penalty=1.2, top_k=40, top_p=0.9, use_cache=False, num_return_sequences=1)
    
    response_text = tokenizer.decode(response[0], skip_special_tokens=True)
   
    # Extract the bot's response from the generated text
    response_text = response_text.split("Bot:")[-1]
    
    # Cut off any "Human:" or "human:" parts from the response
    response_text = response_text.split("Human:")[0]
    response_text = response_text.split("human:")[0]
    memory.append(f"Bot: {response_text}")
    
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
    if message.channel.id == channelID and message.content[0] != "!":
        # Clean the message content
        prompt = re.sub(r'@[A-Za-z0-9]+', '', message.content) # remove mentions
        prompt = re.sub(r'[^\w\s?]', '', prompt) # remove special characters
        prompt = prompt.lower() # lowercase the text
        
        # Generate response
        response_text = generate_response(prompt, message.author.name)
        await message.channel.send(response_text, reference=message, mention_author=False)
    
    if message.content.startswith('!!!reset'):
        memory = []
        await message.channel.send("Emptied memory", reference=message, mention_author=False)

    # Change author id to the one who runs this bot
    if message.content.startswith('!!!channel') and message.author.id == 837454923364827206:
        channelID = message.channel.id
        await message.channel.send(f'Channel has been set.')
    
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(settings["discord_token"])
