import json
import requests
import io
import base64
import os
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"

payload = {
    "prompt": "maltese puppy",
    "steps": 20,
    "width": 768,
    "height": 768
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

    image.save(f"{save_path}output{num_files}.png", pnginfo=pnginfo)

#response = requests.get(url=f'{url}/sdapi/v1/hypernetworks', json=payload)

#r = response.json()
#print(r)
