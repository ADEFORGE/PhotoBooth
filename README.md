# PhotoBooth

PhotoBooth is a Python-based GUI application for capturing images, applying AI-powered artistic styles, and saving the results. It integrates with [ComfyUI](https://github.com/comfyanonymous/ComfyUI) for image generation and style transfer.

## Features

- Capture images from your camera.
- Choose from multiple styles.
- Apply styles using ComfyUI workflows.
- View and save generated images.

## Project Structure

```
PhotoBooth/
├── comfy_classes/
│   └── comfy_class_API.py      # API wrapper for ComfyUI
├── gui_classes/
│   ├── photobooth_app.py         # Camera capture widget
│   ├── choosestylewidget.py    # Style selection widget
│   ├── resultwidget.py         # Result display widget
│   └── loadwidget.py           # Loading animation widget
├── workflows/
│   └── image2image.json        # ComfyUI workflow definition
├── gui_main.py                 # Main GUI application
├── photobooth_main.py          # CLI entry point (optional)
├── constante.py                # Style dictionary and constants
```

##  Installation

### Setup

1. **Clone this repository in the `comfy` folder and enter the directory:**
    ```sh
    git clone https://github.com/ADEFORGE/PhotoBooth.git
    cd PhotoBooth
    ```

2. **Configure ComfyUI**:
    - Make sure ComfyUI is running and accessible (default: `http://localhost:8188`).
    - Place your workflow JSON in the `workflows/` directory.


3. **Edit `constante.py`** to define your available styles and prompts.


### Requirements

Suivez ces instructions pour configurer votre environnement et installer les dépendances nécessaires à l'application.

#### Linux / macOS

```bash
# 1. Installer le package venv (si nécessaire)
sudo apt update && sudo apt install -y python3-venv

# 2. Créer l'environnement virtuel
python3 -m venv .venv

# 3. Activer l'environnement virtuel
source .venv/bin/activate

# 4. Mettre à jour pip
pip install --upgrade pip

# 5. Installer les dépendances
pip install -r requirements.txt

# 6. Lancer l'application
python3 main.py

# 7. (Optionnel) Sortir de l'environnement virtuel
deactivate
```

#### Windows (PowerShell)

```powershell
# 0. Si le module venv n'est pas disponible, installer virtualenv
pip install virtualenv

# 1. Créer l'environnement virtuel
python -m venv .venv

# 2. Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# 3. Mettre à jour pip
pip install --upgrade pip

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Lancer l'application
python3 ./main.py

# 6. (Optionnel) Sortir de l'environnement virtuel
deactivate
```

```


## Usage

### GUI

Run the main GUI application:

```sh
python gui_main.py
```

### CLI (optional)

You can also generate images from the command line:

```sh
python photobooth_main.py
```

## Customization

- **Add new styles:**  
  Edit `constante.py` and update the style prompts in `comfy_class_API.py`.
- **Change workflow:**  
  Edit or replace `workflows/image2image.json` to match your desired ComfyUI workflow.

## Troubleshooting

- **Import errors:**  
  Make sure you run scripts from the `PhotoBooth` directory and set `PYTHONPATH` if needed.
- **ComfyUI errors:**  
  Ensure the workflow JSON matches the expected format and ComfyUI is running.

---

**Developed by ML Group - UiT Tromsø**
