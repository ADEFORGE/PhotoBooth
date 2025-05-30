import json
import os
import glob
import time
import requests
import datetime
import random
from constante import dico_styles

class ImageGeneratorAPIWrapper:
    def __init__(self, server_url="http://127.0.0.1:8188"):
        self.server_url = server_url
        self._style = "oil paint"
        self._output_folder = os.path.abspath("../ComfyUI/output")

        self._styles_prompts = dico_styles

        self._negative_prompt = "watermark, text"
        self._base_prompt = self._load_base_prompt()

########### Prompts and styles ###########
    def _load_base_prompt(self):
        with open("workflows/image2image.json") as f:
            return json.load(f)

    def set_styles_prompts(self, styles_prompts : dict):
        self._styles_prompts = styles_prompts
        
    def set_style(self, style: str):
        if style in self._styles_prompts:
            self._style = style
        else:
            raise ValueError(f"Style '{style}' not recognized.")

    
########### Image ###########

    def delete_images(self):
        png_files = glob.glob(os.path.join(self._output_folder, "*.png"))
        for file_path in png_files:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

    def generate_image(self, output_prefix = f"output_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"):
        self.delete_images()

        prompt = json.loads(json.dumps(self._base_prompt))

        # Modify prompt
        for node_id, node in prompt.items():
            if node["class_type"] == "CLIPTextEncode":
                if node_id == "6":  # positive prompt node
                    node["inputs"]["text"] = self._styles_prompts[self._style]
                elif node_id == "7":  # negative prompt node
                    node["inputs"]["text"] = self._negative_prompt
            elif node["class_type"] == "KSampler":
                node["inputs"]["seed"] = random.randint(0, 1000000000)
                node["inputs"]["cfg"] = 2.0
                node["inputs"]["denoise"] = 0.500000000000001
            elif node["class_type"] == "LoadImage":
                node["inputs"]["image"] = "input.png"
            elif node["class_type"] == "SaveImage":
                node["inputs"]["filename_prefix"] = output_prefix

        # Submit to ComfyUI
        print("Submitting prompt to ComfyUI API...")
        print("Prompt to be sent:", json.dumps(prompt, indent=2))
        response = requests.post(f"{self.server_url}/prompt", json={"prompt": prompt})
        response.raise_for_status()
        prompt_id = response.json().get("prompt_id")
        print(f"Prompt submitted with ID: {prompt_id}")
        print(f"API response: {response.status_code}, {response.text}")

        # Optional: Wait for output image to appear
        self._wait_for_image()

    def _wait_for_image(self, timeout=30):
        print("Waiting for image to appear...")
        start = time.time()
        while time.time() - start < timeout:
            images = self.get_image_paths()
            if images:
                print(f"Image ready: {images[0]}")
                return
            time.sleep(1)
        print("Timeout waiting for image.")

    def get_image_paths(self):
        return sorted(glob.glob(os.path.join(self._output_folder, "*.png")), key=os.path.getmtime)


'''
if __name__ == "__main__":
    wrapper = ImageGeneratorAPIWrapper()
    wrapper.set_style("Oil paint")
    wrapper.generate_image(seed=random.randint(0, 1000000000), output_prefix="realistic_output")
    print("Generated image:", wrapper.get_image_paths())
'''