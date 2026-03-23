call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" x64

"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\cl.exe" /EHsc /LD fastgamepad.cpp ^
  /std:c++17 ^
  /I"c:\Python313\include" ^
  /I"C:\SDL\include" ^
  /link  /LIBPATH:"c:\Python313\libs" python313.lib ^
  /LIBPATH:"C:\SDL\VisualC\x64\Release" SDL3.lib

REM copy fastgamepad.dll "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\fastgamepad.pyd"
REM copy controller.py "C:\Users\johnn\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\controller.py"
copy fastgamepad.dll ..\fastgamepad.pyd