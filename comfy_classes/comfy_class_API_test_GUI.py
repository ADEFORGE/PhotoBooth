import json
import os
import glob
import time
import datetime
import random
from constante import dico_styles
import numpy as np
import cv2

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
        # Crée une fausse image de sortie pour le test
        os.makedirs(self._output_folder, exist_ok=True)
        fake_img_path = os.path.join(self._output_folder, f"{output_prefix}_fake.png")
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(img, self._style, (50, 256), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 3)
        cv2.imwrite(fake_img_path, img)
        self._last_fake_img = fake_img_path

    def _wait_for_image(self, timeout=30):
        # Ne fait rien
        pass

    def get_image_paths(self):
        # Retourne le chemin de la fausse image générée
        if hasattr(self, '_last_fake_img') and os.path.exists(self._last_fake_img):
            return [self._last_fake_img]
        return []


'''
if __name__ == "__main__":
    wrapper = ImageGeneratorAPIWrapper()
    wrapper.set_style("Oil paint")
    wrapper.generate_image(seed=random.randint(0, 1000000000), output_prefix="realistic_output")
    print("Generated image:", wrapper.get_image_paths())
'''