#pragma once

#include "pico/stdlib.h"
#include "tusb.h"
#include "usb_descriptors.h"

//--------------------------------------------------------------------+
// MACRO CONSTANT TYPEDEF PROTYPES
//--------------------------------------------------------------------+

static uint32_t blink_interval_ms = 0;
extern const uint32_t led_pin;

void led_blinking_task(void);
void hid_task(void);