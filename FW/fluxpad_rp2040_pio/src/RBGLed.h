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

class RGBLeds {

  private:
    // uint8_t data_pin;
    bool is_off = false;

    uint8_t gHue = 0; // rotating "base color" used by many of the patterns

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
    RGBLeds(){};

    void setup() {
        FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS); // GRB ordering is assumed
    }

    void show_lights() {
        // leds[0] = CRGB::Red;
        // leds[1] = CRGB::Green;
        // leds[2] = CRGB::Blue;
        rainbowWithGlitter();

        FastLED.show(100);
    }

    void show_disconnected_lights() {
        for (auto &led : leds) {
            led = CRGB::Crimson;
        }
        FastLED.show(20);
    }

    void turn_off() { FastLED.showColor(CRGB::Black); }
};
