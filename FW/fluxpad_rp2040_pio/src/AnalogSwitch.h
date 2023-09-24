
#pragma once

// #include "FIR_filter.hpp"
#include <ADCInput.h>
#include <hardware/adc.h>
#include <stdint.h>

#include "WelfordsAlgorithm.h"

// #include <cstdlib>

// Q22.10 fixed point
// Use fixed point numbers instead of floats since SAM D21 doesn't have FPU
typedef uint32_t q22_10_t;

// Signed Q53.10 fixed point for large fixed point numbers
typedef int64_t q53_10_t;

#define Q22_10_FRAC_BITS 10
#define Q22_10_INT_BITS 22

#define INT_TO_Q22_10(x) ((x) << 10)
#define Q22_10_TO_INT(x) ((x) >> 10)
#define Q22_10_TO_FLOAT(x) ((x) / (1024.0f))
#define FLOAT_TO_Q22_10(x) static_cast<q22_10_t>((x) * (1024))

// ADC to Distance(mm) LUT
#define ADC_BITS 12
#define LUT_BITS 4
const q22_10_t adc_to_dist_lut[] = {
    FLOAT_TO_Q22_10(0.0f), // 0
    FLOAT_TO_Q22_10(0.8f), // 256
    FLOAT_TO_Q22_10(2.1f), // 512
    FLOAT_TO_Q22_10(2.54f), // 768
    FLOAT_TO_Q22_10(2.71f),  // 1024
    FLOAT_TO_Q22_10(2.89),  // 1280
    FLOAT_TO_Q22_10(3.12f),  // 1536
    FLOAT_TO_Q22_10(3.4f),  // 1792
    FLOAT_TO_Q22_10(3.75f), // 2048
    FLOAT_TO_Q22_10(4.2f), // 2304
    FLOAT_TO_Q22_10(4.9f), // 2560
    FLOAT_TO_Q22_10(6.0f), // 2816
    FLOAT_TO_Q22_10(8.1f), // 3072
    FLOAT_TO_Q22_10(8.6f), // 3328
    FLOAT_TO_Q22_10(9.0f), // 3584
    FLOAT_TO_Q22_10(9.5f), // 3840
    FLOAT_TO_Q22_10(10.0f), // 4096
};

const q22_10_t reference_up_mm = FLOAT_TO_Q22_10(6.0f);
const q22_10_t reference_down_mm = FLOAT_TO_Q22_10(2.0f);

const q22_10_t reference_up_adc = INT_TO_Q22_10(2816);
const q22_10_t reference_down_adc = INT_TO_Q22_10(492);
const size_t ADC_SAMPLES_N = 110;

/**
 * @brief Stores all operational settings for an analog switch
 *
 */
typedef struct {
    bool rapid_trigger_enable;
    q22_10_t press_hysteresis_mm;
    q22_10_t release_hysteresis_mm;
    q22_10_t actuation_point_mm;
    q22_10_t release_point_mm;
    uint32_t press_debounce_ms;
    uint32_t release_debounce_ms;
    uint32_t samples;
    q22_10_t calibration_up_adc = reference_up_adc;
    q22_10_t calibration_down_adc = reference_down_adc;
} AnalogSwitchSettings_t;

class AnalogSwitch {
  public:
    const uint32_t pin = 0;
    const uint32_t id = 0;

    q22_10_t current_reading = 0;
    q22_10_t current_reading_calibrated = 0;
    q22_10_t current_height_mm = 0;
    q22_10_t max_height_mm;
    q22_10_t min_height_mm;
    uint32_t last_pressed_time_ms = 0;
    uint32_t last_released_time_ms = 0;

    bool is_pressed = false;
    bool was_pressed = false;
    bool is_setup = false;
    bool use_freerun_mode = true;
    ADCInput adc_input;
    WelfordAlgorithm welford;

    AnalogSwitchSettings_t settings;

    AnalogSwitch(uint32_t pin, uint32_t id) : pin(pin), id(id), adc_input(pin) {}

