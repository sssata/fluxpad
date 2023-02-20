#pragma once

#include <stdint.h>

typedef struct {
    uint32_t debounce_press_ms;
    uint32_t debounce_release_ms;
} DigitalSwitchSettings_t;

class DigitalSwitch {
  public:
    uint32_t pin;
    uint32_t id;

    uint32_t last_pressed_time_ms;
    uint32_t last_release_time_ms;
    unsigned long last_toggle_time_ms;
    bool curr_state_unfiltered;
    bool prev_state_unfiltered;
    bool curr_state;
    bool is_pressed;
    DigitalSwitchSettings_t settings;

    DigitalSwitch(uint32_t _pin, uint32_t _id);

    void setup();

    void applySettings(DigitalSwitchSettings_t *settings);

    void mainLoopService();
};