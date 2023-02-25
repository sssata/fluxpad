
#include "sensor_task.h"

// DEFINES


// TYPES

// GLOBALS
sensor_task_t sensor_task_handle;

// PROTOTYPES

/**
 * @brief Adds period to last_wake_time and sleeps until then
 * If next wake time is before current time, does not sleep.
 * Use this to best effort maintain a loop frequency.
 * 
 * @param last_wake_time last time this function was called
 * @param period_us time to delay
 * @return absolute_time_t 
 */
static bool sleep_until_update(absolute_time_t* last_wake_time, uint64_t period_us);

// CODE

void sensor_task_init(void){

    // Setup GPIOs for I2C
    gpio_set_function(SENSOR_0_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SENSOR_0_SCL_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SENSOR_1_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SENSOR_1_SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(SENSOR_0_SDA_PIN);
    gpio_pull_up(SENSOR_0_SCL_PIN);
    gpio_pull_up(SENSOR_1_SDA_PIN);
    gpio_pull_up(SENSOR_1_SCL_PIN);

    // Create tle493d sensor structs
    sensor_task_handle.sensor_0 = tle493d_create(TLE493D_A0, SENSOR_0_I2C, SENSOR_BAUDRATE);
    sensor_task_handle.sensor_1 = tle493d_create(TLE493D_A0, SENSOR_1_I2C, SENSOR_BAUDRATE);

    // i2c must be initialized before tle_init
    i2c_init(sensor_task_handle.sensor_0.i2c, sensor_task_handle.sensor_0.i2c_baudrate);
    
    tle493d_init(&(sensor_task_handle.sensor_0));
    // tle493d_init(&(sensor_task_handle.sensor_1));

}
void hello(void){
    printf("hello\n");
}

void sensor_task_run(void){
    sensor_task_init();
    irq_add_shared_handler(I2C0_IRQ, &hello, PICO_SHARED_IRQ_HANDLER_DEFAULT_ORDER_PRIORITY);
    
    absolute_time_t last_wake_time = get_absolute_time();
    while(1){
        sensor_task();
        sleep_until_update(&last_wake_time, SENSOR_TASK_PERIOD_US);
    }
        
}


void sensor_task(void){
    tle493d_init(&(sensor_task_handle.sensor_0));
    tle493d_read_blocking(&(sensor_task_handle.sensor_0));
    // tle493d_read_blocking(&(sensor_task_handle.sensor_1));
}

static bool sleep_until_update(absolute_time_t* last_wake_time, uint64_t period_us){
    printf("period: %u, us: %u\n", to_us_since_boot(*last_wake_time), period_us);
    absolute_time_t curr_time = get_absolute_time();
    absolute_time_t next_wake_time = delayed_by_us(*last_wake_time, period_us);
    bool has_slept = true;
    if (absolute_time_diff_us(curr_time, next_wake_time) < 0){
        next_wake_time = curr_time;
        has_slept = false;
    }
    *last_wake_time = next_wake_time;
    sleep_until(next_wake_time);
    return has_slept;
}
