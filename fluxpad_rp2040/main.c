#include <stdio.h>
#include "pico/stdlib.h"
#include "usb_task.h"
#include "sensor_task.h"
#include "rapid_trigger.h"
#include "pico/multicore.h"
#include "pico/stdio_usb.h"
#include "hardware/irq.h"
#include "sensor_adc.h"

const uint key_pin = 10;

void sensor_adc_init(){
    gpio_set_dir(key_pin, GPIO_IN);
    gpio_pull_up(key_pin);
}


int main() {

    // Initialize LED pin
    gpio_init(led_pin);
    gpio_set_dir(led_pin, GPIO_OUT);

    sensor_adc_init();

    // Initialize chosen serial port
    tusb_init();

    stdio_usb_init();
    

    uint64_t last_time = time_us_64();
    uint64_t print_period_us = 1000*1000;

    // sensor_task_init();
    // multicore_launch_core1(sensor_task_run);
    // multicore_launch_core1(adc_speed_test);
    // Loop forever
    while (true) {
        // adc_speed_test();

        // sensor_task();  //read sensors task
        // rapid_trigger_step();
        // // sensor_task();
        // hid_task();
        uint64_t curr_time = time_us_64();
        if (last_time - curr_time > print_period_us){
            printf("hello\n");
            last_time = curr_time;
        }

        tud_cdc_read("");
        tud_task(); // tinyusb device task
        hid_task(gpio_get(key_pin)); // hid device task

        // // Blink LED
        // printf("Blinking!\r\n");
        // gpio_put(led_pin, true);
        // sleep_ms(1000);
        // gpio_put(led_pin, false);
        // sleep_ms(1000);
    }
}

