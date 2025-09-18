#include <Python.h>
#include <SDL3\SDL.h>
#include <map>
#include <iostream>
#include <cstdio>
#include <unordered_map>
using namespace std;

struct EMAState {
    double emaAlpha = 0.2;
    bool initialized = false;
    float value = 0.0f;
};

struct DebounceState {
    Uint64 debounceDelayNS = 30 * 1000000ULL; 
    int stableState = 0;      // last debounced state (0 or 1)
    int pendingState = 0;     // last raw state observed
    Uint64 lastChangeTime = 0; // time of last raw change
};

struct Input {
    int id = -1;
    int type = 0;
    string name = "";
    int index = 0;
    EMAState smoothing;
    DebounceState debounce;
};

static SDL_Gamepad* gamepad = nullptr;
static unordered_map<int,Input> inputs;
static EMAState axisEMA[6];   // lx, ly, rx, ry, lt, rt
static double emaAlpha = 0.2; // default smoothing factor
static std::map<int, DebounceState> buttonStates; 
static Uint64 debounceDelayNS = 30 * 1000000ULL; // 30ms default
static SDL_Joystick* virtual_joystick = NULL;
static SDL_Haptic* haptic = NULL;
static SDL_HapticID* haptics = NULL;

static PyObject *run_haptic(PyObject* self, PyObject* args){
    int ms;
    int f1;
    int f2;
    if (!PyArg_ParseTuple(args, "iii",&f1, &f2, &ms)) {
        return NULL;
    }
    SDL_RumbleGamepad(gamepad,  f1, f2, ms);
    Py_RETURN_NONE;
}


static PyObject* fg_initialized(PyObject* self, PyObject* args) {
    if (gamepad) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
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


static int debounceButtonState(int button, int rawState) {
    Uint64 now = SDL_GetTicksNS();
    auto &state = inputs[button].debounce;

    if (rawState != state.pendingState) {
        state.pendingState = rawState;
        state.lastChangeTime = now;
    } else {
        if (rawState != state.stableState &&
            (now - state.lastChangeTime) >= debounceDelayNS) {
            state.stableState = rawState;
        }
    }
    return state.stableState;
}

static float get_button(int id,int index=0){
    Input i = inputs[id]; 
    
    if(i.type == 1){
        float value =  SDL_GetGamepadAxis(gamepad, (SDL_GamepadAxis)i.id) / 32767.0f;
        if(emaAlpha > 0){
            value =  emaUpdate(inputs[id].smoothing, value);
        }
        return value;
    } else if (i.type==0) {
        int value = SDL_GetGamepadButton(gamepad, (SDL_GamepadButton)i.id);
        // if (i.debounce.debounceDelayNS > 0){
        //     value = debounceButtonState(id,value);
        // }
        //value = emaUpdate(inputs[id].smoothing, value);
        return value;
    } else if (i.type==2){        
        float data[3];
        int value = SDL_GetGamepadSensorData(gamepad, (SDL_SensorType) i.id, data, 3);        
        if(!value){
           return 0;
        } 
        return data[index];
    }   
    
}


static PyObject* fg_get_button_list(PyObject* self, PyObject* args) {
    PyObject* listObj;

    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &listObj)) {
        return nullptr;
    }

    Py_ssize_t size = PyList_Size(listObj);
    
    PyObject* dict = PyDict_New();
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(listObj, i);  // borrowed reference
        if (!PyLong_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "List elements must be integers");
            return nullptr;
        }
        long value = PyLong_AsLong(item);
        float current = get_button(value);
        PyDict_SetItemString(dict, inputs[value].name.c_str(), PyFloat_FromDouble(current));        
    }
    return dict;
    //Py_RETURN_NONE;
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
static PyObject* fg_set_smoothing_single(PyObject* self, PyObject* args) {
    int ms;
    int id;
    if (!PyArg_ParseTuple(args, "ii", &ms,&id)) {
        return NULL;
    }
    
    if (ms == 0) {
        inputs[id].smoothing.emaAlpha = 0.0; // no smoothing
        inputs[id].smoothing.initialized = false; // reset EMA state
        Py_RETURN_NONE;
    }
    
    // Assume poll rate ~60 Hz (~16 ms per sample).
    // Equivalent N samples = ms / 16.
    // Alpha = 2 / (N + 1)
    double N = (double)ms / 16.0;
    if (N < 1) N = 1;
    inputs[id].smoothing.emaAlpha = 2.0 / (N + 1.0);
    Py_RETURN_NONE;
}
static PyObject* fg_set_debounce_single(PyObject* self, PyObject* args) {
    int ms;
    int id;
    
    if (!PyArg_ParseTuple(args, "ii", &ms,&id)) {
        return NULL;
    }
    debounceDelayNS = (Uint64)ms * 1000000ULL;

     return Py_BuildValue("l", debounceDelayNS);
    //Py_RETURN_NONE;
}



