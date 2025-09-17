from multiprocessing import context
import sys
import os
import math
from pathlib import Path


import fastgamepad
fastgamepad.init()


a = fastgamepad.get_axes()
b = fastgamepad.get_buttons()
c = fastgamepad.get_sensors()

print("Axes:", a)
print("Buttons:", b)    
print("Sensors:", c) 

#fastgamepad.rumble(0xFFFF,0xFFFF,0)
fastgamepad.quit()