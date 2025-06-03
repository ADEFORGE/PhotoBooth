import json
import os
import glob
import time
import datetime
import random
from constante import dico_styles

class ImageGeneratorAPIWrapper:
    def __init__(self, server_url="http://127.0.0.1:8188"):
        self.server_url = server_url
        self._style = "oil paint"
        self._output_folder = "../ComfyUI/output"
        self._styles_prompts = dico_styles
        self._negative_prompt = "watermark, text"
        self._base_prompt = {}  # Ne charge rien

########### Prompts and styles ###########
    def _load_base_prompt(self):
        return {}

    def set_styles_prompts(self, styles_prompts : dict):
        self._styles_prompts = styles_prompts
        
    def set_style(self, style: str):
        if style in self._styles_prompts:
            self._style = style
        else:
            raise ValueError(f"Style '{style}' not recognized.")

########### Image ###########
    def delete_images(self):
        # Ne fait rien
        pass

    def generate_image(self, output_prefix = "output_test"):
        # Simule un délai pour tester le chargement
        time.sleep(3)

    def _wait_for_image(self, timeout=30):
        # Ne fait rien
        pass

    def get_image_paths(self):
        # Retourne une liste vide ou un faux chemin pour test
        return []


'''
if __name__ == "__main__":
    wrapper = ImageGeneratorAPIWrapper()
    wrapper.set_style("Oil paint")
    wrapper.generate_image(seed=random.randint(0, 1000000000), output_prefix="realistic_output")
    print("Generated image:", wrapper.get_image_paths())
'''