static PyObject* fg_set_smoothing(PyObject* self, PyObject* args) {
    int ms;
    if (!PyArg_ParseTuple(args, "i", &ms)) {
        return NULL;
    }
    
    if (ms == 0) {
        emaAlpha = 0.0; // no smoothing
       for (auto& [key, value] : inputs) {
            value.smoothing.initialized = false;
        }

        Py_RETURN_NONE;
    }
    
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
    debounceDelayNS = (Uint64)ms * 1000000ULL;

    return Py_BuildValue("l", (long)debounceDelayNS / 1000000);
    //Py_RETURN_NONE;
}



// Get axes
static PyObject* fg_get_axes(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "lx", PyFloat_FromDouble(get_button(1000)));
    PyDict_SetItemString(dict, "ly", PyFloat_FromDouble(get_button(1001)));   
    PyDict_SetItemString(dict, "rx", PyFloat_FromDouble(get_button(1002)));
    PyDict_SetItemString(dict, "ry", PyFloat_FromDouble(get_button(1003)));
    PyDict_SetItemString(dict, "lt", PyFloat_FromDouble(get_button(1004)));
    PyDict_SetItemString(dict, "rt", PyFloat_FromDouble(get_button(1005)));
    return dict;    
  
}


static PyObject* fg_get_buttons(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "south", PyLong_FromLong(get_button(0)));
    PyDict_SetItemString(dict, "east", PyLong_FromLong(get_button(1)));
    PyDict_SetItemString(dict, "west", PyLong_FromLong(get_button(2)));
    PyDict_SetItemString(dict, "north", PyLong_FromLong(get_button(3)));
    PyDict_SetItemString(dict, "back", PyLong_FromLong(get_button(4)));
    PyDict_SetItemString(dict, "guide", PyLong_FromLong(get_button(5)));
    PyDict_SetItemString(dict, "start", PyLong_FromLong(get_button(6)));
    PyDict_SetItemString(dict, "lstick", PyLong_FromLong(get_button(7)));
    PyDict_SetItemString(dict, "rstick", PyLong_FromLong(get_button(8)));   
    PyDict_SetItemString(dict, "lshoulder", PyLong_FromLong(get_button(9)));
    PyDict_SetItemString(dict, "rshoulder", PyLong_FromLong(get_button(10)));
    PyDict_SetItemString(dict, "dpad_up", PyLong_FromLong(get_button(11)));
    PyDict_SetItemString(dict, "dpad_down", PyLong_FromLong(get_button(12)));
    PyDict_SetItemString(dict, "dpad_left", PyLong_FromLong(get_button(13)));
    PyDict_SetItemString(dict, "dpad_right", PyLong_FromLong(get_button(14)));
    PyDict_SetItemString(dict, "misc1", PyLong_FromLong(get_button(15)));
    PyDict_SetItemString(dict, "rp1", PyLong_FromLong(get_button(16)));
    PyDict_SetItemString(dict, "lp1", PyLong_FromLong(get_button(17)));
    PyDict_SetItemString(dict, "rp2", PyLong_FromLong(get_button(18)));
    PyDict_SetItemString(dict, "lp2", PyLong_FromLong(get_button(19)));
    PyDict_SetItemString(dict, "touchbutton", PyLong_FromLong(get_button(20)));
    PyDict_SetItemString(dict, "misc2", PyLong_FromLong(get_button(21)));
    PyDict_SetItemString(dict, "misc3", PyLong_FromLong(get_button(22)));
    PyDict_SetItemString(dict, "misc4", PyLong_FromLong(get_button(23)));
    PyDict_SetItemString(dict, "misc5", PyLong_FromLong(get_button(24)));
    PyDict_SetItemString(dict, "misc6", PyLong_FromLong(get_button(25)));
    return dict;
}
static PyObject* fg_get_sensors(PyObject* self, PyObject* args) {
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    SDL_PumpEvents();
    PyObject* dict = PyDict_New();
    PyDict_SetItemString(dict, "accelx", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL+2000,0)));
    PyDict_SetItemString(dict, "accely", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL+2100,1)));
    PyDict_SetItemString(dict, "accelz", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL+2200,2)));
    PyDict_SetItemString(dict, "gyrox", PyLong_FromLong(get_button(SDL_SENSOR_GYRO+2000,0)));
    PyDict_SetItemString(dict, "gyroy", PyLong_FromLong(get_button(SDL_SENSOR_GYRO+2100,1)));
    PyDict_SetItemString(dict, "gyroz", PyLong_FromLong(get_button(SDL_SENSOR_GYRO+2200,2)));

    PyDict_SetItemString(dict, "accelx_l", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_L+2000,0)));
    PyDict_SetItemString(dict, "accely_l", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_L+2100,1)));
    PyDict_SetItemString(dict, "accelz_l", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_L+2200,2)));
    PyDict_SetItemString(dict, "gyrox_l", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_L+2000,0)));
    PyDict_SetItemString(dict, "gyroy_l", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_L+2100,1)));
    PyDict_SetItemString(dict, "gyroz_l", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_L+2200,2)));

    PyDict_SetItemString(dict, "accelx_r", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_R+2000,0)));
    PyDict_SetItemString(dict, "accely_r", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_R+2100,1)));
    PyDict_SetItemString(dict, "accelz_r", PyLong_FromLong(get_button(SDL_SENSOR_ACCEL_R+2200,2)));
    PyDict_SetItemString(dict, "gyrox_r", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_R+2000,0)));
    PyDict_SetItemString(dict, "gyroy_r", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_R+2100,1)));
    PyDict_SetItemString(dict, "gyroz_r", PyLong_FromLong(get_button(SDL_SENSOR_GYRO_R+2200,2)));


    return dict;
}








