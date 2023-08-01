#pragma once
#include <Adafruit_TinyUSB.h>
#include <hardware/timer.h>
// #include <hardware/tim>

const uint32_t USB_HID_WAIT_TIME_US = 1500;

/**
 * @brief Blocks until given usb hid interface is ready
 *
 * @return true if ready
 * @return false if timeout before ready
 */
bool usb_hid_wait_until_ready(Adafruit_USBD_HID &usb_hid, uint32_t timeout_us) {
    auto start_time_us = time_us_64();
    do {
        if (usb_hid.ready()) {
            return true;
        }
    } while (time_us_64() - timeout_us < start_time_us);
    return false;
}