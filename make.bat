 cl /EHsc /LD fastgamepad.cpp ^
  /std:c++17 ^
  /I"c:\Program Files\Python311\include" ^
  /I"C:\SDL\include" ^
  /link  /LIBPATH:"c:\Program Files\Python311\libs" python311.lib ^
  /LIBPATH:"C:\SDL\VisualC\x64\Release" SDL3.lib

REM copy fastgamepad.dll "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\fastgamepad.pyd"
REM copy controller.py "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\controller.py"
copy fastgamepad.dll fastgamepad.pyd