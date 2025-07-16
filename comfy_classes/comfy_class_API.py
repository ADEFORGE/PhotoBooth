#!/usr/bin/env python3
import glob
import json
import os
import random
import time
from typing import List, Optional

import requests
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException, create_connection
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

import traceback
from websocket import WebSocketConnectionClosedException, WebSocketTimeoutException, create_connection


DEBUG_ImageGeneratorAPIWrapper = True
from gui_classes.gui_object.constante import (
    WS_URL, HTTP_BASE_URL, BASE_DIR, COMFY_OUTPUT_FOLDER, INPUT_IMAGE_PATH, COMFY_WORKFLOW_DIR, DICO_STYLES
)

# Progress tracking globals
TOTAL_STEPS: dict[str, float] = {}
TOTAL_STEPS_SUM: float = 0
PROGRESS_ACCUM: dict[str, float] = {}

class ImageGeneratorAPIWrapper(QObject):
    progress_changed = Signal(float)  # Signal: percentage (0.0 to 100.0)
    def __init__(self, style: Optional[str] = None, qimg: Optional[QImage] = None) -> None:
        super().__init__()
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG_ImageGeneratorAPIWrapper] Initializing with style={style}")
        self.server_url = HTTP_BASE_URL
        self._styles_prompts = DICO_STYLES
        self._output_folder = COMFY_OUTPUT_FOLDER
        self._workflow_dir = COMFY_WORKFLOW_DIR
        self._style = style if style in self._styles_prompts else next(iter(self._styles_prompts))

        # Load workflow JSON
        path = self.find_json_by_name(self._workflow_dir, self._style)
        with open(path, encoding='utf-8') as f:
            self._base_prompt = json.load(f)

        # Setup step tracking
        global TOTAL_STEPS, TOTAL_STEPS_SUM
        TOTAL_STEPS = {
            nid: node['inputs']['steps']
            for nid, node in self._base_prompt.items()
            if isinstance(node.get('inputs', {}).get('steps'), (int, float))
        }
        TOTAL_STEPS_SUM = sum(TOTAL_STEPS.values())

        self._negative_prompt = 'watermark, text'
        if qimg is not None:
            self.set_img(qimg)
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG_ImageGeneratorAPIWrapper] Initialized. Total steps sum = {TOTAL_STEPS_SUM}")
            
    def set_img(self, qimg: QImage) -> None:
        """
        Set the input image for the workflow by saving the provided QImage to the input directory as 'input.png'.

        :param qimg: QImage to save as input image.
        :raises ValueError: If the image is invalid.
        """
        self.save_qimage(os.path.dirname(INPUT_IMAGE_PATH), qimg)

    def set_style(self, style: str) -> None:
        """Set a new style and reload workflow."""
        if style not in self._styles_prompts:
            raise ValueError(f"Style '{style}' not found.")
        self._style = style
        path = self.find_json_by_name(self._workflow_dir, self._style)
        with open(path, encoding='utf-8') as f:
            self._base_prompt = json.load(f)

        global TOTAL_STEPS, TOTAL_STEPS_SUM
        TOTAL_STEPS = {
            nid: node['inputs']['steps']
            for nid, node in self._base_prompt.items()
            if isinstance(node.get('inputs', {}).get('steps'), (int, float))
        }
        TOTAL_STEPS_SUM = sum(TOTAL_STEPS.values())
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG_ImageGeneratorAPIWrapper] Style set to {style}. Total steps = {TOTAL_STEPS_SUM}")

    @staticmethod
    def find_json_by_name(directory: str, name: str) -> str:
        """Find workflow JSON by style name."""
        target = f"{name}.json"
        default = "default.json"
        found_default = None
        for fname in os.listdir(directory):
            if fname.endswith('.json'):
                if fname == target:
                    return os.path.join(directory, fname)
                if fname == default:
                    found_default = os.path.join(directory, fname)
        if found_default:
            return found_default
        raise FileNotFoundError(f"No JSON found for {name}")

    def _clear_output_folder(self) -> None:
        """Remove existing PNG files in output folder."""
        for fpath in glob.glob(os.path.join(self._output_folder, '*.png')):
            try:
                os.remove(fpath)
            except OSError:
                pass

    def _prepare_prompt(self, custom_prompt: Optional[dict]) -> dict:
        """Prepare full prompt dict with inputs set. Modifies preview_method if KSampler (Efficient) node exists."""
        prompt = json.loads(json.dumps(custom_prompt or self._base_prompt))
        for nid, node in prompt.items():
            ctype = node.get('class_type', '')
            inputs = node.setdefault('inputs', {})
            if ctype == 'Text MultiLine':
                if DEBUG_ImageGeneratorAPIWrapper:
                    print("[DEBUG_ImageGeneratorAPIWrapper] Prompt modifier <Text MultiLine> found, setting inputs['text']")
                inputs['text'] = (
                    self._styles_prompts[self._style] if nid == '6' else self._negative_prompt
                )
            elif ctype in ('KSampler', 'KSampler (Efficient)'):
                inputs['seed'] = random.randint(0, 2**32 - 1)
                # Force preview_method to 'auto' if present
                if 'preview_method' in inputs:
                    old_preview = inputs['preview_method']
                    inputs['preview_method'] = 'auto'
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG_ImageGeneratorAPIWrapper] Changed preview_method for node {nid} from {old_preview} to 'auto'")
            elif ctype == 'LoadImage':
                inputs['image'] = INPUT_IMAGE_PATH
            elif ctype == 'SaveImage':
                inputs['filename_prefix'] = 'output'
        if DEBUG_ImageGeneratorAPIWrapper:
            print("[DEBUG_ImageGeneratorAPIWrapper] Prompt envoyé:")
            print(json.dumps(prompt, indent=2, ensure_ascii=False))
        return prompt


    def generate_image(self, custom_prompt: Optional[dict] = None, timeout: int = 30000) -> None:
        """Generate an image synchronously, blocking until completion, with detailed WebSocket logging,
        message truncation, et filtration des pourcentages non désirés."""
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG] Starting image generation…")
        self._clear_output_folder()
        prompt = self._prepare_prompt(custom_prompt)

        # --- Ouvrir WS sans timeout ---
        ws = create_connection(WS_URL, timeout=None)
        ws.settimeout(None)

        # Thread de keep-alive
        import threading
        def _keep_alive():
            while True:
                try:
                    ws.ping()
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print("[DEBUG][KEEPALIVE] ping envoyé")
                except Exception as e:
                    print(f"[DEBUG][KEEPALIVE] Exception ping: {e!r}")
                    break
                time.sleep(15)
        threading.Thread(target=_keep_alive, daemon=True).start()

        # Récupérer client_id
        welcome = ws.recv()
        try:
            welcome_data = json.loads(welcome)
        except Exception:
            welcome_data = {}
        client_id = welcome_data.get('data', {}).get('sid') or welcome_data.get('data', {}).get('client_id')
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG] Received welcome, client_id={client_id!r}")

        # Envoi du prompt par HTTP
        payload = {'client_id': client_id, 'prompt': prompt, 'outputs': [['8', 0]], 'force': True}
        resp = requests.post(f"{self.server_url}/prompt", json=payload)
        resp.raise_for_status()
        if DEBUG_ImageGeneratorAPIWrapper:
            print("[DEBUG] Prompt envoyé via HTTP.")

        # Boucle d'écoute
        MAX_LOG_LEN = 500
        try:
            while True:
                if DEBUG_ImageGeneratorAPIWrapper:
                    print(f"[DEBUG] Avant ws.recv() — connected={ws.connected}")
                try:
                    msg = ws.recv()
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG] Après ws.recv() — connected={ws.connected}, raw type: {type(msg).__name__}")
                except WebSocketTimeoutException:
                    print("[DEBUG] WebSocketTimeoutException: pas de message, on continue.")
                    continue
                except WebSocketConnectionClosedException as e:
                    print(f"[DEBUG] WebSocketConnectionClosedException: {e!r}")
                    traceback.print_exc()
                    break
                except Exception as e:
                    print(f"[DEBUG] Exception inattendue sur ws.recv(): {type(e).__name__}: {e!r}")
                    traceback.print_exc()
                    break

                # Filtrer le binaire
                if isinstance(msg, (bytes, bytearray)):
                    continue

                # Tronquer long messages
                if len(msg) > MAX_LOG_LEN:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        snippet = msg[:MAX_LOG_LEN].replace('\n', '\\n')
                        print(f"[DEBUG] msg trop long, snippet:\n{snippet}…")
                else:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG] Message texte reçu ({len(msg)} car.)")

                # Parser JSON
                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue

                t = data.get('type', '')
                d = data.get('data', {})
                node = d.get('node')
                # On ne traite les progress que si node est en TOTAL_STEPS
                if t == 'progress' and node in TOTAL_STEPS:
                    raw = d.get('value', 0)
                    max_steps = TOTAL_STEPS[node]
                    PROGRESS_ACCUM[node] = raw
                    done = sum(PROGRESS_ACCUM.values())
                    pct = done / TOTAL_STEPS_SUM * 100 if TOTAL_STEPS_SUM else 0
                    self.progress_changed.emit(pct)
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG][PROG] {pct:.2f}% — node {node}: {raw}/{max_steps}")
                elif t == 'progress':
                    # cas ignoré : soit pas de node, soit node non suivi
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG] Ignored progress for unknown node {node!r}")
                    continue

                elif t.lower() in ('done', 'execution_success', 'execution_complete', 'execution_end'):
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG][EVENT] Génération terminée (type={t})")
                    break

        finally:
            code = getattr(getattr(ws, 'sock', None), 'close_code', None)
            reason = getattr(getattr(ws, 'sock', None), 'close_reason', None)
            print(f"[DEBUG] Avant fermeture ws — connected={ws.connected}, close_code={code}, close_reason={reason!r}")
            ws.close()
            print(f"[DEBUG] Après ws.close() — connected={ws.connected}")


    def get_progress_percentage(self) -> float:
        """Get current global progress percentage."""
        done = sum(PROGRESS_ACCUM.values())
        return (done / TOTAL_STEPS_SUM * 100) if TOTAL_STEPS_SUM else 0.0

    def get_image_paths(self) -> List[str]:
        """Get sorted list of generated image file paths."""
        return sorted(
            glob.glob(os.path.join(self._output_folder, '*.png')),
            key=os.path.getmtime
        )

    def save_qimage(self, directory: str, image: QImage) -> None:
        """
        Sauvegarde une QImage dans le répertoire spécifié sous le nom 'input.png'.

        :param directory: Chemin du répertoire de destination.
        :param image: L'image à sauvegarder.
        :raises ValueError: Si l'image est vide ou invalide.
        """
        if image.isNull():
            raise ValueError("QImage est vide, impossible de sauvegarder.")
        
        os.makedirs(directory, exist_ok=True)
        save_path = os.path.join(directory, "input.png")
        success = image.save(save_path)
        
        if DEBUG_ImageGeneratorAPIWrapper:
            print(f"[DEBUG_ImageGeneratorAPIWrapper] Image sauvegardée dans : {save_path if success else 'Échec de la sauvegarde'}")
        
        if not success:
            raise IOError(f"Échec de la sauvegarde de l'image à {save_path}")
        
    def wait_for_and_load_image(self, timeout: float = 10.0, poll_interval: float = 0.5) -> QImage:
        """Wait until output image file is fully written, then load into QImage."""
        start = time.time()
        paths_prev = []
        while time.time() - start < timeout:
            paths = self.get_image_paths()
            if paths and paths != paths_prev:
                latest = paths[-1]
                # check file write completion by size stability
                size1 = os.path.getsize(latest)
                time.sleep(poll_interval)
                size2 = os.path.getsize(latest)
                if size1 == size2 and size1 > 0:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        print(f"[DEBUG_ImageGeneratorAPIWrapper] Image file ready: {latest}")
                    return QImage(latest)
                paths_prev = paths
            time.sleep(poll_interval)
        raise TimeoutError("Failed to load image within timeout period.")
    
    def delete_input_and_output_images(self) -> None:
        """Delete input image and all output images."""
        # Delete input image
        if os.path.exists(INPUT_IMAGE_PATH):
            try:
                os.remove(INPUT_IMAGE_PATH)
                if DEBUG_ImageGeneratorAPIWrapper:
                    print(f"[DEBUG_ImageGeneratorAPIWrapper] Deleted input image: {INPUT_IMAGE_PATH}")
            except OSError as e:
                if DEBUG_ImageGeneratorAPIWrapper:
                    print(f"[DEBUG_ImageGeneratorAPIWrapper] Failed to delete input image: {e}")

        # Delete output images
        for fpath in glob.glob(os.path.join(self._output_folder, '*.png')):
            try:
                os.remove(fpath)
                if DEBUG_ImageGeneratorAPIWrapper:
                    print(f"[DEBUG_ImageGeneratorAPIWrapper] Deleted output image: {fpath}")
            except OSError as e:
                if DEBUG_ImageGeneratorAPIWrapper:
                    print(f"[DEBUG_ImageGeneratorAPIWrapper] Failed to delete output image {fpath}: {e}")



if __name__ == '__main__':
    wrapper = ImageGeneratorAPIWrapper(style='oil paint')
    wrapper.generate_image()
    img = wrapper.wait_for_and_load_image()
    wrapper.delete_input_and_output_images()

    print(f"Loaded QImage: {img.isNull() and 'Failed' or 'Success'}")
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtGui import QPixmap
    import sys

    # Démarre une application Qt si ce n'est pas déjà fait
    app = QApplication.instance() or QApplication(sys.argv)

    # Crée un QLabel pour afficher l'image
    label = QLabel()
    label.setPixmap(QPixmap.fromImage(img))
    label.setWindowTitle("Image générée")
    label.resize(img.width(), img.height())
    label.show()

    # Lancer la boucle événementielle
    sys.exit(app.exec())