from . import fastgamepad
fastgamepad.init()
b = fastgamepad.get_buttons()
print(b)
ax = fastgamepad.get_axes()

rounded_ax = {k: round(v * 20) / 20 for k, v in ax.items()}
print(rounded_ax)

fastgamepad.quit()