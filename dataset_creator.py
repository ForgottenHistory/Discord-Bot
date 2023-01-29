import torch
from transformers import GPT2Tokenizer

# Tokenize the text
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

# Read the text file
import codecs

with codecs.open("./dataset/reformatted_text.txt", "r", encoding='utf-8') as file:
    text = file.read()
    

# Tokenize the text
tokens = tokenizer.tokenize(text)

# Create a dataset from the tokens
dataset = torch.tensor([tokenizer.convert_tokens_to_ids(tokens)])

# Save the dataset to a file
torch.save(dataset, "chatlog_dataset.pt")

# Split the dataset into training and validation sets
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
print(f"Dataset length: {len(dataset)} Train size: {train_size} Val Size = {val_size}")
print("Train dataset")
print(train_dataset)
print("Val dataset")
print(val_dataset)

# Save the datasets to files
torch.save(train_dataset, "chatlog_train_dataset.pt")
torch.save(val_dataset, "chatlog_val_dataset.pt")
