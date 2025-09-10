 cl /EHsc /LD fastgamepad.cpp ^
  /I"c:\Program Files\Python311\include" ^
  /I"C:\SDL\include" ^
  /link  /LIBPATH:"c:\Program Files\Python311\libs" python311.lib ^
  /LIBPATH:"C:\SDL\VisualC\x64\Debug" SDL3.lib

copy fastgamepad.dll "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\fastgamepad.pyd"
copy controller.py "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\controller.py"
copy fastgamepad.dll fastgamepad.pyd