from multiprocessing import context
#import sys
#import os
#import math
#from pathlib import Path


import fastgamepad
fastgamepad.init()

print(fastgamepad.set_player(-1,0))
print(fastgamepad.set_player(-1,1))

fastgamepad.get_gamepad_count()

#fastgamepad.rumble(0xFFFF,0xFFFF,0)
fastgamepad.quit()