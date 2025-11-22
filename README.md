# PhotoBooth

**PhotoBooth** is a Python-based GUI application for capturing images, applying AI-powered artistic styles, and sharing the results.  
It integrates with **ComfyUI** for image generation and style transfer, and includes a Raspberry Pi–based hotspot system (optional) for offline image sharing via a captive portal.

---

## Features

- Capture images from a connected camera.
- Choose from multiple artistic styles.
- Apply styles using ComfyUI workflows.
- View, save, and share generated images.
- Local hotspot and captive portal for phone downloads without internet.

---

## Project Structure

```
PhotoBooth/
├── comfy_classes/        # Handles communication with ComfyUI
│   └── comfy_class_API.py
├── gui_classes/          # GUI components (PySide6)
│   ├── photobooth_app.py      # Main PhotoBooth GUI logic
│   ├── choosestylewidget.py  # Widget to select image styles
│   ├── resultwidget.py       # Widget to display generated results
│   └── loadwidget.py         # Widget to load or process images
├── workflows/            # ComfyUI workflow definitions
│   └── default.json          # Default workflow configuration
├── constant.py          # Style dictionary and constants
├── main.py               # Entry point for the GUI application
└── hotspot_classes/      # Raspberry Pi hotspot integration
```
---

## Documentation


## Installation

Follow these steps to install and set up PhotoBooth. For full details, refer to **`CR_Installation_Photobooth_2025_V3_en.pdf`**.

### 1. Prerequisites

- Python 3.10 or newer
- Raspberry Pi OS (for hotspot features, if using Raspberry Pi)
- Camera connected to your PC or Raspberry Pi

### 2. Clone the Repository

```bash
git clone https://github.com/uitml/PhotoBooth.git
cd PhotoBooth
```

### 3. Install Python Dependencies

It is recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Additional AI/FaceID dependencies

```bash
pip install insightface
pip install onnxruntime
pip install onnxruntime-gpu
```

### 4. Install Qt (Qt6) and System Libraries

```bash
sudo apt update
sudo apt install qt6-base-dev
sudo apt install libxcb-cursor0
```

### 5. Configure ComfyUI


#### ComfyUI Installation & Model Setup

1. **Install ComfyUI**
	 - Follow instructions at: https://github.com/comfyanonymous/ComfyUI
	 - Example (Linux):
		 ```bash
		 git clone https://github.com/comfyanonymous/ComfyUI.git
		 cd ComfyUI
		 python3 -m venv venv
		 source venv/bin/activate
		 pip install -r requirements.txt
		 python main.py
		 ```


2. **Install Custom Nodes and Extensions**
	 - For enhanced features, search for and install the following ComfyUI custom nodes:
		 - [ComfyUI_IPAdapter_plus](https://github.com/cubiq/ComfyUI_IPAdapter_plus)
		 - [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux)
		 - [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts)
		 - [efficiency-nodes-comfyui](https://github.com/jags111/efficiency-nodes-comfyui)
		 - [was-node-suite-comfyui](https://github.com/ltdrdata/was-node-suite-comfyui)

	 - **Automatic installation:**
		 - Use the ComfyUI Manager or extension installer (if available) to search for and install these nodes.

	 - **Manual installation:**
		 - Go to the `ComfyUI/custom_nodes` directory and run:
			 ```bash
			 git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git
			 git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git
			 git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git
			 git clone https://github.com/jags111/efficiency-nodes-comfyui.git
			 git clone https://github.com/ltdrdata/was-node-suite-comfyui.git
			 ```
		 - Restart ComfyUI after installing new nodes.

3. **Download Required Models**
	 - **ControlNet Models:**
		 - Place in `ComfyUI/models/controlnet/`
		 - Download from:
			 - [Depth](https://huggingface.co/lllyasviel/control_v11f1p_sd15_depth)
			 - [IP2P](https://huggingface.co/lllyasviel/control_v11e_sd15_ip2p)
	 - **Stable Diffusion Checkpoints:**
		 - Place in `ComfyUI/models/checkpoints/`
		 - Example: [DreamShaper](https://civitai.com/models/4384/dreamshaper) (any SD 1.5 model can be used)
	 - **Other Models:**
		 - For IP-Adapter, follow the procedure in the [ComfyUI_IPAdapter_plus documentation](https://github.com/cubiq/ComfyUI_IPAdapter_plus).
	 - **VAE Models:** (optional, for better color reproduction)
		 - Place in `ComfyUI/models/vae/`
	 - **InsightFace Models:** (for face recognition)
		 - Place in `ComfyUI/models/insightface/`
	 - **ONNX Models:** (for onnxruntime)
		 - Place in appropriate subfolders under `ComfyUI/models/`

3. **Configure Workflows**
	 - Place workflow JSON files (e.g., `default.json`, `comic.json`) in the `workflows/` directory of PhotoBooth.
	 - You can create or edit workflows in the ComfyUI web interface and export them as JSON.

4. **Test ComfyUI**
	 - Start ComfyUI and verify that models are detected and loaded correctly.
	 - Ensure the PhotoBooth app can communicate with ComfyUI (see PDF for API/config details).

### 6. Hotspot & Captive Portal Setup (Raspberry Pi)

Follow the steps in the PDF to set up the hotspot and captive portal. Place configuration files in `hotspot_classes/in_py/configuration_files/` as described.

### 7. Run PhotoBooth


#### Linux/macOS
```bash
python main.py
```

#### Windows
You can use a `.bat` script to automate launching PhotoBooth and ComfyUI:

```bat
@echo off
del /f /q "C:\AI Demos\PhotoBooth\app.log"
start "" "C:\Users\vitensenteret_ml3\AppData\Local\Programs\@comfyorgcomfyui-electron\ComfyUI.exe"
cd /d "C:\AI Demos\PhotoBooth"
python .\main.py
pause
```

**This script does the following:**
- Deletes the previous log file.
- Launches the ComfyUI executable (via ComfyUI Electron).
- Starts the PhotoBooth app.
- Leaves the window open (useful for checking for any error messages).

**Note:**
Adapt this `.bat` file to your own configuration, including the paths to `ComfyUI.exe` and the PhotoBooth folder.

---

## Credits

Developed as part of the **Machine Learning Group – UiT Tromsø** demonstration projects.  
Full list of contributors and acknowledgements are included in the PDF documentation.

