#pragma once

#include "Adafruit_TinyUSB.h"
#include "USBCommon.hpp"
#include <Arduino.h>

#define REPORT_MAX_SIZE 64
#define CONSUMER_REPORT_SIZE 3

/**
 * @brief Handles HID Consumer device logic
 *
 */
class HIDKeyboard {
  private:
    // uint16_t pressed_consumer_key;
    uint8_t pressed_keys[6];

  public:
    HIDKeyboard() { memset(pressed_keys, 0, sizeof(pressed_keys)); }

    /**
     * @brief Press the given key
     *
     * @param key
     */
    void add_key(uint8_t key) {
        for (size_t i = 0; i < sizeof(pressed_keys); i++) {
            // If key already exists in pressed keys, just return
            if (pressed_keys[i] == key) {
                return;
            }

            // If empty slot found, put key in
            if (pressed_keys[i] == 0) {
                pressed_keys[i] = key;
                return;
            }
        }

        // If we're here, no empty slots were found. Replace first one instead (FIFO)
        pressed_keys[0];
    }

    /**
     * @brief Release the given key
     *
     * @param key keycode of key to release
     * @return true if successfully released
     * @return false if key wasn't pressed in the first place
     */
    bool remove_key(uint8_t key) {
        for (size_t i = 0; i < sizeof(pressed_keys); i++) {
            // Look for key in existing array
            if (pressed_keys[i] == key) {
                // If the key to remove is the last key, just set it to zero
                if (i == sizeof(pressed_keys) - 1) {
                    pressed_keys[i] = 0;
                }
                // Otherwise shift array elements over to fill in removed element
                else {
                    memmove(pressed_keys + i, pressed_keys + i + 1, sizeof(pressed_keys) - i - 1);
                }
                return true;
            }
        }
        return false;
    }

    /**
     * @brief Should be run once in main loop if usb_hid device is ready
     *
     */
    bool hid_keyboard_service(Adafruit_USBD_HID &usb_hid, const uint8_t report_id) {
        bool send_report_ok = false;
        if (usb_hid_wait_until_ready(usb_hid, USB_HID_WAIT_TIME_US) &&
            usb_hid.keyboardReport(report_id, 0, pressed_keys)) {
            return true;
        }
        return false;
        // Serial.printf("hello %d %d\n", , pressed_consumer_key);
    }

    /**
     * @brief Get whether key is currently pressed or released
     *
     * @return true
     * @return false
     */
    bool isPressed() const {
        for (const auto &key : pressed_keys) {
            if (key != 0) {
                return true;
            }
        }
        return false;
    }
};
