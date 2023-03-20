#pragma once

#include <stdint.h>

typedef struct {
    uint32_t debounce_press_ms;
    uint32_t debounce_release_ms;
} DigitalSwitchSettings_t;

class DigitalSwitch {
  public:
    const uint32_t pin;
    const uint32_t id;

    uint32_t last_pressed_time_ms;
    uint32_t last_release_time_ms;
    unsigned long last_toggle_time_ms;
    bool is_pressed;
    DigitalSwitchSettings_t settings;

    DigitalSwitch(uint32_t pin, uint32_t id) : pin(pin), id(id) {}

    void setup() {
        is_pressed = false;
        pinMode(pin, INPUT_PULLUP);
        last_pressed_time_ms = millis();
        last_release_time_ms = millis();
    }

    void applySettings(DigitalSwitchSettings_t *_settings) {
        settings = *_settings;
        is_pressed = false;
    }

    void mainLoopService() {
        bool curr_state = !digitalRead(pin);
        unsigned long current_time_ms = millis();

        switch (is_pressed) {
        case true:
            if (curr_state) {
                last_pressed_time_ms = current_time_ms;
            }

            if (current_time_ms - last_pressed_time_ms > settings.debounce_release_ms) {
                is_pressed = false;
            }
            break;
        case false:
            if (!curr_state) {
                last_release_time_ms = current_time_ms;
            }

            if (current_time_ms - last_release_time_ms > settings.debounce_press_ms) {
                is_pressed = true;
            }
        default:
            // Nothing
            break;
        }
    }
};