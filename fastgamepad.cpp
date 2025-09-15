#include <Python.h>
#include <SDL3\SDL.h>
#include <map>
#include <iostream>
using namespace std;

struct EMAState {
    bool initialized = false;
    float value = 0.0f;
};

struct DebounceState {
    int stableState = 0;      // last debounced state (0 or 1)
    int pendingState = 0;     // last raw state observed
    Uint64 lastChangeTime = 0; // time of last raw change
};


static SDL_Gamepad* gamepad = nullptr;
static EMAState axisEMA[6];   // lx, ly, rx, ry, lt, rt
static double emaAlpha = 0.2; // default smoothing factor
static std::map<int, DebounceState> buttonStates; 
static Uint64 debounceDelayNS = 30 * 1000000ULL; // 30ms default
static SDL_Joystick *virtual_joystick = NULL;

static PyObject* fg_initialized(PyObject* self, PyObject* args) {
    if (gamepad) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}


static int debounceButton(int button, int rawState) {
    Uint64 now = SDL_GetTicksNS();
    auto &state = buttonStates[button];

    if (rawState != state.pendingState) {
        // Raw state changed → start debounce timer
        state.pendingState = rawState;
        state.lastChangeTime = now;
    } else {
        // Raw state is the same as last time
        if (rawState != state.stableState &&
            (now - state.lastChangeTime) >= debounceDelayNS) {
            // Enough time has passed → commit to stable state
            state.stableState = rawState;
        }
    }

    return state.stableState;
}


static float emaUpdate(EMAState &state, float newValue) {
    if (!state.initialized) {
        state.value = newValue;   // first sample just seeds it
        state.initialized = true;
    } else {
        state.value = (float)(emaAlpha * newValue + (1.0 - emaAlpha) * state.value);
    }
    return state.value;
}

static PyObject* fg_set_smoothing(PyObject* self, PyObject* args) {
    int ms;
    if (!PyArg_ParseTuple(args, "i", &ms)) {
        return NULL;
    }
    
    cout << "Setting smoothing to " << ms << " ms" << endl;
    // Assume poll rate ~60 Hz (~16 ms per sample).
    // Equivalent N samples = ms / 16.
    // Alpha = 2 / (N + 1)
    double N = (double)ms / 16.0;
    if (N < 1) N = 1;
    emaAlpha = 2.0 / (N + 1.0);

    Py_RETURN_NONE;
}
static PyObject* fg_set_debounce(PyObject* self, PyObject* args) {
    int ms;
    
    if (!PyArg_ParseTuple(args, "i", &ms)) {
        return NULL;
    }
    cout << "Setting debounce to " << ms << " ms" << endl;
    debounceDelayNS = (Uint64)ms * 1000000ULL;

    return Py_BuildValue("l", (long)debounceDelayNS / 1000000);
    //Py_RETURN_NONE;
}

static PyObject* fg_init(PyObject* self, PyObject* args) {
    if (SDL_Init(SDL_INIT_GAMEPAD | SDL_INIT_JOYSTICK ) == 0) {
        return PyErr_Format(PyExc_RuntimeError, "SDL_Init failed: %s", SDL_GetError());
    }

    int num_gamepads = 0;
    SDL_JoystickID* gamepad_ids = SDL_GetGamepads(&num_gamepads);

    if (num_gamepads < 1) {
        if (!virtual_joystick) {
        SDL_VirtualJoystickDesc desc;
        SDL_INIT_INTERFACE(&desc);     // zero/init the interface struct. (use SDL_INIT_INTERFACE macro)
        desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
        desc.naxes = 6;    // Lx, Ly, Rx, Ry, LT, RT
        desc.nbuttons = 11; // A,B,X,Y,LB,RB,Back,Start,Guide,LS,RS (adjust as you like)
        desc.nhats = 1;    // d-pad as a POV hat
        desc.name = "Virtual Xbox 360 (SDL3)";

        // Make SDL know which buttons/axes are valid for a gamepad layout.
        // Use SDL_GAMEPAD_AXIS_* and SDL_GAMEPAD_BUTTON_* enum values as bits.
        desc.axis_mask = (1u << SDL_GAMEPAD_AXIS_LEFTX) |
                        (1u << SDL_GAMEPAD_AXIS_LEFTY) |
                        (1u << SDL_GAMEPAD_AXIS_RIGHTX) |
                        (1u << SDL_GAMEPAD_AXIS_RIGHTY) |
                        (1u << SDL_GAMEPAD_AXIS_LEFT_TRIGGER) |
                        (1u << SDL_GAMEPAD_AXIS_RIGHT_TRIGGER);

        desc.button_mask = (1u << SDL_GAMEPAD_BUTTON_SOUTH) |  // A
                        (1u << SDL_GAMEPAD_BUTTON_EAST)  |  // B
                        (1u << SDL_GAMEPAD_BUTTON_WEST)  |  // X
                        (1u << SDL_GAMEPAD_BUTTON_NORTH) |  // Y
                        (1u << SDL_GAMEPAD_BUTTON_LEFT_SHOULDER) |
                        (1u << SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER) |
                        (1u << SDL_GAMEPAD_BUTTON_BACK) |
                        (1u << SDL_GAMEPAD_BUTTON_START) |
                        (1u << SDL_GAMEPAD_BUTTON_GUIDE) |
                        (1u << SDL_GAMEPAD_BUTTON_LEFT_STICK) |
                        (1u << SDL_GAMEPAD_BUTTON_RIGHT_STICK);

        SDL_JoystickID virtual_id = SDL_AttachVirtualJoystick(&desc);

        if (virtual_id == 0) {
            SDL_Log("Couldn't attach virtual device: %s\n", SDL_GetError());
            // Optionally, you might want to return an error here if a virtual joystick is critical
        } else {
            virtual_joystick = SDL_OpenJoystick(virtual_id);
            if (!virtual_joystick) {
                SDL_Log("Couldn't open virtual device: %s\n", SDL_GetError());
                // Optionally, return an error here
            } else {
                SDL_Log("Virtual joystick attached with ID: %d\n", virtual_id);
            }
        }

        gamepad = SDL_OpenGamepad(virtual_id);
    }
        
    if (gamepad_ids) {
        SDL_free(gamepad_ids);
        gamepad_ids = NULL; 
    }

   if (!virtual_joystick) {
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "Failed to create or open virtual joystick");
    }
    } else {
        gamepad = SDL_OpenGamepad(gamepad_ids[0]);
        if (!gamepad) {
            SDL_Quit();
            return PyErr_Format(PyExc_RuntimeError, "Failed to open gamepad: %s", SDL_GetError());
        }
        if (gamepad_ids) {
            SDL_free(gamepad_ids);
            gamepad_ids = NULL;
        }
    }\
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
    
    lx = emaUpdate(axisEMA[0], lx);
    ly = emaUpdate(axisEMA[1], ly);
    rx = emaUpdate(axisEMA[2], rx);
    ry = emaUpdate(axisEMA[3], ry);
    lt = emaUpdate(axisEMA[4], lt);
    rt = emaUpdate(axisEMA[5], rt);

    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "lx", PyFloat_FromDouble(lx));
    PyDict_SetItemString(dict, "ly", PyFloat_FromDouble(ly));   
    PyDict_SetItemString(dict, "rx", PyFloat_FromDouble(rx));
    PyDict_SetItemString(dict, "ry", PyFloat_FromDouble(ry));
    PyDict_SetItemString(dict, "lt", PyFloat_FromDouble(lt));
    PyDict_SetItemString(dict, "rt", PyFloat_FromDouble(rt));
    return dict;
}

