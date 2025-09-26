from multiprocessing import context
import bpy
import math
#from . import rumble
from . import mapping_data
from . import handlers
from . import fastgamepad
from . import mapping_data


def easing(value, easing_type):
    if easing_type == "linear":
        return value
    elif easing_type == "x2":
        return value**2 * (1 if value >= 0 else -1)
    elif easing_type == "x3":
        return value**3
    elif easing_type == "sqrt":
        return math.sqrt(math.fabs(value)) * (1 if value >= 0 else -1)
    elif easing_type == "cubet":
        return math.pow(math.fabs(value),.333) * (1 if value >= 0 else -1)
    elif easing_type == "sin":
        return math.sin(value * math.pi / 2)
    elif easing_type == "log":
        if value == 0:
            return 0
        else:
            return math.copysign(math.log1p(math.fabs(value) * (math.e - 1)), value)
    elif easing_type == "smoothstep":
        x = (value + 1) / 2
        s = 3*x * x - 2 * x * x * x
        return 2 * s -1
    return value