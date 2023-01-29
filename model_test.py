import torch

# Load the pre-trained model
print("Loading model...")
model = torch.load("pytorch_model.bin")
model.eval()

# Define your prompt and generate text
prompt = "What is the meaning of life?"
generated_text = model.generate(prompt)
print(generated_text)

x = input()
