from multiprocessing import context
import sys
import os
import math
from pathlib import Path
import padtest
padtest.init()

padtest.get_info()
# print(padtest.get_button(2,1))
# print(padtest.get_button(2,2))

padtest.quit()