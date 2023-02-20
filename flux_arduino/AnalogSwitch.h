
#pragma once

// #include "FIR_filter.hpp"
#include <stdint.h>

// Q22.10 fixed point
typedef uint32_t q22_10_t;

#define INT_TO_Q22_10(x) x << 10
#define Q22_10_TO_INT(x) x >> 10
#define Q22_10_TO_FLOAT(x) ((x)/(1024.0))

// typedef Array<fir_tap_t, FIR_NUM_TAPS> fir_taps_array_t;

// fir_taps_array_t fir_taps {0};

uint32_t adc_to_dist_lut[4] = {1 >> 10, 2, 3, 4};

typedef struct {
    q22_10_t press_hysteresis;
    q22_10_t release_hysteresis;
    q22_10_t actuation_point;
    q22_10_t release_point;
    uint32_t samples;
} AnalogSwitchSettings_t;

class AnalogSwitch {
  public:
    uint32_t pin = 0;
    uint32_t id = 0;

    q22_10_t current_reading = 0;
    q22_10_t distance_mm = 0;
    q22_10_t max_reading;
    q22_10_t min_reading;

    bool is_pressed = false;
    bool is_setup = false;
    bool use_freerun_mode = false;

    AnalogSwitchSettings_t settings;

    AnalogSwitch(uint32_t _pin, uint32_t _id) : pin(_pin), id(_id) {}

    void setup() {
        pinMode(pin, INPUT);
        ADCsetup(64, 0);
        is_pressed = false;
        reset_min_max();
        is_setup = true;
    }

    void applySettings(AnalogSwitchSettings_t *_settings) {
        settings = *_settings;
    }

    void takeAvgReading(size_t no_of_measurements) {
        q22_10_t sum = 0;
        for (size_t i = 0; i < no_of_measurements; i++) {
            sum += INT_TO_Q22_10(analogRead(pin));
        }
        current_reading = sum / no_of_measurements;
    }

    void mainLoopService() {
        if (use_freerun_mode){
            takeAvgReadingFreerun(settings.samples);
        } else {
            takeAvgReading(settings.samples);
        }
        // Serial.printf("current_reading: %lu, max_reading: %lu, min_reading: %lu ", current_reading, max_reading, min_reading);
        // Serial.printf("press_hys: %lu, release_hys: %lu ", settings.press_hysteresis, settings.release_hysteresis);

        switch (is_pressed) {
        case true:
            if (current_reading > max_reading) {
                max_reading = current_reading;
            }

            if (max_reading - current_reading > settings.press_hysteresis) {
                is_pressed = false;
                reset_min_max();
                min_reading = current_reading;
            };
            break;
        case false:
            if (current_reading < min_reading) {
                min_reading = current_reading;
            }

            if (current_reading - min_reading > settings.release_hysteresis) {
                is_pressed = true;
                reset_min_max();
                max_reading = current_reading;
            };
            break;
        default:
            // Nothing
            break;
        }
    }

    /**
     * @brief Read n samples from pin in freerun mode
     * 
     * @param samples 
     * @param pin 
     * @return uint32_t 
     */
    uint32_t takeAvgReadingFreerun(size_t samples){
        syncADC();

        ADC->INPUTCTRL.bit.MUXPOS = g_APinDescription[pin].ulADCChannelNumber;  // Select pos adc input
        ADC->CTRLB.bit.FREERUN = 1;  // Turn on freerun mode

        ADC->CTRLA.bit.ENABLE = 1;  // Turn on ADC
        syncADC();

        ADC->SWTRIG.bit.START = 1;  // Start conversion
        syncADC();

        // Throw away first result after turning on the ADC
        while (ADC->INTFLAG.bit.RESRDY == 0);   // Wait for conversion to complete
        uint32_t throwaway = ADC->RESULT.reg;
        ADC->INTFLAG.reg = ADC_INTFLAG_RESRDY;  // Clear ready flag

        q22_10_t sum = 0;
        for (size_t i=0; i<samples; i++){
            while (ADC->INTFLAG.bit.RESRDY == 0);   // Wait for conversion to complete
            uint32_t result = ADC->RESULT.reg;
            ADC->INTFLAG.reg = ADC_INTFLAG_RESRDY;  // Clear ready flag
            sum += INT_TO_Q22_10(result);
        }
        current_reading = sum / samples;

        ADC->CTRLA.bit.ENABLE = 0;
    }
    
