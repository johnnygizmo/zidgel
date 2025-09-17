#include <Python.h>
#include <SDL3\SDL.h>
#include <map>
#include <iostream>
#include <cstdio>
#include <unordered_map>
using namespace std;


static SDL_Gamepad* gamepad = nullptr;
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





static PyObject* get_button(PyObject* self, PyObject* args) {
    int type;
    int id;
    if (!PyArg_ParseTuple(args, "ii", &type,&id)) {
        return NULL;
    }
    
    if(type == 1){
        float value =  SDL_GetGamepadAxis(gamepad, (SDL_GamepadAxis)id) / 32767.0f;
        return PyLong_FromLong(value);
    } else if (type==0) {
        int value = SDL_GetGamepadButton(gamepad, (SDL_GamepadButton)id);
        return PyLong_FromLong(value);
    } else if (type==2){        
        float data[3];
        int value = SDL_GetGamepadSensorData(gamepad, (SDL_SensorType) id, data, 3);        
        if(!value){
           Py_RETURN_NONE;
        } 
        
        
        // Create a new tuple of size 3
        PyObject* py_tuple = PyTuple_New(3);
        if (!py_tuple) return NULL;

        for (int i = 0; i < 3; i++) {
            // Convert each C int into a Python integer
            PyObject* py_int = PyLong_FromLong(data[i]);
            if (!py_int) {
                Py_DECREF(py_tuple);
                return NULL;
            }
            // Set item steals reference to py_int
            PyTuple_SET_ITEM(py_tuple, i, py_int);
        }

        return py_tuple;  


    }   
    
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
    {"get_button",get_button, METH_VARARGS,"Get Specific Button States"},
    {"rumble", run_haptic, METH_VARARGS,"run haptic"},
    {"quit", fg_quit, METH_NOARGS, "Close gamepad and quit SDL"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef fastgamepadmodule = {
    PyModuleDef_HEAD_INIT,
    "padtest",
    "Fast gamepad polling via SDL3",
    -1,
    FastGamepadMethods
};

PyMODINIT_FUNC PyInit_padtest(void) {
    return PyModule_Create(&fastgamepadmodule);
}
