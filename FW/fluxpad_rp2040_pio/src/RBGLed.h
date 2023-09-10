#pragma once

#include <Arduino.h>
#include <FastLED.h>

#define CHIPSET WS2812B
#define COLOR_ORDER GRB
#define NUM_LEDS 3
// #define DATA_PIN 11

// // #define NUM_LEDS 3
// // #define DATA_PIN 3
constexpr uint8_t DATA_PIN = 11u;

CRGB leds[NUM_LEDS];

enum class RGBMode { OFF, STATIC, RAINBOW };

typedef struct {
    RGBMode mode;
    uint32_t color_1;
    uint32_t color_2;
    uint32_t color_3;
    uint8_t brightness;
    float speed_bpm;
} RGBSettings;

class RGBLeds {

  private:
    // uint8_t data_pin;
    RGBSettings &settings;

  public:
    RGBLeds(RGBSettings &settings) : settings(settings){};

    void setup() {
        FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS); // GRB ordering is assumed
        new_mode();
    }

    void loop_service() {
        switch (settings.mode) {
        case RGBMode::OFF:
            // Nothing
            break;
        case RGBMode::STATIC:
            // Nothing
            break;
        case RGBMode::RAINBOW:
            rainbow_mode();
            break;
        }
    }

    void assign_settings(RGBSettings &new_settings) {
        settings = new_settings;
        new_mode();
    }

    void new_mode() {
        Serial.printf("newmode");
        switch (settings.mode) {
        case RGBMode::OFF:
            turn_off();
            break;
        case RGBMode::STATIC:
            static_mode();
            break;
        case RGBMode::RAINBOW:
            settings.mode = RGBMode::RAINBOW;
            break;
        }
    }

    void rainbow_mode() {
        // FastLED's built-in rainbow generator
        uint8_t thisHue = beat8(static_cast<accum88>(settings.speed_bpm)); // A simple rainbow march.
        fill_rainbow(leds, NUM_LEDS, thisHue, 255 / 10);

        FastLED.show(settings.brightness);
    }

    void static_mode() {
        Serial.print("static");
        leds[0].setColorCode(settings.color_1);
        leds[1].setColorCode(settings.color_2);
        leds[2].setColorCode(settings.color_3);
        FastLED.show(settings.brightness);
    }

    void show_disconnected_state() {
        for (auto &led : leds) {
            led = CRGB::Red;
        }
        FastLED.show(20);
    }

    void turn_off() { FastLED.showColor(CRGB::Black); }
};