static int get_debounced_button(int button) {
    int rawState = SDL_GetGamepadButton(gamepad, (SDL_GamepadButton)button);
    return debounceButton(button, rawState);
}

static PyObject* fg_get_buttons(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    // SDL3 button constants for A, B, X, Y

    int south = get_debounced_button(SDL_GAMEPAD_BUTTON_SOUTH);  // A
    int east = get_debounced_button(SDL_GAMEPAD_BUTTON_EAST); // B
    int west = get_debounced_button(SDL_GAMEPAD_BUTTON_WEST);  // X
    int north = get_debounced_button(SDL_GAMEPAD_BUTTON_NORTH);    // Y

    int lshoulder = get_debounced_button(SDL_GAMEPAD_BUTTON_LEFT_SHOULDER);
    int rshoulder = get_debounced_button(SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER);

    int lstick = get_debounced_button(SDL_GAMEPAD_BUTTON_LEFT_STICK);
    int rstick = get_debounced_button(SDL_GAMEPAD_BUTTON_RIGHT_STICK);

    int dpad_up = get_debounced_button(SDL_GAMEPAD_BUTTON_DPAD_UP);
    int dpad_down = get_debounced_button(SDL_GAMEPAD_BUTTON_DPAD_DOWN);
    int dpad_left = get_debounced_button(SDL_GAMEPAD_BUTTON_DPAD_LEFT);
    int dpad_right = get_debounced_button(SDL_GAMEPAD_BUTTON_DPAD_RIGHT);

    int misc1 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC1);
    int misc2 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC2);
    int misc3 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC3);
    int misc4 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC4);
    int misc5 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC5);
    int misc6 = get_debounced_button(SDL_GAMEPAD_BUTTON_MISC6);

    int back = get_debounced_button(SDL_GAMEPAD_BUTTON_BACK);
    int start = get_debounced_button(SDL_GAMEPAD_BUTTON_START);
    int guide = get_debounced_button(SDL_GAMEPAD_BUTTON_GUIDE);

    int lp1 = get_debounced_button(SDL_GAMEPAD_BUTTON_LEFT_PADDLE1);
    int lp2 = get_debounced_button(SDL_GAMEPAD_BUTTON_LEFT_PADDLE2);
    int rp1 = get_debounced_button(SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1);
    int rp2 = get_debounced_button(SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2);

    int touchbutton = get_debounced_button(SDL_GAMEPAD_BUTTON_TOUCHPAD);


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
    {"initialized", fg_initialized, METH_NOARGS, "Check if gamepad is initialized"},
    {"get_axes", fg_get_axes, METH_NOARGS, "Get joystick axes"},
    {"get_buttons", fg_get_buttons, METH_NOARGS, "Get A/B/X/Y button states"},
    {"set_smoothing", fg_set_smoothing, METH_VARARGS, "Set axis smoothing in ms"},
    {"set_debounce", fg_set_debounce, METH_VARARGS, "Set button debounce window (ms)"},
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
