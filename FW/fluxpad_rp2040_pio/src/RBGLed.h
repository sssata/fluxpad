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

enum class RGBState {
    OFF,
    DISCONNECTED,
    CONNECTED,
};

typedef struct {
    RGBState connectedState;
} RGBSettings;

class RGBLeds {

  private:
    // uint8_t data_pin;
    RGBState state;

    void rainbow() {
        // FastLED's built-in rainbow generator
        uint8_t thisHue = beat8(20); // A simple rainbow march.
        fill_rainbow(leds, NUM_LEDS, thisHue, 255 / 10);
    }

    void addGlitter(fract8 chanceOfGlitter) {
        if (random8() < chanceOfGlitter) {
            leds[random16(NUM_LEDS)] += CRGB::White;
        }
    }

    void rainbowWithGlitter() {
        // built-in FastLED rainbow, plus some random sparkly glitter
        rainbow();
        // addGlitter(80);
    }

  public:
    RGBLeds() : state(RGBState::OFF){};

    void setup() {
        FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS); // GRB ordering is assumed
    }

    void loop_service() {
        switch (state) {
        case RGBState::OFF:
            // Nothing
            break;
        case RGBState::CONNECTED:
            connected_state();
            break;
        case RGBState::DISCONNECTED:
            // Nothing
            break;
        }
    }

    void set_state(RGBState new_state) {
        switch (new_state) {
        case RGBState::OFF:
            if (state != RGBState::OFF) {
                state = RGBState::OFF;
                turn_off();
            }
            break;
        case RGBState::CONNECTED:
            if (state != RGBState::CONNECTED) {
                state = RGBState::CONNECTED;
            }
            break;
        case RGBState::DISCONNECTED:
            if (state != RGBState::DISCONNECTED) {
                state = RGBState::DISCONNECTED;
                show_disconnected_state();
            }
            break;
        }
    }

    void connected_state() {
        // leds[0] = CRGB::Red;
        // leds[1] = CRGB::Green;
        // leds[2] = CRGB::Blue;
        // rainbowWithGlitter();
        rainbow();

        FastLED.show(100);
    }

    void show_disconnected_state() {
        for (auto &led : leds) {
            led = CRGB::Crimson;
        }
        FastLED.show(20);
    }

    void turn_off() { FastLED.showColor(CRGB::Black); }
};
