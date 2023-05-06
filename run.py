import time
import subprocess
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtWidgets import *
import numpy as np
import sys
import os
import glob
from collections import deque
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
time.sleep(30)
cmds = "cd /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/deepstream_custom/ && python3 main.py"
run = subprocess.run(cmds, shell = True, capture_output=True, text=True)
