#include <Adafruit_TinyUSB.h>
#include <Arduino.h>
#include <hardware/flash.h>

#include "HIDConsumerService.hpp"
#include "HIDKeyboardService.hpp"
#include "USBCommon.hpp"

// Report ID
enum {
    RID_KEYBOARD = 1,
    RID_MOUSE,
    RID_CONSUMER_CONTROL, // Media, volume etc ..
};

// uint8_t pressed_keys[6];

uint8_t pressed_mouse_buttons;

// uint8_t report[REPORT_MAX_SIZE];
// size_t report_len;

HIDConsumerDevice consumer_device = HIDConsumerDevice();
HIDKeyboard keyboard_device = HIDKeyboard();

// HID report descriptor using TinyUSB's template
uint8_t const desc_hid_report[] = {TUD_HID_REPORT_DESC_KEYBOARD(HID_REPORT_ID(RID_KEYBOARD)),
                                   TUD_HID_REPORT_DESC_MOUSE(HID_REPORT_ID(RID_MOUSE)),
                                   TUD_HID_REPORT_DESC_CONSUMER(HID_REPORT_ID(RID_CONSUMER_CONTROL))};

Adafruit_USBD_HID usb_hid(desc_hid_report, sizeof(desc_hid_report), HID_ITF_PROTOCOL_NONE, 1, false);

char serial_number[32];
char product_descriptor[] = "Fluxpad V2 Analog Keypad";
char manufacturer_descriptor[] = "FLUXPAD";

uint64_t get_serial_number() {
    uint64_t serial_number;
    flash_get_unique_id((uint8_t *)&serial_number);
    return serial_number;
}

void usb_service_setup(uint16_t vid, uint16_t pid) {
    TinyUSBDevice.setID(vid, pid);
    sprintf(serial_number, "%llu", get_serial_number());
    TinyUSBDevice.setSerialDescriptor(serial_number);

    TinyUSBDevice.setProductDescriptor(product_descriptor);
    TinyUSBDevice.setManufacturerDescriptor(manufacturer_descriptor);

    usb_hid.begin();
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
        if (keyboard_device.isPressed()) {
            shouldWakeup = true;
        }
        if (pressed_mouse_buttons > 0) {
            shouldWakeup = true;
        }
        if (consumer_device.isPressed()) {
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

    if (TinyUSBDevice.mounted()) {
        usb_hid_wait_until_ready(usb_hid, USB_HID_WAIT_TIME_US);
        if (usb_hid.ready()) {
            // usb_hid.keyboardReport(RID_KEYBOARD, 0, pressed_keys);
            keyboard_device.hid_keyboard_service(usb_hid, RID_KEYBOARD);
            consumer_device.hid_consumer_service(usb_hid, RID_CONSUMER_CONTROL);
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
}
