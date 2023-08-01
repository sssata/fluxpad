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
class HIDConsumerDevice {
  private:
    enum class ConsumerKeyState {
        IDLE,
        PRESS,
        RELEASE,
    } consumer_key_state;

    uint16_t pressed_consumer_key;

  public:
    HIDConsumerDevice() {
        pressed_consumer_key = 0;
        consumer_key_state = ConsumerKeyState::IDLE;
    }

    /**
     * @brief Press the given keyboard keycode
     *
     * @param key
     * @returns true if key successfully pressed
     */
    bool consumer_press_and_release_key(uint16_t key) {

        if (consumer_key_state == ConsumerKeyState::IDLE) {
            pressed_consumer_key = key;
            consumer_key_state = ConsumerKeyState::PRESS;
            return true;
        }
        return false;
    }

    /**
     * @brief Should be run once in main loop if usb_hid device is ready
     *
     */
    void hid_consumer_service(Adafruit_USBD_HID &usb_hid, const uint8_t report_id) {
        bool send_report_ok = false;
        switch (consumer_key_state) {
        case ConsumerKeyState::PRESS: {
            // Press once and then immediately release next call
            if (usb_hid_wait_until_ready(usb_hid, USB_HID_WAIT_TIME_US) &&
                usb_hid.sendReport16(report_id, pressed_consumer_key)) {
                consumer_key_state = ConsumerKeyState::RELEASE;
            }
            // Serial.printf("hello %d %d\n", , pressed_consumer_key);

            break;
        }
        case ConsumerKeyState::RELEASE:
            // Release all keys
            if (usb_hid_wait_until_ready(usb_hid, USB_HID_WAIT_TIME_US) && usb_hid.sendReport16(report_id, 0)) {
                consumer_key_state = ConsumerKeyState::IDLE;
            }
            // send_report_ok usb_hid.sendReport16(report_id, 0);
            break;
        case ConsumerKeyState::IDLE:
            // Do nothing
            break;
        }
    }

    // bool append_consumer_report(uint8_t report_id, uint8_t *report, size_t &report_len) {
    //     if (report_len + sizeof(pressed_consumer_key) + sizeof(report_id) > REPORT_MAX_SIZE) {
    //         return false;
    //     }

    //     // report[report_len] = report_id;
    //     memcpy(report + report_len, &pressed_consumer_key, sizeof(pressed_consumer_key));
    //     // report_len += sizeof(report_id);
    //     report_len += sizeof(pressed_consumer_key);
    //     return true;
    // }

    /**
     * @brief Get whether key is currently pressed or released
     *
     * @return true
     * @return false
     */
    bool isPressed() { return (consumer_key_state == ConsumerKeyState::PRESS); }
};