    /**
     * @brief Setup hardware for analog key
     */
    void setup() {
        adc_gpio_init(pin);
        adc_set_clkdiv(0);
        adc_init();

        resetMinMaxDistance();
        is_pressed = false;
        is_setup = true;
        // analogRead(pin);
        last_pressed_time_ms = millis();
        last_released_time_ms = millis();
    }

    /**
     * @brief Update operational settings of the analog switch
     *
     * @param _settings
     */
    void applySettings(const AnalogSwitchSettings_t *_settings) { settings = *_settings; }

    void mainLoopService() {
        unsigned long current_time_ms = millis();
        // if (use_freerun_mode) {
        //     // takeAvgReadingFreerun(settings.samples);
        // } else {
        //     takeAvgReading(settings.samples);
        // }
        takeAvgReading(ADC_SAMPLES_N);
        // Serial.printf("current_reading: %lu, max_reading: %lu, min_reading:
        // %lu ", current_reading, max_reading, min_reading);
        // Serial.printf("press_hys: %lu, release_hys: %lu ",
        // settings.press_hysteresis, settings.release_hysteresis);
        current_reading_calibrated = apply_calibration(current_reading);
        current_height_mm = adcCountsToDistanceMM(current_reading_calibrated);
        welford.update(Q22_10_TO_FLOAT(current_height_mm));

        // Check if we are at guaranteed release or guaranteed press height
        bool height_should_actuate = current_height_mm < settings.actuation_point_mm;
        bool height_should_release = current_height_mm > settings.release_point_mm;

        was_pressed = is_pressed;
        switch (is_pressed) {
        case false: {
            // If we are released, we are looking for the right conditions to press the key
            if (!settings.rapid_trigger_enable) {
            }

            // Update max distance
            if (current_height_mm > max_height_mm) {
                max_height_mm = min(settings.release_point_mm, current_height_mm); // Cap at guaranteed release distance
            }

            // Check if should press
            bool no_rapid_trigger_should_press =
                !settings.rapid_trigger_enable && current_height_mm < settings.actuation_point_mm;
            bool hysteresis_should_press =
                abs(static_cast<int>(max_height_mm - current_height_mm)) > settings.press_hysteresis_mm;
            bool should_press = settings.rapid_trigger_enable &&
                                ((hysteresis_should_press || height_should_actuate) && !height_should_release);
            // Serial.printf("hyp: %d, hp: %d, sp: %d\n", hysteresis_should_press, height_should_actuate, should_press);

            // Update debounce timer
            if (settings.rapid_trigger_enable) {
                if (!should_press) {
                    last_released_time_ms = current_time_ms;
                }
            } else {
                if (!no_rapid_trigger_should_press) {
                    last_released_time_ms = current_time_ms;
                }
            }

            // Check debounce timer
            if (current_time_ms - last_released_time_ms > settings.press_debounce_ms) {
                // All conditions for press fullfilled for at least debounce time
                // Transition to pressed state
                is_pressed = true;
                resetMinMaxDistance(); // Reset max height
            }
            break;
        }
        case true: {
            // If we are pressed, we are looking for the right conditions to release the key

            // Update min distance
            if (current_height_mm < min_height_mm) {
                min_height_mm =
                    max(settings.actuation_point_mm, current_height_mm); // Cap at guaranteed actuation distance
            }

            // Check if should release
            bool no_rapid_trigger_should_release =
                !settings.rapid_trigger_enable && current_height_mm > settings.release_point_mm;
            bool hysteresis_should_release =
                abs(static_cast<int>(current_height_mm - min_height_mm)) > settings.release_hysteresis_mm;
            bool should_release = (hysteresis_should_release || height_should_release) && !height_should_actuate;
            // Serial.printf("hyr: %d, hr: %d, sr: %d\n", hysteresis_should_release, height_should_release,
            // should_release);

            // Update debounce timer
            if (settings.rapid_trigger_enable) {
                if (!should_release) {
                    last_pressed_time_ms = current_time_ms;
                }
            } else {
                if (!no_rapid_trigger_should_release) {
                    last_pressed_time_ms = current_time_ms;
                }
            }

            // Check debounce timer
            if (current_time_ms - last_pressed_time_ms > settings.release_debounce_ms) {
                // All conditions for release fullfilled for at least debounce time
                // Transition to released state
                is_pressed = false;
                resetMinMaxDistance();
            }
            break;
        }
        default:
            // Nothing
            break;
        }
    }

