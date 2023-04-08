import os
import json

#Part-of-Speech (POS)
import nltk

#Named Entity Recognition (NER)
from nltk import word_tokenize, pos_tag, ne_chunk

#stable diffusion local
from PIL import Image, PngImagePlugin
import io
import base64

def create_directory_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def load_list_from_file(file_path):
    with open(file_path, 'r') as file:
        data = file.readlines()
    return [x.strip() for x in data]
    
def load_settings(settings_file):
    with open(f"./settings.json", "r") as f:
        settings = json.load(f)
    
    sampler_order = [6,0,1,2,3,4,5]
    this_settings = { 
    "prompt": " ",
    "use_story": False,
    "use_memory": False,
    "use_authors_note": False,
    "use_world_info": False,
    "max_context_length": settings["max_context_length"],
    "max_length": settings["max_length"],
    "rep_pen": 1.08,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.9,
    "temperature": settings["temperature"],
    "tfs": 0.9,
    "top_a": 0,
    "top_k": settings["top_k"],
    "top_p": settings["top_p"],
    "typical": 1,
    "sampler_order": sampler_order
}
    print("Loaded settings")
    return this_settings
    
def extract_keywords_POS(text):
    tokens = nltk.word_tokenize(text)
    pos_tagged_tokens = nltk.pos_tag(tokens)
    keywords = [word for word, pos in pos_tagged_tokens if pos in ['NN', 'JJ']]
    return keywords
  
def generate_image(prompt, steps=20, width=768, height=768):
    url = "http://127.0.0.1:7860"

    payload = {
        "prompt": prompt,
        "steps": steps,
        "width": width,
        "height": height
    }

    response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)

    r = response.json()

    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))

        save_path = "./generated_images/"
        files = os.listdir(save_path)
        num_files = len(files)

        image.save(f"{save_path}output{num_files+1}.png", pnginfo=pnginfo)
        return f"{save_path}output{num_files+1}.png"