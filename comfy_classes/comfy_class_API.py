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

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL
DEBUG_ImageGeneratorAPIWrapper = DEBUG
from gui_classes.gui_object.constante import (
    WS_URL, HTTP_BASE_URL, BASE_DIR, COMFY_OUTPUT_FOLDER, INPUT_IMAGE_PATH, COMFY_WORKFLOW_DIR, dico_styles
)

TOTAL_STEPS: dict[str, float] = {}
TOTAL_STEPS_SUM: float = 0
PROGRESS_ACCUM: dict[str, float] = {}

class ImageGeneratorAPIWrapper(QObject):
    progress_changed = Signal(float)

    def __init__(self, style: Optional[str] = None, qimg: Optional[QImage] = None) -> None:
        """
        Initialize the ImageGeneratorAPIWrapper with an optional style and input QImage.
        """
        super().__init__()
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Initializing with style={style}")
        self.server_url = HTTP_BASE_URL
        self._styles_prompts = dico_styles
        self._output_folder = COMFY_OUTPUT_FOLDER
        self._workflow_dir = COMFY_WORKFLOW_DIR
        self._style = style if style in self._styles_prompts else next(iter(self._styles_prompts))

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

        self._negative_prompt = 'watermark, text'
        if qimg is not None:
            self.set_img(qimg)
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Initialized. Total steps sum = {TOTAL_STEPS_SUM}")
            
    def set_img(self, qimg: QImage) -> None:
        """
        Set the input image for the workflow by saving the provided QImage.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Setting input image.")
        self.save_qimage(os.path.dirname(INPUT_IMAGE_PATH), qimg)
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Input image set at {INPUT_IMAGE_PATH}")

    def set_style(self, style: str) -> None:
        """
        Set a new style and reload the workflow.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Setting style to {style}.")
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
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Style set to {style}. Total steps = {TOTAL_STEPS_SUM}")
        
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Workflow reloaded for style {style}.")

    @staticmethod
    def find_json_by_name(directory: str, name: str) -> str:
        """
        Find and return the path to the workflow JSON file by style name.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Searching for JSON file for style '{name}' in {directory}")
        target = f"{name}.json"
        default = "default.json"
        found_default = None
        for fname in os.listdir(directory):
            if fname.endswith('.json'):
                if fname == target:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Found JSON: {fname}")
                    return os.path.join(directory, fname)
                if fname == default:
                    found_default = os.path.join(directory, fname)
        if found_default:
            if DEBUG_ImageGeneratorAPIWrapper:
                logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Using default JSON: {found_default}")
            return found_default
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] No JSON found for style '{name}', raising FileNotFoundError")
        raise FileNotFoundError(f"No JSON found for {name}")
    

    def _clear_output_folder(self) -> None:
        """
        Remove existing PNG files in the output folder.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Clearing output folder: {self._output_folder}")
        for fpath in glob.glob(os.path.join(self._output_folder, '*.png')):
            try:
                os.remove(fpath)
            except OSError:
                pass
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Output folder cleared.")

    def _prepare_prompt(self, custom_prompt: Optional[dict]) -> dict:
        """
        Prepare the full prompt dictionary with all required inputs set.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Preparing prompt with custom_prompt={custom_prompt}")
        prompt = json.loads(json.dumps(custom_prompt or self._base_prompt))
        for nid, node in prompt.items():
            ctype = node.get('class_type', '')
            inputs = node.setdefault('inputs', {})
            if DEBUG_ImageGeneratorAPIWrapper:
                logger.info(f"[DEBUG][DEBUG_ImageGeneratorAPIWrapper] Treatment node {nid} ({ctype})")
                
            if ctype.lower().replace(' ', '') in ('textmultiline', 'textmultilinewidget', 'textmultilineprompt') or ctype in ('Text Multiline', 'TextMultiLine'):
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Remplacement inputs['text'] pour node {nid} (Text Multiline)")

                inputs['text'] = self._styles_prompts[self._style]
            elif ctype in ('KSampler', 'KSampler (Efficient)'):
                inputs['seed'] = random.randint(0, 2**32 - 1)
                
                if 'preview_method' in inputs:
                    old_preview = inputs['preview_method']
                    inputs['preview_method'] = 'auto'
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Changed preview_method for node {nid} from {old_preview} to 'auto'")
            elif ctype == 'LoadImage':
                inputs['image'] = INPUT_IMAGE_PATH
            elif ctype == 'SaveImage':
                inputs['filename_prefix'] = 'output'
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info("[DEBUG_ImageGeneratorAPIWrapper] Prompt sent:")
            logger.info(json.dumps(prompt, indent=2, ensure_ascii=False))
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Prepared prompt for generation: {prompt}")
        return prompt


    def generate_image(self, custom_prompt: Optional[dict] = None, timeout: int = 30000) -> None:
        """
        Generate an image synchronously, blocking until completion.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG] Starting image generation…")
        self._clear_output_folder()
        prompt = self._prepare_prompt(custom_prompt)


        ws = create_connection(WS_URL, timeout=None)
        ws.settimeout(None)


        import threading
        def _keep_alive():
            while True:
                try:
                    ws.ping()
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info("[DEBUG][KEEPALIVE] ping sent successfully.")
                except Exception as e:
                    logger.info(f"[DEBUG][KEEPALIVE] Exception ping: {e!r}")
                    break
                time.sleep(15)
        threading.Thread(target=_keep_alive, daemon=True).start()


        welcome = ws.recv()
        try:
            welcome_data = json.loads(welcome)
        except Exception:
            welcome_data = {}
        client_id = welcome_data.get('data', {}).get('sid') or welcome_data.get('data', {}).get('client_id')
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG] Received welcome, client_id={client_id!r}")


        payload = {'client_id': client_id, 'prompt': prompt, 'outputs': [['8', 0]], 'force': True}
        resp = requests.post(f"{self.server_url}/prompt", json=payload)
        resp.raise_for_status()
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info("[DEBUG] Prompt sent via HTTP.")


        MAX_LOG_LEN = 500
        try:
            while True:
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG] Before ws.recv() — connected={ws.connected}")
                try:
                    msg = ws.recv()
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG] After ws.recv() — connected={ws.connected}, raw type: {type(msg).__name__}")
                except WebSocketTimeoutException:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info("[DEBUG] WebSocketTimeoutException: no message, we continue.")
                    continue
                except WebSocketConnectionClosedException as e:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG] WebSocketConnectionClosedException: {e!r}")
                        traceback.logger.info_exc()
                    break
                except Exception as e:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG] Unexpected exception on ws.recv(): {type(e).__name__}: {e!r}")
                        traceback.logger.info_exc()
                    traceback.logger.info_exc()
                    break


                if isinstance(msg, (bytes, bytearray)):
                    continue
                
                if len(msg) > MAX_LOG_LEN:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        snippet = msg[:MAX_LOG_LEN].replace('\n', '\\n')
                        logger.info(f"[DEBUG] msg too long, snippet:\n{snippet}…")
                else:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG] Message text received ({len(msg)} chars.)")


                try:
                    data = json.loads(msg)
                except json.JSONDecodeError:
                    continue

                t = data.get('type', '')
                d = data.get('data', {})
                node = d.get('node')

                if t == 'progress' and node in TOTAL_STEPS:
                    raw = d.get('value', 0)
                    max_steps = TOTAL_STEPS[node]
                    PROGRESS_ACCUM[node] = raw
                    done = sum(PROGRESS_ACCUM.values())
                    pct = done / TOTAL_STEPS_SUM * 100 if TOTAL_STEPS_SUM else 0
                    self.progress_changed.emit(pct)
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG][PROG] {pct:.2f}% — node {node}: {raw}/{max_steps}")
                elif t == 'progress':

                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG] Ignored progress for unknown node {node!r}")
                    continue

                elif t.lower() in ('done', 'execution_success', 'execution_complete', 'execution_end'):
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG][EVENT] GGeneration terminated (type={t})")
                    break

        finally:
            code = getattr(getattr(ws, 'sock', None), 'close_code', None)
            reason = getattr(getattr(ws, 'sock', None), 'close_reason', None)
            if DEBUG_ImageGeneratorAPIWrapper:
                logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Before closing ws — connected={ws.connected}, close_code={code}, close_reason={reason!r}")
            ws.close()
            if DEBUG_ImageGeneratorAPIWrapper:
                logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] After ws.close() — connected={ws.connected}")


    def get_progress_percentage(self) -> float:
        """
        Get the current global progress percentage.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Getting progress percentage.")
        done = sum(PROGRESS_ACCUM.values())
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Progress done: {done}, Total steps sum: {TOTAL_STEPS_SUM}")
        return (done / TOTAL_STEPS_SUM * 100) if TOTAL_STEPS_SUM else 0.0

    def get_image_paths(self) -> List[str]:
        """
        Get a sorted list of generated image file paths.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Getting image paths from output folder: {self._output_folder}")
        return sorted(
            glob.glob(os.path.join(self._output_folder, '*.png')),
            key=os.path.getmtime
        )

    def save_qimage(self, directory: str, image: QImage) -> None:
        """
        Save a QImage to the specified directory as 'input.png'.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Saving QImage to {directory}/input.png")
        if image.isNull():
            raise ValueError("QImage is empty, cannot save.")
        
        os.makedirs(directory, exist_ok=True)
        save_path = os.path.join(directory, "input.png")
        success = image.save(save_path)
        
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Image saved at: {save_path if success else 'Save failed'}")
        
        if not success:
            raise IOError(f"Backup failed for image at {save_path}")
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Image saved successfully at {save_path}")

    def wait_for_and_load_image(self, timeout: float = 10.0, poll_interval: float = 0.5) -> QImage:
        """
        Wait until the output image file is fully written, then load it into a QImage.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Waiting for image file to be ready (timeout={timeout}s, poll_interval={poll_interval}s)")
        start = time.time()
        paths_prev = []
        while time.time() - start < timeout:
            paths = self.get_image_paths()
            if paths and paths != paths_prev:
                latest = paths[-1]

                size1 = os.path.getsize(latest)
                time.sleep(poll_interval)
                size2 = os.path.getsize(latest)
                if size1 == size2 and size1 > 0:
                    if DEBUG_ImageGeneratorAPIWrapper:
                        logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Image file ready: {latest}")
                    return QImage(latest)
                paths_prev = paths
            time.sleep(poll_interval)
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Timeout reached, no image file found.")
        raise TimeoutError("Failed to load image within timeout period.")
    
    def delete_input_and_output_images(self) -> None:
        """
        Delete the input image and all output images from disk.
        """
        if DEBUG_ImageGeneratorAPIWrapper:
            logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Deleting input and output images.")
        if os.path.exists(INPUT_IMAGE_PATH):
            try:
                os.remove(INPUT_IMAGE_PATH)
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Deleted input image: {INPUT_IMAGE_PATH}")
            except OSError as e:
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Failed to delete input image: {e}")

    
        for fpath in glob.glob(os.path.join(self._output_folder, '*.png')):
            try:
                os.remove(fpath)
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Deleted output image: {fpath}")
            except OSError as e:
                if DEBUG_ImageGeneratorAPIWrapper:
                    logger.info(f"[DEBUG_ImageGeneratorAPIWrapper] Failed to delete output image {fpath}: {e}")



if __name__ == '__main__':
    wrapper = ImageGeneratorAPIWrapper(style='oil paint')
    wrapper.generate_image()
    img = wrapper.wait_for_and_load_image()
    wrapper.delete_input_and_output_images()

    logger.info(f"Loaded QImage: {img.isNull() and 'Failed' or 'Success'}")
    from PySide6.QtWidgets import QApplication, QLabel
    from PySide6.QtGui import QPixmap
    import sys

    app = QApplication.instance() or QApplication(sys.argv)

    label = QLabel()
    label.setPixmap(QPixmap.fromImage(img))
    label.setWindowTitle("Generated Image")
    label.resize(img.width(), img.height())
    label.show()

    sys.exit(app.exec())