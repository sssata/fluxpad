
#include "FIR_filter.hpp"

#define FIR_NUM_TAPS 63

typedef uint32_t milli_adc_t;

#define ADC_TO_MILLI_ADC(x) x * 1000

// typedef Array<fir_tap_t, FIR_NUM_TAPS> fir_taps_array_t;

// fir_taps_array_t fir_taps {0};


class KeySwitch {
  public:

    int pin;
    char key;
    milli_adc_t avg_reading;
    KeySwitch(int pin) : pin(pin) {}
    
    void begin() {
      pinMode(pin, INPUT_PULLUP);
    }
    
    bool isPressed() {
      return !digitalRead(pin);
    }

    void take_avg_reading(size_t no_of_measurements){
        milli_adc_t sum = 0;
        for (size_t i = 0; i < no_of_measurements; i++){
            sum += ADC_TO_MILLI_ADC(analogRead(pin));
        }
        avg_reading = sum/no_of_measurements;

    }

  private:
};



