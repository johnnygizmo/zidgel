#include <Python.h>
#include <SDL3\SDL.h>

static SDL_Gamepad* gamepad = nullptr;

// Init SDL and open the first gamepad
static PyObject* fg_init(PyObject* self, PyObject* args) {
    if (!SDL_Init(SDL_INIT_GAMEPAD)) {
        return PyErr_Format(PyExc_RuntimeError, "SDL_Init failed: %s", SDL_GetError());
    }
    // int num = SDL_GetNumGamepads();
    int num;
    SDL_JoystickID* ids = SDL_GetGamepads(&num);
    if (num < 1) {
        return PyErr_Format(PyExc_RuntimeError, "No gamepads found");
    }
    gamepad = SDL_OpenGamepad(ids[0]);
    SDL_free(ids);
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Failed to open gamepad: %s", SDL_GetError());
    }
    Py_RETURN_NONE;
}

// Get axes
static PyObject* fg_get_axes(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    float lx = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTX) / 32767.0f;
    float ly = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFTY) / 32767.0f;
    float rx = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_RIGHTX) / 32767.0f;
    float ry = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_RIGHTY) / 32767.0f;
    float lt = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_LEFT_TRIGGER) / 32767.0f;
    float rt = SDL_GetGamepadAxis(gamepad, SDL_GAMEPAD_AXIS_RIGHT_TRIGGER) / 32767.0f;
    
    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "lx", PyFloat_FromDouble(lx));
    PyDict_SetItemString(dict, "ly", PyFloat_FromDouble(ly));   
    PyDict_SetItemString(dict, "rx", PyFloat_FromDouble(rx));
    PyDict_SetItemString(dict, "ry", PyFloat_FromDouble(ry));
    PyDict_SetItemString(dict, "lt", PyFloat_FromDouble(lt));
    PyDict_SetItemString(dict, "rt", PyFloat_FromDouble(rt));
    return dict;
}

static PyObject* fg_get_buttons(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    // SDL3 button constants for A, B, X, Y
    int south = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_SOUTH);  // A
    int east = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_EAST); // B
    int west = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_WEST);  // X
    int north = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_NORTH);    // Y

    int lshoulder = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_LEFT_SHOULDER); 
    int rshoulder = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER); 
 
    int lstick = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_LEFT_STICK); 
    int rstick = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_STICK); 
 
    int dpad_up = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_DPAD_UP);
    int dpad_down = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_DPAD_DOWN);
    int dpad_left = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_DPAD_LEFT);
    int dpad_right = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_DPAD_RIGHT);
 
    int misc1 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC1); 
    int misc2 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC2); 
    int misc3 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC3); 
    int misc4 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC4); 
    int misc5 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC5); 
    int misc6 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_MISC6);
 
    int back = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_BACK);
    int start = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_START);
    int guide = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_GUIDE);
 
    int lp1 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_LEFT_PADDLE1);
    int lp2 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_LEFT_PADDLE2);
    int rp1 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1);
    int rp2 = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2);

    int touchbutton = SDL_GetGamepadButton(gamepad, SDL_GAMEPAD_BUTTON_TOUCHPAD);


    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "south", PyLong_FromLong(south));
    PyDict_SetItemString(dict, "east", PyLong_FromLong(east));
    PyDict_SetItemString(dict, "west", PyLong_FromLong(west));
    PyDict_SetItemString(dict, "north", PyLong_FromLong(north));
    PyDict_SetItemString(dict, "lshoulder", PyLong_FromLong(lshoulder));
    PyDict_SetItemString(dict, "rshoulder", PyLong_FromLong(rshoulder));
    PyDict_SetItemString(dict, "lstick", PyLong_FromLong(lstick));
    PyDict_SetItemString(dict, "rstick", PyLong_FromLong(rstick));
    PyDict_SetItemString(dict, "dpad_up", PyLong_FromLong(dpad_up));
    PyDict_SetItemString(dict, "dpad_down", PyLong_FromLong(dpad_down));
    PyDict_SetItemString(dict, "dpad_left", PyLong_FromLong(dpad_left));
    PyDict_SetItemString(dict, "dpad_right", PyLong_FromLong(dpad_right));
    PyDict_SetItemString(dict, "back", PyLong_FromLong(back));
    PyDict_SetItemString(dict, "start", PyLong_FromLong(start));
    PyDict_SetItemString(dict, "guide", PyLong_FromLong(guide));
    PyDict_SetItemString(dict, "lp1", PyLong_FromLong(lp1));
    PyDict_SetItemString(dict, "lp2", PyLong_FromLong(lp2));
    PyDict_SetItemString(dict, "rp1", PyLong_FromLong(rp1));
    PyDict_SetItemString(dict, "rp2", PyLong_FromLong(rp2));
    PyDict_SetItemString(dict, "misc1", PyLong_FromLong(misc1));
    PyDict_SetItemString(dict, "misc2", PyLong_FromLong(misc2));
    PyDict_SetItemString(dict, "misc3", PyLong_FromLong(misc3));
    PyDict_SetItemString(dict, "misc4", PyLong_FromLong(misc4));
    PyDict_SetItemString(dict, "misc5", PyLong_FromLong(misc5));
    PyDict_SetItemString(dict, "misc6", PyLong_FromLong(misc6));
    PyDict_SetItemString(dict, "touchbutton", PyLong_FromLong(touchbutton));
    
    return dict;
}

static PyObject* fg_quit(PyObject* self, PyObject* args) {
    if (gamepad) {
        SDL_CloseGamepad(gamepad);
        gamepad = nullptr;
    }
    SDL_Quit();
    Py_RETURN_NONE;
}

static PyMethodDef FastGamepadMethods[] = {
    {"init", fg_init, METH_NOARGS, "Init SDL3 and open gamepad"},
    {"get_axes", fg_get_axes, METH_NOARGS, "Get joystick axes"},
    {"get_buttons", fg_get_buttons, METH_NOARGS, "Get A/B/X/Y button states"},
    {"quit", fg_quit, METH_NOARGS, "Close gamepad and quit SDL"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastgamepadmodule = {
    PyModuleDef_HEAD_INIT,
    "fastgamepad",
    "Fast gamepad polling via SDL3",
    -1,
    FastGamepadMethods
};

PyMODINIT_FUNC PyInit_fastgamepad(void) {
    return PyModule_Create(&fastgamepadmodule);
}
