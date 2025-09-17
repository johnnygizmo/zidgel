from multiprocessing import context
import sys
import os
import math
from pathlib import Path


import fastgamepad
fastgamepad.init()
print(fastgamepad.get_axes())
print(fastgamepad.get_buttons())

fastgamepad.rumble(0x6CCC,0xCDDD,400)

print(fastgamepad.get_axes())
print(fastgamepad.get_axes())
print(fastgamepad.get_axes())
print(fastgamepad.get_axes())
print(fastgamepad.get_axes())
print(fastgamepad.get_axes())
print(fastgamepad.get_axes())



fastgamepad.quit()