#include <Python.h>
#include <SDL3\SDL.h>
#include <map>
#include <iostream>
#include <cstdio>
#include <unordered_map>
#include <iomanip>
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
       //cout << "Sensor data " << id << " : " << data[0] << ", " << data[1] << ", " << data[2] << endl;
        if(!value){
           Py_RETURN_NONE;
        } 
        
        
        // Create a new tuple of size 3
        PyObject* py_tuple = PyTuple_New(3);
        if (!py_tuple) return NULL;

        for (int i = 0; i < 3; i++) {
            // Convert each C int into a Python integer
            PyObject* py_float = PyFloat_FromDouble(data[i]+.1f);
            if (!py_float) {
                Py_DECREF(py_tuple);
                return NULL;
            }
            // Set item steals reference to py_int
            PyTuple_SET_ITEM(py_tuple, i, py_float);
        }

        return py_tuple;  


    }   
    
}

static PyObject* set_led(PyObject* self, PyObject* args) {
    int r;
    int g;
    int b;
    if (!PyArg_ParseTuple(args, "iii", &r,&g,&b)) {
        return NULL;
    }

    cout << "Setting LED to: " << r << ", " << g << ", " << b << endl;
    bool result = SDL_SetGamepadLED(gamepad, r, g, b);
    if (!result) {
        return PyErr_Format(PyExc_RuntimeError, "Failed to set LED color: %s", SDL_GetError());
    }

    Py_RETURN_NONE;
}


static PyObject* get_info(PyObject* self, PyObject* args) {
    cout << "Getting info..." << endl;
    if (!gamepad) {
        return PyErr_Format(PyExc_RuntimeError, "Gamepad not initialized");
    }
    //SDL_PumpEvents();
    int vendor = SDL_GetGamepadVendor(gamepad);
    int product = SDL_GetGamepadProduct(gamepad);


    cout << "Vendor ID: " << hex << vendor << endl;
    cout << "Product ID: " << hex << product << endl;

    
    int num_touchpads = SDL_GetNumGamepadTouchpads(gamepad);
    cout << "Number of touchpads: " << num_touchpads << endl;
    for (int t = 0; t < num_touchpads; t++) {
        int nfingers = SDL_GetNumGamepadTouchpadFingers(gamepad, t);
        cout << "Touchpad " << t << " supports " << nfingers << " fingers." << endl;
    }

    if(SDL_GamepadHasSensor(gamepad, SDL_SENSOR_ACCEL) ) {
        cout << "Gamepad has Accelerometer." << endl;
    } else {
        cout << "Gamepad has NO Accelerometer." << endl;
    }
    if(SDL_GamepadHasSensor(gamepad, SDL_SENSOR_GYRO) ) {
        cout << "Gamepad has gyro." << endl;
    } else {
        cout << "Gamepad has NO gyro." << endl;
    }

    if(SDL_GamepadEventsEnabled()) {
        cout << "Gamepad events are enabled." << endl;
    } else {
        cout << "Gamepad events are NOT enabled." << endl;
    }
    cout << "Rate: "<< SDL_GetGamepadSensorDataRate( gamepad, (SDL_SensorType)1) << endl;  
    
    SDL_Event event;                                    
    while(SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_EVENT_QUIT:
                    break;
                    

            }        // Just drain the event queue
    }

    float accel_data[3]; // X, Y, Z values
    if (SDL_GetGamepadSensorData(gamepad, SDL_SENSOR_ACCEL, accel_data, 3) == 1) {
        // Clear the line and print new accelerometer values
        std::cout << "\rAccel - X: " << std::fixed << std::setprecision(6) 
                    << std::setw(8) << accel_data[0] 
                    << " Y: " << std::setw(8) << accel_data[1] 
                    << " Z: " << std::setw(8) << accel_data[2] 
                    << " m/s²" << std::endl;
    }
    float gyro_data[3]; // X, Y, Z values
    if (SDL_GetGamepadSensorData(gamepad, SDL_SENSOR_GYRO, gyro_data, 3) == 1) {
        // Clear the line and print new gyroscope values
        std::cout << "\rGyro - X: " << std::fixed << std::setprecision(6) 
                    << std::setw(8) << gyro_data[0] 
                    << " Y: " << std::setw(8) << gyro_data[1] 
                    << " Z: " << std::setw(8) << gyro_data[2] 
                    << " m/s²" << std::endl;
    }

    
    Py_RETURN_NONE;
}

