import threading
from . import fastgamepad

def rumble_async(strong, weak, ms):
    """Start rumble, then stop after ms milliseconds."""
    # Start the rumble immediately
    fastgamepad.rumble(strong, weak, ms)

    # Schedule stop after ms milliseconds
    def stop():
        try:
            fastgamepad.rumble(0, 0, 0)  # stop rumble
        except Exception as e:
            print("Error stopping rumble:", e)

    t = threading.Timer(ms/1000, stop)
    t.daemon = True  # so Blender can exit cleanly
    t.start()