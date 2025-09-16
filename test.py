from multiprocessing import context
import sys
import os
import math
from pathlib import Path


import fastgamepad
fastgamepad.init()
print(fastgamepad.get_axes())
print(fastgamepad.get_buttons())
fastgamepad.set_smoothing_single(5,2)
fastgamepad.set_smoothing_single(30,3)
fastgamepad.quit()