
#pragma once

#include <stdint.h>

#define FLASH_DURATION_US 50 * 1000
#define DUTY_CYCLE_ON 255
#define DUTY_CYCLE_OFF 0
#define UPDATE_PERIOD_US 20 * 1000
#define FADE_MIN_DUTY_CYCLE 10

enum LightingMode {
    LIGHTING_MODE_OFF,
    LIGHTING_MODE_STATIC,
    LIGHTING_MODE_FADE,
    LIGHTING_MODE_FLASH
};

typedef struct {
    LightingMode mode;
    uint32_t fade_half_life_us;
    uint32_t flash_duration_us;
    uint8_t static_duty_cycle;
} KeyLightingSettings_t;

class KeyLighting {
  public:
    const uint32_t pin;
    KeyLightingSettings_t settings;
    bool pressed_prev;
    float fade_factor;
    uint8_t last_duty_cycle;
    uint32_t last_fade_time_us;
    uint8_t last_pressed_time_us;

    KeyLighting(uint32_t pin) : pin(pin){};

    void setup() {
        pinMode(pin, OUTPUT);
        analogWriteResolution(8);
    }

    void applySettings(KeyLightingSettings_t *_settings) {
        settings = *_settings;
        fade_factor = pow(
            float(UPDATE_PERIOD_US) / float(settings.fade_half_life_us), 0.5);
    }

    void main_task(uint32_t time_us, bool pressed) {
        switch (settings.mode) {
        case LIGHTING_MODE_OFF:
            set_duty_cycle(DUTY_CYCLE_OFF);
            break;
        case LIGHTING_MODE_STATIC:
            break;
        case LIGHTING_MODE_FADE:
            switch (pressed) {
            case true:
                // Turn on the led
                set_duty_cycle(DUTY_CYCLE_ON);
                break;
            case false:
                // Fade the led
                if (time_us - last_fade_time_us > UPDATE_PERIOD_US) {
                    last_fade_time_us = time_us;
                    uint8_t duty_cycle =
                        max(last_duty_cycle * fade_factor, FADE_MIN_DUTY_CYCLE);
                    set_duty_cycle(duty_cycle);
                }
                break;
            default:
                break;
            }
            break;
        case LIGHTING_MODE_FLASH:
            if (!pressed_prev && pressed) {
                last_pressed_time_us = time_us;
            }
            pressed_prev = pressed;

            if (time_us - last_pressed_time_us > settings.flash_duration_us) {
                set_duty_cycle(DUTY_CYCLE_ON);
            } else {
                set_duty_cycle(DUTY_CYCLE_OFF);
            }

            break;
        default:
            break;
        }
    }

  private:
    bool set_duty_cycle(uint8_t duty_cycle) {
        if (last_duty_cycle != duty_cycle) {
            analogWrite(pin, duty_cycle);
            return true;
        }
        return false;
    }
};
