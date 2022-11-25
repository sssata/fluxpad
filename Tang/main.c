#include <stdio.h>
#include "pico/stdlib.h"
#include "usb_task.h"
#include "sensor_task.h"
#include "rapid_trigger.h"
#include "pico/multicore.h"
#include "pico/stdio_usb.h"
#include "hardware/irq.h"

int main() {

    // Initialize LED pin
    gpio_init(led_pin);
    gpio_set_dir(led_pin, GPIO_OUT);

    // Initialize chosen serial port
    tusb_init();
    stdio_init_all();

    // sensor_task_init();
    multicore_launch_core1(sensor_task_run);
    // Loop forever
    while (true) {

        // sensor_task();  //read sensors task
        rapid_trigger_step();
        // sensor_task();
        hid_task();
        tud_task(); // tinyusb device task
        // hid_task(); // hid device task

        // // Blink LED
        // printf("Blinking!\r\n");
        // gpio_put(led_pin, true);
        // sleep_ms(1000);
        // gpio_put(led_pin, false);
        // sleep_ms(1000);
    }
}

