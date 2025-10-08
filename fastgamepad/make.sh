#!/bin/bash

# Homebrew Python headers (with Python.h available)
BREW_PY_INC="/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/include/python3.11"
BREW_PY_LIB="/opt/homebrew/opt/python@3.11/Frameworks/Python.framework/Versions/3.11/lib"

clang++ -std=c++17 \
  -I"$BREW_PY_INC" \
  -L"$BREW_PY_LIB" \
  -shared -undefined dynamic_lookup \
  -fPIC \
  fastgamepad.cpp \
  -o fastgamepad.so \
  -Wl,-rpath,@loader_path \
  -I/opt/homebrew/include -L/opt/homebrew/lib -lSDL3

install_name_tool -change /opt/homebrew/opt/sdl3/lib/libSDL3.0.dylib @loader_path/libSDL3.0.dylib fastgamepad.so


if [ -f fastgamepad.so ]; then
    mv fastgamepad.so ..
    echo "✅ Build succeeded, moved fastgamepad.so to parent folder."
else
    echo "❌ Build failed, fastgamepad.so not created."
fi
