from multiprocessing import context
import sys
import os
import math
from pathlib import Path


import fastgamepad
fastgamepad.init()
print(fastgamepad.get_axes())
print(fastgamepad.get_buttons())
#fastgamepad.rumble(0xFFFF,0xFFFF,0)
fastgamepad.quit()