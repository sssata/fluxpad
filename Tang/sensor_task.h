#pragma once

#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/time.h"
#include "TLE493D.h"

#define SENSOR_0_SDA_PIN 4
#define SENSOR_0_SCL_PIN 5

#define SENSOR_1_SDA_PIN 6
#define SENSOR_1_SCL_PIN 7

#define SENSOR_0_I2C i2c0
#define SENSOR_1_I2C i2c1

#define SENSOR_BAUDRATE 1000*1000

#define SENSOR_TASK_FREQUENCY_HZ 1
#define SENSOR_TASK_PERIOD_US (1000000.0/SENSOR_TASK_FREQUENCY_HZ)

typedef struct{
    TLE493D_t sensor_0;
    TLE493D_t sensor_1;
} sensor_task_t;

extern sensor_task_t sensor_task_handle;

void sensor_task_run(void);
void sensor_task_init();
void sensor_task(void);


