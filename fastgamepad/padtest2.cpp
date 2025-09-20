#include <SDL3/SDL.h>
#include <iostream>
#include <iomanip>

int main(int argc, char* argv[]) {
    // Initialize SDL with gamepad subsystem
    if (SDL_Init(SDL_INIT_GAMEPAD) == 0) {
        std::cerr << "SDL initialization failed: " << SDL_GetError() << std::endl;
        return -1;
    }

    int num_gamepads = 0;
    SDL_JoystickID* gamepad_ids = SDL_GetGamepads(&num_gamepads);
    
    if (num_gamepads == 0) {
        std::cerr << "No gamepads connected!" << std::endl;
        SDL_Quit();
        return -1;
    }

    std::cout << "Found " << num_gamepads << " gamepad(s)" << std::endl;

    SDL_Gamepad* gamepad = SDL_OpenGamepad(gamepad_ids[0]);
    if (!gamepad) {
        std::cerr << "Failed to open gamepad: " << SDL_GetError() << std::endl;
        SDL_free(gamepad_ids);
        SDL_Quit();
        return -1;
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
        return -1;
    }

    // Enable the accelerometer sensor
    if (SDL_SetGamepadSensorEnabled(gamepad, SDL_SENSOR_ACCEL, true) == 0) {
        std::cerr << "Failed to enable accelerometer: " << SDL_GetError() << std::endl;
        SDL_CloseGamepad(gamepad);
        SDL_free(gamepad_ids);
        SDL_Quit();
        return -1;
    }

    std::cout << "Accelerometer enabled. Press Ctrl+C to exit." << std::endl;
    std::cout << "Accelerometer data (X, Y, Z in m/s²):" << std::endl;

    // Main execution loop
    SDL_Event event;
    bool running = true;
    
    while (running) {
        // Process SDL events
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_EVENT_QUIT:
                    running = false;
                    break;
                    

            }
        }

        // Read accelerometer data
        float accel_data[3]; // X, Y, Z values
        if (SDL_GetGamepadSensorData(gamepad, SDL_SENSOR_ACCEL, accel_data, 3) == 1) {
            // Clear the line and print new accelerometer values

        }
        float gyro_data[3]; // X, Y, Z values
        if (SDL_GetGamepadSensorData(gamepad, SDL_SENSOR_GYRO, gyro_data, 3) == 1) {
            // Clear the line and print new gyroscope values

        }

            std::cout << "\rAccel - X: " << std::fixed << std::setprecision(3) 
                      << std::setw(8) << accel_data[0] 
                      << " Y: " << std::setw(8) << accel_data[1] 
                      << " Z: " << std::setw(8) << accel_data[2] 
                      << " m/s²   " 
                      << "\rGyro - X: " 
                      << std::setw(8)  << gyro_data[0] 
                      << " Y: " << std::setw(8) << gyro_data[1] 
                      << " Z: " << std::setw(8) << gyro_data[2] 
                      << " m/s²" << std::endl;

        // Small delay to avoid overwhelming the console
        SDL_Delay(50); // Update every 50ms (20 Hz)
    }

    std::cout << std::endl << "Cleaning up..." << std::endl;

    // Cleanup
    SDL_CloseGamepad(gamepad);
    SDL_free(gamepad_ids);
    SDL_Quit();

    return 0;
}