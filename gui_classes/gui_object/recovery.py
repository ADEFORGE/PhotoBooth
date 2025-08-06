# utils/recovery.py

import sys
import subprocess
import os
import logging

def restart_app():
    python = sys.executable
    subprocess.Popen([python] + sys.argv, close_fds=False)
    sys.exit(1)

def reboot_pc():
    os.system("shutdown /r /t 0")