    /**
     * @brief Read n samples from pin with ADC
     *
     * @param samples
     * @param pin
     * @return uint32_t
     */
    void takeAvgReading(size_t no_of_measurements) {
        q22_10_t sum = 0;
        // adc_input.begin();
        adc_select_input(pin - 26);
        // adc_fifo_setup(true, false, 0, false, false);
        // adc_fifo_drain();
        // adc_run(true);
        for (size_t i = 0; i < no_of_measurements; i++) {
            // while (!adc_input.available())
            //     ;
            // sum += INT_TO_Q22_10(adc_input.read());
            // sum += INT_TO_Q22_10(adc_fifo_get_blocking());
            // sum += INT_TO_Q22_10(adc_input.read());
            sum += INT_TO_Q22_10(adc_read());
        }
        // adc_run(false);
        // adc_fifo_drain();
        // adc_input.end();
        current_reading = sum / no_of_measurements;
    }

    void setCurrentReading(uint32_t reading_counts) { INT_TO_Q22_10(reading_counts); }

    q22_10_t adcCountsToDistanceMM(q22_10_t counts) { return lut(counts); }

  private:
    void resetMinMaxDistance() {
        min_height_mm = UINT32_MAX;
        max_height_mm = 0;
    }

    /**
     * @brief Linearly interpolate input t between a and b.
     *
     * @param a If t=0, output is a
     * @param b If t=1, output is b
     * @param t Must be between 0 an 1
     * @return q22_10_t
     */
    q22_10_t lerp(q22_10_t a, q22_10_t b, q22_10_t t) const {
        q22_10_t a_weight = a * ((1 << Q22_10_FRAC_BITS) - t) >> Q22_10_FRAC_BITS;
        q22_10_t b_weight = b * t >> Q22_10_FRAC_BITS;
        return a_weight + b_weight;
    }

    /**
     * @brief Linear interpolation
     *
     * @param x If x=x0, output is y0, if x=x1, output is y1
     * @param y0 output mapping
     * @param y1 output mapping
     * @param x0 input mapping
     * @param x1 input mapping
     * @return q22_10_t
     */
    q22_10_t lerp2(q22_10_t x, q22_10_t y0, q22_10_t y1, q22_10_t x0, q22_10_t x1) const {
        q53_10_t term_a = int64_t(y0) * (int64_t(x1) - int64_t(x));
        q53_10_t term_b = int64_t(y1) * (int64_t(x) - int64_t(x0));
        q53_10_t term_c = int64_t(x1) - int64_t(x0);
        q53_10_t temp = (term_a + term_b) / term_c;
        return static_cast<q22_10_t>(temp); // Should be safe to truncate back to 32 bits at this point
    }

    q22_10_t apply_calibration(q22_10_t adc) const {
        return lerp2(adc, reference_down_adc, reference_up_adc, settings.calibration_down_adc,
                     settings.calibration_up_adc);
    }

    /**
     * @brief converts adc counts to distance with a lookup table
     *
     * @param x input, must be in range [0 and 2^ADC_BITS)
     * @return q22_10_t
     */
    q22_10_t lut(q22_10_t x) {
        // Get integer part of input
        size_t x_integer = Q22_10_TO_INT(x);
        // Convert ADC integer to LUT index
        size_t lut_index = x_integer >> (ADC_BITS - LUT_BITS);
        // Convert LUT index back to ADC but now it's floored
        q22_10_t x_floored = INT_TO_Q22_10(lut_index << (ADC_BITS - LUT_BITS));
        // Get difference between input and LUT index
        q22_10_t fraction = (x - x_floored) >> (ADC_BITS - LUT_BITS);
        return lerp(adc_to_dist_lut[lut_index], adc_to_dist_lut[lut_index + 1], fraction);
    }
};