static PyObject* fg_init(PyObject* self, PyObject* args) {
   if (SDL_Init(SDL_INIT_GAMEPAD | SDL_INIT_JOYSTICK | SDL_INIT_HAPTIC | SDL_INIT_SENSOR ) == 0) {
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
    }
    Py_RETURN_NONE;
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
    {"get_button_list",fg_get_button_list, METH_VARARGS,"Get Specific Button States"},
    {"get_sensors", fg_get_sensors, METH_NOARGS, "Get sensor data"},
    {"set_smoothing", fg_set_smoothing, METH_VARARGS, "Set axis smoothing in ms"},


    {"set_debounce", fg_set_debounce, METH_VARARGS, "Set button debounce window (ms)"},
    {"rumble", run_haptic, METH_VARARGS,"run haptic"},
    {"set_smoothing_single", fg_set_smoothing_single, METH_VARARGS, "Set axis smoothing in ms"},
    {"set_debounce_single", fg_set_debounce_single, METH_VARARGS, "Set button debounce window (ms)"},
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
    inputs[SDL_GAMEPAD_AXIS_LEFTX + 1000] = {SDL_GAMEPAD_AXIS_LEFTX,1,"lx"};
    inputs[SDL_GAMEPAD_AXIS_LEFTY + 1000] = {SDL_GAMEPAD_AXIS_LEFTY,1,"ly"};
    inputs[SDL_GAMEPAD_AXIS_RIGHTX + 1000] = {SDL_GAMEPAD_AXIS_RIGHTX,1,"rx"};
    inputs[SDL_GAMEPAD_AXIS_RIGHTY + 1000] = {SDL_GAMEPAD_AXIS_RIGHTY,1,"ry"};
    inputs[SDL_GAMEPAD_AXIS_LEFT_TRIGGER + 1000] = {SDL_GAMEPAD_AXIS_LEFT_TRIGGER,1,"lt"};
    inputs[SDL_GAMEPAD_AXIS_RIGHT_TRIGGER + 1000] = {SDL_GAMEPAD_AXIS_RIGHT_TRIGGER,1,"rt"};

    inputs[SDL_GAMEPAD_BUTTON_SOUTH] = {SDL_GAMEPAD_BUTTON_SOUTH,0,"south"};
    inputs[SDL_GAMEPAD_BUTTON_EAST] = {SDL_GAMEPAD_BUTTON_EAST,0,"east"};
    inputs[SDL_GAMEPAD_BUTTON_WEST] = {SDL_GAMEPAD_BUTTON_WEST,0,"west"};
    inputs[SDL_GAMEPAD_BUTTON_NORTH] = {SDL_GAMEPAD_BUTTON_NORTH,0,"north"};

    inputs[SDL_GAMEPAD_BUTTON_BACK] = {SDL_GAMEPAD_BUTTON_BACK,0,"back"};
    inputs[SDL_GAMEPAD_BUTTON_GUIDE] = {SDL_GAMEPAD_BUTTON_GUIDE,0,"guide"};
    inputs[SDL_GAMEPAD_BUTTON_START] = {SDL_GAMEPAD_BUTTON_START,0,"start"};
    inputs[SDL_GAMEPAD_BUTTON_LEFT_STICK] = {SDL_GAMEPAD_BUTTON_LEFT_STICK,0,"lstick"};
    inputs[SDL_GAMEPAD_BUTTON_RIGHT_STICK] = {SDL_GAMEPAD_BUTTON_RIGHT_STICK,0,"rstick"};
    inputs[SDL_GAMEPAD_BUTTON_LEFT_SHOULDER] = {SDL_GAMEPAD_BUTTON_LEFT_SHOULDER,0,"lshoulder"};
    inputs[SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER] = {SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER,0,"rshoulder"};
    inputs[SDL_GAMEPAD_BUTTON_DPAD_UP] = {SDL_GAMEPAD_BUTTON_DPAD_UP,0,"dpad_up"};
    inputs[SDL_GAMEPAD_BUTTON_DPAD_DOWN] = {SDL_GAMEPAD_BUTTON_DPAD_DOWN,0,"dpad_down"};
    inputs[SDL_GAMEPAD_BUTTON_DPAD_LEFT] = {SDL_GAMEPAD_BUTTON_DPAD_LEFT,0,"dpad_left"};
    inputs[SDL_GAMEPAD_BUTTON_DPAD_RIGHT] = {SDL_GAMEPAD_BUTTON_DPAD_RIGHT,0,"dpad_right"};
    inputs[SDL_GAMEPAD_BUTTON_MISC1] = {SDL_GAMEPAD_BUTTON_MISC1,0,"misc1"};
    inputs[SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1] = {SDL_GAMEPAD_BUTTON_RIGHT_PADDLE1,0,"rp1"};
    inputs[SDL_GAMEPAD_BUTTON_LEFT_PADDLE1] = {SDL_GAMEPAD_BUTTON_LEFT_PADDLE1,0,"lp1"};
    inputs[SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2] = {SDL_GAMEPAD_BUTTON_RIGHT_PADDLE2,0,"rp2"};
    inputs[SDL_GAMEPAD_BUTTON_LEFT_PADDLE2] = {SDL_GAMEPAD_BUTTON_LEFT_PADDLE2,0,"lp2"};
    inputs[SDL_GAMEPAD_BUTTON_TOUCHPAD] = {SDL_GAMEPAD_BUTTON_TOUCHPAD,0,"touchpad"};
    inputs[SDL_GAMEPAD_BUTTON_MISC2] = {SDL_GAMEPAD_BUTTON_MISC2,0,"misc2"};
    inputs[SDL_GAMEPAD_BUTTON_MISC3] = {SDL_GAMEPAD_BUTTON_MISC3,0,"misc3"};
    inputs[SDL_GAMEPAD_BUTTON_MISC4] = {SDL_GAMEPAD_BUTTON_MISC4,0,"misc4"};   
    inputs[SDL_GAMEPAD_BUTTON_MISC5] = {SDL_GAMEPAD_BUTTON_MISC5,0,"misc5"};
    inputs[SDL_GAMEPAD_BUTTON_MISC6] = {SDL_GAMEPAD_BUTTON_MISC6,0,"misc6"};

    inputs[SDL_SENSOR_ACCEL+2000] = {SDL_SENSOR_ACCEL,2,"accelx",0};
    inputs[SDL_SENSOR_ACCEL+2100] = {SDL_SENSOR_ACCEL,2,"accely",1};
    inputs[SDL_SENSOR_ACCEL+2200] = {SDL_SENSOR_ACCEL,2,"accelz",2};
    inputs[SDL_SENSOR_GYRO+2000] = {SDL_SENSOR_GYRO,2,"gyrox",0};
    inputs[SDL_SENSOR_GYRO+2100] = {SDL_SENSOR_GYRO,2,"gyroy",1};
    inputs[SDL_SENSOR_GYRO+2200] = {SDL_SENSOR_GYRO,2,"gyroz",2};

    inputs[SDL_SENSOR_ACCEL_L+2000] = {SDL_SENSOR_ACCEL_L,2,"accelx_l",0};
    inputs[SDL_SENSOR_ACCEL_L+2100] = {SDL_SENSOR_ACCEL_L,2,"accely_l",1};
    inputs[SDL_SENSOR_ACCEL_L+2200] = {SDL_SENSOR_ACCEL_L,2,"accelz_l",2};
    inputs[SDL_SENSOR_GYRO_L+2000] = {SDL_SENSOR_GYRO_L,2,"gyrox_l",0};
    inputs[SDL_SENSOR_GYRO_L+2100] = {SDL_SENSOR_GYRO_L,2,"gyroy_l",1};
    inputs[SDL_SENSOR_GYRO_L+2200] = {SDL_SENSOR_GYRO_L,2,"gyroz_l",2};

    inputs[SDL_SENSOR_ACCEL_R+2000] = {SDL_SENSOR_ACCEL_R,2,"accelx_r",0};
    inputs[SDL_SENSOR_ACCEL_R+2100] = {SDL_SENSOR_ACCEL_R,2,"accely_r",1};
    inputs[SDL_SENSOR_ACCEL_R+2200] = {SDL_SENSOR_ACCEL_R,2,"accelz_r",2};
    inputs[SDL_SENSOR_GYRO_R+2000] = {SDL_SENSOR_GYRO_R,2,"gyrox_r",0};
    inputs[SDL_SENSOR_GYRO_R+2100] = {SDL_SENSOR_GYRO_R,2,"gyroy_r",1};
    inputs[SDL_SENSOR_GYRO_R+2200] = {SDL_SENSOR_GYRO_R,2,"gyroz_r",2};

    return PyModule_Create(&fastgamepadmodule);
}
