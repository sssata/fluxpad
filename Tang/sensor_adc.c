#include "sensor_adc.h"

static const uint64_t measurement_period_us = 100*1000;

void adc_speed_test(void){
    
    absolute_time_t last_start_time = get_absolute_time();
    uint32_t adc_samples = 0;
    float adc_avg = 0;

    adc_init();
    adc_select_input(26);


    while (1){
        absolute_time_t current_time = get_absolute_time();
        uint64_t time_since_last_start_time_us = absolute_time_diff_us(last_start_time, current_time);
        if (time_since_last_start_time_us > measurement_period_us){
            // printf("%llu", to_us_since_boot(current_time));
            // printf(",%llu", time_since_last_start_time_us);
            // printf("%lu", adc_samples);
            printf("%f\n", adc_avg);
            last_start_time = current_time;
            adc_samples = 0;
        }
        else{
            // adc_select_input(26);
            uint16_t read = adc_read();
            adc_samples ++;
            float prev_weight = (float)(adc_samples - 1)/(float)adc_samples;
            float curr_weight = 1.0 - prev_weight;
            adc_avg = adc_avg * prev_weight + (float)read * curr_weight;
        }
    }
}
