![PhotoBooth Screenshot](photoboothscreenshotsmall.png)

<center><b>Welcome to PhotoBooth!</b><br>Strike a pose and have fun with AI-powered styles.</center>

# PhotoBooth

**PhotoBooth** takes a picture of you from the webcam and generate an imaginary version of your picture, in different styles, using AI. It is a Python-based GUI application which applies AI-powered artistic styles using Comfy.ui. It includes a Raspberry Pi–based hotspot system (optional) for offline image sharing via a captive portal.

---

## Features

- Capture images from a connected camera.
- Choose from multiple artistic styles.
- Apply styles using ComfyUI workflows. (styles are customizable)
- View, save, and share generated images.
- Local hotspot and captive portal for phone downloads without internet.

---

## Hardware requirements

A gamer PC with a GPU is required. It works with a Nvidia 3050 but a bit slow (~20 seconds to generate an image). It has been tested on Windows and Linux. It should work decently with recent Macs.
Connecting to a Raspberry Pi is optional and only required for sharing the generated pictures on a wifi hotspot run on the Raspberry Pi.

---

## Project Structure

```
PhotoBooth/
├── comfy_classes/           # ComfyUI API integration
│   └── comfy_class_API.py
├── gui_classes/            # GUI logic and components (Pyside6)
│   ├── gui_manager/        # Managers for background, language, standby, threads, windows
│   ├── gui_object/         # GUI widgets: buttons, overlays, toolbox, etc.
│   └── gui_window/         # Window classes: main, base, sleep screen
├── gui_template/           # UI assets: icons, textures, gradients, sleep images
├── hotspot_classes/        # Hotspot and captive portal integration (Raspberry Pi)
├── language_file/          # Language translations (norway.json, sami.json, uk.json)
├── workflows/              # ComfyUI workflow definitions (default.json, clay.json, etc.)
├── constant.py             # Application constants and settings
├── prompts.py              # Style prompts for AI transformations
├── main.py                 # Main entry point for the application
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```
---

## Documentation

## Configuration Guide

PhotoBooth uses two key files for configuration:

- **`prompts.py`**: Contains the dictionary `dico_styles` for all available artistic style prompts. You can customize or add new styles by editing this file. Each style entry defines how the AI should transform images in that style.
- **`constant.py`**: This file contains, in particular:
  - Interface appearance settings (colors, fonts, button styles, dimensions)
  - The messages displayed on the screen
  - Paths to working folders (input/output)
  - ComfyUI connection settings
  - The location of the workflows associated with each AI transformation
  - It is possible to fine-tune the appearance and behavior of the application by modifying this file.
  - Important note: Some constants present in this file are no longer used in the current version of the interface, but have been retained to ensure compatibility with older imports and avoid runtime errors.

### Customization possible
Main elements you can edit in `constant.py`:
- **Colors:** The `COLORS` dictionary centralizes all the colors used.
- **Text and button styles:** Constants like `BUTTON_STYLE`, `TITLE_LABEL_STYLE`, `DISPLAY_LABEL_STYLE`, etc., precisely define the visual rendering.
- **Size and layout:** Ratios (`DISPLAY_SIZE_RATIO`, `HUD_SIZE_RATIO`) or margins (`GRID_MARGIN_TOP`, etc.) allow you to adjust the display on screens of various sizes.
- **Custom AI prompt:** The `dico_styles` variable allows you to associate each style with a unique prompt used in the build via ComfyUI.
- **Timeout settings:** `SLEEP_TIMER_SECONDS`, `COUNTDOWN_START`, etc.

### Enable debug logs
There are two constants that control the amount of logs displayed in the console or saved in log files:
- `DEBUG = False`
- `DEBUG_FULL = False`

Set `DEBUG = True` to enable standard logs for monitoring normal execution.
Set `DEBUG_FULL = True` to enable all logs, including frequent operations (e.g., refreshing the image), resulting in very verbose output.

### Change connection addresses (ComfyUI, Flask, WebSocket)
If you have changed the network configuration or launched the services on different ports/addresses, update the following constants:
- `WS_URL = "ws://127.0.0.1:8188/ws"`
- `HTTP_BASE_URL = "http://127.0.0.1:8188"`
- `HOTSPOT_URL = "https://192.168.10.2:5000/share"`

- `WS_URL`: The URL of the WebSocket to receive build notifications from ComfyUI.
- `HTTP_BASE_URL`: HTTP URL to send requests to ComfyUI.
- `HOTSPOT_URL`: Local address of the Raspberry Pi Flask server (see dedicated section).

### Disable hotspot image sharing
If you don't have a Raspberry Pi connected or you don't want to enable Wi-Fi sharing (captive portal), disable this option in `constant.py`:
- `ShareByHotspot = False`


After making changes, restart PhotoBooth to apply your new configuration.

---

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

#### Linux

```bash
sudo apt update
sudo apt install qt6-base-dev
sudo apt install libxcb-cursor0 #may be needed
```

### 5. Configure ComfyUI


#### ComfyUI Installation & Model Setup

Comfy is assumed to be in the same folder as Photobooth. If this is not the case, be sure to set the correct path in `constant.py`.

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

Photobooth assumes that ComfyUI is running and accessible at the local url `HTTP_BASE_URL = "http://127.0.0.1:8188"`.
If it is serving another url, you can modify the `constant.py` to point to the correct one.

#### Linux/macOS
```bash
python main.py
```

#### Windows
You can use a `.bat` script to automate launching PhotoBooth and ComfyUI (change the paths to your correct comfy and photobooth paths):

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

### 8. Quit Photobooth

Just press the keys alt and F4 to close the window. The Photobooth window is configured to be always in front.

---

## Credits

Developed as part of the **Machine Learning Group – UiT Tromsø** demonstration projects.  
Full list of contributors and acknowledgements are included in the PDF documentation.

