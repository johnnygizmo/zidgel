from multiprocessing import context
import sys
import os
import math
from pathlib import Path
import padtest
padtest.init()
b = padtest.get_button(0,1)
print (b)
padtest.quit()