    // Wait for synchronization of registers between the clock domains
    static inline __attribute__((always_inline)) void syncADC() {
        while (ADC->STATUS.bit.SYNCBUSY == 1);
    }

    void ADCsetup(unsigned int prescaler, unsigned int cyclesPerSample) {
        unsigned int my_ADC_CTRLB_PRESCALER_DIV;
        unsigned int my_SAMPCTRLREGVal;

        
        if (prescaler == 4) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV4_Val;
        } else if (prescaler == 8) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV8_Val;
        } else if (prescaler == 16) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV16_Val;
        } else if (prescaler == 32) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV32_Val;
        } else if (prescaler == 64) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV64_Val;
        } else if (prescaler == 128) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV128_Val;
        } else if (prescaler == 256) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV256_Val;
        } else if (prescaler == 512) {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV512_Val;
        } else {
            my_ADC_CTRLB_PRESCALER_DIV = ADC_CTRLB_PRESCALER_DIV512_Val;
        }
        // ADC->CTRLB.reg = my_ADC_CTRLB_PRESCALER_DIV | ADC_CTRLB_RESSEL_12BIT;
        ADC->CTRLB.bit.PRESCALER = my_ADC_CTRLB_PRESCALER_DIV;
        
        while (ADC->STATUS.bit.SYNCBUSY);
        
        if (cyclesPerSample < 0) {
            cyclesPerSample = 0;
        }
        if (cyclesPerSample > 63) {
            cyclesPerSample = 63;
        }
        ADC->SAMPCTRL.reg = cyclesPerSample;

    }

    void adc_to_distance() {}

  private:
    // /**
    //  * @brief Fixed point linear interpolation.
    //  *
    //  * @param a
    //  * @param b
    //  * @param t
    //  * @return uint32_t
    //  */
    // adc_s32_t lerp(us22_10_t a, us22_10_t b, us22_10_t t)
    // {
    //     return (((a << FXP_FRAC_BITS) - t) * a + t * b) >> (FXP_FRAC_BITS *
    //     2);
    // }

    
    void reset_min_max(){
        min_reading = UINT32_MAX;
        max_reading = 0;
    }


};


/*#include <iostream>

#define FXP_FRAC_BITS 10

size_t adc_bits = 12;
size_t lut_bits = 2;

typedef uint32_t us22_10_t;

us22_10_t adc_to_dist_lut[] = {
    1 << 10,
    2 << 10,
    4 << 10,
    8 << 10,
};

us22_10_t lerp(us22_10_t a, us22_10_t b, us22_10_t t)
{
    return (((a << FXP_FRAC_BITS) - t) * a + t * b) >> (FXP_FRAC_BITS * 2);
}

us22_10_t lut(us22_10_t x)
{
    size_t x_lut = x >> FXP_FRAC_BITS >> (adc_bits - lut_bits);
    return lerp(adc_to_dist_lut[x_lut], adc_to_dist_lut[x_lut + 1], x);
}

float to_float(us22_10_t x)
{
    return static_cast<float>(x) / (1 << FXP_FRAC_BITS);
}

us22_10_t to_us22_10_t(float x)
{
    return static_cast<uint32_t>(x * (1 << FXP_FRAC_BITS));
} */

// int main()
// {
//     cout<<"Hello World";

//     float adc = 1024.1;

//     us22_10_t adc_fixed = to_us22_10_t(adc);

//     us22_10_t result = lut(adc_fixed);

//     float result_float = to_float(result);

//     cout << "adc: " << adc << endl;
//     cout << "adc float: " << adc_fixed << endl;
//     cout << "result: " << result << endl;
//     cout << "result_float: " << result_float << endl;

//     return 0;
// }