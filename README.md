# PhotoBooth

**PhotoBooth** is a Python-based GUI application for capturing images, applying AI-powered artistic styles, and sharing the results.  
It integrates with **ComfyUI** for image generation and style transfer, and includes a Raspberry Pi–based hotspot system for offline image sharing via a captive portal.

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

All installation, configuration, and usage instructions are provided in:  

**`CR_Installation_Photobooth_2025_V3_en.pdf`**  

This document covers:  
- Software and hardware prerequisites  
- Installation for the generation PC and Raspberry Pi  
- Hotspot and captive portal setup  
- Workflow and style customization  

---

## Credits

Developed as part of the **Machine Learning Group – UiT Tromsø** demonstration projects.  
Full list of contributors and acknowledgements are included in the PDF documentation.

