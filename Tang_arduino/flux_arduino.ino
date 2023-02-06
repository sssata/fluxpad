#include <HID-Project.h>
#include <HID-Settings.h>
#include <ArduinoJson.h>
#include <Encoder.h>
#include <FlashStorage_SAMD.h>
#include "FIR_filter.hpp"
#include "Switch.hpp"

#define SAMPLE_FREQ_HZ 10
#define SAMPLE_PERIOD_US 1000000 / SAMPLE_FREQ_HZ

#define KEY1_PIN 3
#define KEY2_PIN 9
#define KEY3_PIN 6
#define KEY4_PIN 8


#define FIR_NUM_TAPS 32
const int samples = 10;
const int readPin = 6;

unsigned long last_time_us;


KeySwitch analogKey1 = KeySwitch(KEY3_PIN);
KeySwitch analogKey2 = KeySwitch(KEY4_PIN);;

KeySwitch analogKeys [] = {analogKey1, analogKey2};

void setup()
{
  // put your setup code here, to run once:
  Serial.begin(115200);
  analogReadResolution(12);

  last_time_us = micros();
}

void loop()
{
  //  delay(10);

  if (micros() - last_time_us < SAMPLE_PERIOD_US)
  {
    return;
  }
  last_time_us = micros();

  for (auto key : analogKeys){
    key.take_avg_reading(20);
    Serial.printf("%d,", key.avg_reading);
  }
  Serial.printf("\n");


  //  Serial.printf("%d\n", analogRead(readPin));

  // float sum = 0;
  // for (int i = 0; i < samples; i++)
  // {
  //   delayMicroseconds(10);
  //   sum += (float)(analogRead(readPin));
  // }
  // float avg = sum / samples;
  // Serial.printf("%f\n", avg);

  // for (const auto &i : FIR_coefficients)
  // {
  //   Serial.printf("%d, ", i);
  // }
}
