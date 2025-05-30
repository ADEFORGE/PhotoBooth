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
│   ├── camerawidget.py         # Camera capture widget
│   ├── choosestylewidget.py    # Style selection widget
│   ├── resultwidget.py         # Result display widget
│   └── loadwidget.py           # Loading animation widget
├── workflows/
│   └── image2image.json        # ComfyUI workflow definition
├── gui_main.py                 # Main GUI application
├── photobooth_main.py          # CLI entry point (optional)
├── constante.py                # Style dictionary and constants
```

## Requirements

- Python 3.8+
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) running as a backend server
- [PySide6](https://pypi.org/project/PySide6/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- NumPy

Install dependencies with:

```sh
pip install -r requirements.txt
```

## Setup

1. **Clone this repository in the `comfy` folder and enter the directory:**
    ```sh
    git clone https://github.com/ADEFORGE/PhotoBooth.git
    cd PhotoBooth
    ```

2. **Configure ComfyUI**:
    - Make sure ComfyUI is running and accessible (default: `http://localhost:8188`).
    - Place your workflow JSON in the `workflows/` directory.


3. **Edit `constante.py`** to define your available styles and prompts.

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

## License

MIT License (or your chosen license)

---

**Developed by [Your Name or Team]**