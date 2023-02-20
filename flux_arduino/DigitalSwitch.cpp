
#include "DigitalSwitch.h"
#include "Arduino.h"

DigitalSwitch::DigitalSwitch(uint32_t _pin, uint32_t _id) {
    last_pressed_time_ms = 0UL;
    last_release_time_ms = 0UL;
    curr_state = false;
    curr_state_unfiltered = false;
    prev_state_unfiltered = false;
    pin = _pin;
    id = _id;
}

void DigitalSwitch::setup() {
    pinMode(pin, INPUT_PULLUP);
    curr_state_unfiltered = digitalRead(pin);
    prev_state_unfiltered = curr_state_unfiltered;
    curr_state = curr_state_unfiltered;
}

void DigitalSwitch::applySettings(DigitalSwitchSettings_t *_settings) {
    settings = *_settings;
    is_pressed = false;
}

void DigitalSwitch::mainLoopService() {
    prev_state_unfiltered = curr_state_unfiltered;
    curr_state_unfiltered = !digitalRead(pin);
    curr_state = digitalRead(pin);
    unsigned long current_time_ms = millis();

    switch (is_pressed) {
    case true:
        if (curr_state) {
            last_pressed_time_ms = current_time_ms;
        }

        if (current_time_ms - last_pressed_time_ms >
            settings.debounce_release_ms) {
            is_pressed = false;
        }
        break;
    case false:
        if (!curr_state) {
            last_release_time_ms = current_time_ms;
        }

        if (current_time_ms - last_release_time_ms >
            settings.debounce_press_ms) {
            is_pressed = false;
        }
    default:
        // Nothing
        break;
    }
}