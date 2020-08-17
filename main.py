import os
import subprocess
import sys
from colorama import init, Fore, Back, Style
import time

init()

while (True):
    process = subprocess.Popen([sys.executable, "get_data.py"])
    process.wait()
