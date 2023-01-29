import json

# Load the json file
print("Json to load?")
fileToLoad = input()
with open(f"./json/{fileToLoad}.json", "r") as f:
    data = json.load(f)

# Access the values
char_name = data["char_name"]
char_persona = data["char_persona"]
print(char_name)
print(char_persona)
