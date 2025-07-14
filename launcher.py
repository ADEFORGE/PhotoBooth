import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication

DEBUG_AppLauncher = False
DEBUG_ComfyWatcherThread = False

class AppLauncher(QObject):
    class ComfyWatcherThread(QThread):
        percentage_updated = Signal(float)
        comfy_ready = Signal()

        def __init__(self, comfy_exe_path: str, log_file_path: Path) -> None:
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Entering __init__: args={(comfy_exe_path, log_file_path)}")
            super().__init__()
            self.comfy_exe_path = comfy_exe_path
            self._process: Optional[subprocess.Popen] = None
            self._running = True
            self.log_file_path = log_file_path
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Exiting __init__: return=None")

        def run(self) -> None:
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Entering run: args=()")
            percentage_regex = re.compile(r'(\d+)%')

            with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
                self._process = subprocess.Popen(
                    [self.comfy_exe_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1,
                    text=True,
                    universal_newlines=True
                )

                try:
                    while self._running and self._process.stdout:
                        line = self._process.stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        log_file.write(line + "\n")
                        log_file.flush()

                        match = percentage_regex.search(line)
                        if match:
                            perc = float(match.group(1))
                            self.percentage_updated.emit(perc)

                        if 'All startup tasks have been completed.' in line:
                            self.comfy_ready.emit()
                finally:
                    if self._process.stdout:
                        self._process.stdout.close()
                    self._process.wait()
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Exiting run: return=None")

        def stop(self) -> None:
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Entering stop: args=()")
            self._running = False
            if self._process and self._process.poll() is None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()
            if DEBUG_ComfyWatcherThread:
                print(f"[DEBUG][ComfyWatcherThread] Exiting stop: return=None")

    def __init__(self, comfy_exe_path: str, photobooth_dir: str) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering __init__: args={(comfy_exe_path, photobooth_dir)}")
        super().__init__()
        self.comfy_exe_path = comfy_exe_path
        self.photobooth_dir = photobooth_dir
        self._percentage = 0.0
        self._comfy_thread: Optional[AppLauncher.ComfyWatcherThread] = None
        self._photobooth_process: Optional[subprocess.Popen] = None
        self.log_file_path = Path(__file__).parent / 'tmp' / 'watcher.log'
        os.makedirs(self.log_file_path.parent, exist_ok=True)
        if self.log_file_path.exists():
            try:
                self.log_file_path.unlink()
            except Exception:
                pass
        signal.signal(signal.SIGINT, self._signal_handler)
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting __init__: return=None")

    def _signal_handler(self, sig: int, frame) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering _signal_handler: args={(sig, frame)}")
        self.stop()
        sys.exit(0)
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting _signal_handler: return=None")

    def _on_percentage_updated(self, perc: float) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering _on_percentage_updated: args=({perc},)")
        self._percentage = perc
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting _on_percentage_updated: return=None")

    def _on_comfy_ready(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering _on_comfy_ready: args=()")
        self.launch_photobooth()
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting _on_comfy_ready: return=None")

    def launch_comfyui(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering launch_comfyui: args=()")
        if self._comfy_thread is not None:
            if DEBUG_AppLauncher:
                print(f"[DEBUG][AppLauncher] Exiting launch_comfyui: return=None")
            return
        self._comfy_thread = self.ComfyWatcherThread(self.comfy_exe_path, self.log_file_path)
        self._comfy_thread.percentage_updated.connect(self._on_percentage_updated)
        self._comfy_thread.comfy_ready.connect(self._on_comfy_ready)
        self._comfy_thread.start()
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting launch_comfyui: return=None")

    def launch_photobooth(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering launch_photobooth: args=()")
        if self._photobooth_process is not None:
            if DEBUG_AppLauncher:
                print(f"[DEBUG][AppLauncher] Exiting launch_photobooth: return=None")
            return
        photobooth_main = os.path.join(self.photobooth_dir, 'main.py')
        self._photobooth_process = subprocess.Popen(
            ['python3', photobooth_main],
            cwd=self.photobooth_dir
        )
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting launch_photobooth: return=None")

    def launch_full_app_in_order(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering launch_full_app_in_order: args=()")
        self.launch_comfyui()
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting launch_full_app_in_order: return=None")

    def start_percentage_monitoring(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering start_percentage_monitoring: args=()")
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting start_percentage_monitoring: return=None")

    def stop(self) -> None:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering stop: args=()")
        if self._comfy_thread is not None:
            self._comfy_thread.stop()
            self._comfy_thread.wait()
            self._comfy_thread = None
        if self._photobooth_process is not None:
            self._photobooth_process.terminate()
            self._photobooth_process.wait()
            self._photobooth_process = None
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting stop: return=None")

    def get_percentage(self) -> float:
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Entering get_percentage: args=()")
        result = self._percentage
        if DEBUG_AppLauncher:
            print(f"[DEBUG][AppLauncher] Exiting get_percentage: return={result}")
        return result


if __name__ == "__main__":
    comfy_exe_path = r"C:\Users\vitensenteret_ml3\AppData\Local\Programs\@comfyorgcomfyui-electron\ComfyUI.exe"
    base_dir = os.path.abspath(os.path.dirname(__file__))
    photobooth_dir = os.path.join(base_dir, '..', 'PhotoBooth')

    app = QApplication(sys.argv)
    launcher = AppLauncher(comfy_exe_path, photobooth_dir)
    launcher.launch_full_app_in_order()
    sys.exit(app.exec())
