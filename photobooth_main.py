import os
import sys

from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
from constante import *

def main():
    wrapper = ImageGeneratorAPIWrapper()
    wrapper.set_styles_prompts(dico_styles)    
    output_prefix = "ComfyUI"

    wrapper.generate_image(output_prefix)

if __name__ == "__main__":
    main()