static PyObject* get_touchpad(PyObject* self, PyObject* args) {
    int touchpad;
    int finger;

    if (!PyArg_ParseTuple(args, "ii", &touchpad, &finger)) {
        return NULL;
    }

    // Make sure SDL updates device state
    
    int num_touchpads = SDL_GetNumGamepadTouchpads(gamepad);
    cout << "Number of touchpads: " << num_touchpads << endl;

    for (int t = 0; t < num_touchpads; t++) {
        int nfingers = SDL_GetNumGamepadTouchpadFingers(gamepad, t);
        cout << "Touchpad " << t << " supports " << nfingers << " fingers." << endl;

        for (int i = 0; i < nfingers; i++) {
            bool down;
            float x, y, pressure;
            bool ok = SDL_GetGamepadTouchpadFinger(gamepad, t, i, &down, &x, &y, &pressure);

            cout << "  finger " << i
                 << " ok=" << (ok ? "true" : "false")
                 << " down=" << (down ? "1" : "0")
                 << " x=" << x
                 << " y=" << y
                 << " pressure=" << pressure
                 << endl;
        }
    }
    Py_RETURN_NONE;
}



static PyObject* fg_init(PyObject* self, PyObject* args) {
    if (SDL_Init(SDL_INIT_GAMEPAD) == 0) {
        std::cerr << "SDL initialization failed: " << SDL_GetError() << std::endl;
        return PyErr_Format(PyExc_RuntimeError, "SDL initialization failed: %s", SDL_GetError());
    }

    int num_gamepads = 0;
    SDL_JoystickID* gamepad_ids = SDL_GetGamepads(&num_gamepads);
    
    if (num_gamepads == 0) {
        std::cerr << "No gamepads connected!" << std::endl;        
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "No gamepads connected!")  ;
    }

    std::cout << "Found " << num_gamepads << " gamepad(s)" << std::endl;
    gamepad = SDL_OpenGamepad(gamepad_ids[0]);
    if (!gamepad) {
        std::cerr << "Failed to open gamepad: " << SDL_GetError() << std::endl;
        SDL_free(gamepad_ids);
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "Failed to open gamepad: %s", SDL_GetError());
    }

    // Get gamepad name
    const char* name = SDL_GetGamepadName(gamepad);
    std::cout << "Opened gamepad: " << (name ? name : "Unknown") << std::endl;

    // Check if the gamepad has a sensor (accelerometer)
    if (!SDL_GamepadHasSensor(gamepad, SDL_SENSOR_ACCEL)) {
        std::cerr << "Gamepad does not have an accelerometer!" << std::endl;
        SDL_CloseGamepad(gamepad);
        SDL_free(gamepad_ids);
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "Gamepad does not have an accelerometer!");
    }

    if (SDL_SetGamepadSensorEnabled(gamepad, SDL_SENSOR_ACCEL, true) == 0) {
        std::cerr << "Failed to enable accelerometer: " << SDL_GetError() << std::endl;
        SDL_CloseGamepad(gamepad);
        SDL_free(gamepad_ids);
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "Failed to enable accelerometer: %s", SDL_GetError());
    }    

    if (SDL_SetGamepadSensorEnabled(gamepad, SDL_SENSOR_GYRO, true) == 0) {
        std::cerr << "Failed to enable gyroscope: " << SDL_GetError() << std::endl;
        SDL_CloseGamepad(gamepad);
        SDL_free(gamepad_ids);
        SDL_Quit();
        return PyErr_Format(PyExc_RuntimeError, "Failed to enable gyroscope: %s", SDL_GetError());
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
    {"rumble", run_haptic, METH_VARARGS,"run haptic"},
    {"set_led", set_led, METH_VARARGS,"set led"},    
    {"get_info", get_info, METH_NOARGS,"get info"},
    {"get_touchpad", get_touchpad, METH_VARARGS,"get touchpad state"},
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
