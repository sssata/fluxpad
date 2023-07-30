#include <Arduino.h>

#include "Adafruit_TinyUSB.h"

// Report ID
enum {
    RID_KEYBOARD = 1,
    RID_MOUSE,
    RID_CONSUMER_CONTROL, // Media, volume etc ..
};

uint8_t pressed_keys[6];

uint16_t pressed_consumer_key;
bool consumer_key_pressed;

uint8_t pressed_mouse_buttons;

// HID report descriptor using TinyUSB's template
uint8_t const desc_hid_report[] = {TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(RID_KEYBOARD)),
                                   TUD_HID_REPORT_DESC_MOUSE(HID_REPORT_ID(RID_MOUSE)),
                                   TUD_HID_REPORT_DESC_CONSUMER(HID_REPORT_ID(RID_CONSUMER_CONTROL))};

Adafruit_USBD_HID usb_hid(desc_hid_report, sizeof(desc_hid_report), HID_ITF_PROTOCOL_KEYBOARD, 1, false);

void usb_service_setup() {
    usb_hid.begin();
    pinMode(5, OUTPUT_12MA);

    // setBootProtocol(1);  // Boot protocol keyboard
}

/**
 * @brief Service that handles USB remote wakeup functionality
 * Should be called once every loop
 *
 */
void wakeup_service() {
    if (TinyUSBDevice.suspended()) {
        bool shouldWakeup;

        // Wake up if any button is pressed
        for (const auto &i : pressed_keys) {
            if (i != 0) {
                shouldWakeup = true;
                break;
            }
        }
        if (pressed_mouse_buttons > 0) {
            shouldWakeup = true;
        }
        if (pressed_consumer_key != 0) {
            shouldWakeup = true;
        }
        if (shouldWakeup) {
            TinyUSBDevice.remoteWakeup();
        }
    }
}

/**
 * @brief Service that handles all USB HID Device comms. Should be run every loop
 *
 */
void usb_service() {
    if (usb_hid.ready()) {
        digitalWrite(5, 1);
        usb_hid.keyboardReport(RID_KEYBOARD, 0, pressed_keys);
    } else {
        digitalWrite(5, 0);
    }

    // usb_hid.sendReport();
    // Remote wakeup
    // if (TinyUSBDevice.suspended() &&) {
    //     // Wake up host if we are in suspend mode
    //     // and REMOTE_WAKEUP feature is enabled by host
    //     TinyUSBDevice.remoteWakeup();
    // }

    wakeup_service();
}

/**
 * @brief Press the given keyboard keycode
 *
 * @param key
 */
void press_and_release_consumer(uint16_t key) {
    // usb_hid.sendReport16(RID_CONSUMER_CONTROL, );
    // usb
}

void keyboard_press_key(uint8_t key) {
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

void keyboard_release_key(uint8_t key) {
    for (size_t i = 0; i < sizeof(pressed_keys); i++) {
        if (pressed_keys[i] == key) {
            Serial.printf("shift %d", i);
            // Check for last key
            if (i >= sizeof(pressed_keys) - 1) {
                pressed_keys[i] = 0;
            }

            // Shift keys over
            else {
                Serial.printf("shift %d", i);
                memmove(pressed_keys + i, pressed_keys + i + 1, sizeof(pressed_keys) - i - 1);
            }
        }
    }
}