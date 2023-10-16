
#include <ADCInput.h>
#include <Adafruit_TinyUSB.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include <LittleFS.h>
#include <RotaryEncoder.h>
#include <hardware/adc.h>

#include "AnalogSwitch.h"
#include "DigitalSwitch.h"
#include "KeyLighting.h"
#include "RBGLed.h"
#include "USBService.hpp"
#include "tusb_config.h"

// #include "flash.h"
// #include <RP2040.h>

#define HZ_TO_PERIOD_US(x) (1000000 / (x))

#define VERSION 2

// PIN DEFINITIONS
constexpr uint32_t ENC_A_PIN = 23u;
constexpr uint32_t ENC_B_PIN = 24u;
constexpr uint32_t KEY0_PIN = 20u;
constexpr uint32_t KEY1_PIN = 21u;
constexpr uint32_t KEY2_PIN = A2;
constexpr uint32_t KEY3_PIN = A1;
constexpr uint32_t KEY4_PIN = A0;

#define KEY0_LIGHT_PIN 5u
#define KEY1_LIGHT_PIN 6u
#define KEY2_LIGHT_PIN 3u
#define KEY3_LIGHT_PIN 4u
#define KEY4_LIGHT_PIN 7u
constexpr uint32_t RGB_LED_PIN = 11u;

#define LED_PIN 13u

// GLOBALS
constexpr uint32_t normal_mode_freq_hz = 2000;

constexpr int WRITTEN_SIGNATURE = 0xABCDEF01;
constexpr uint16_t storedAddress = 0;

constexpr uint32_t ENC_UP_KEY_ID = 5u;
constexpr uint32_t ENC_DOWN_KEY_ID = 6u;

constexpr uint16_t VID = 0x1209;
constexpr uint16_t PID = 0x7272;

// GLOBAL STATE
bool debug_mode = false;

uint32_t mainloop_period_us = HZ_TO_PERIOD_US(normal_mode_freq_hz);

uint64_t loop_count = 0;
uint64_t last_print_us = 0;
uint32_t print_period_us = 2 * 1000 * 1000;

uint64_t last_time_us;

// ENUMS
enum class KeyType_t { NONE = 0, KEYBOARD = 1, CONSUMER = 2, MOUSE = 3 };

// STRUCTS
typedef struct {
    union keycode {
        uint8_t keyboard;
        uint16_t consumer;
        uint16_t value;
    } keycode = {};
    KeyType_t keyType;
} KeyMapEntry_t;

typedef struct {
    KeyMapEntry_t keymap[7];

    AnalogSwitchSettings_t analogSettings[3];
    DigitalSwitchSettings_t digitalSettings[2];

    KeyLightingSettings_t lightingSettings[5];

    RGBSettings rgbSettings;

    uint64_t firstWriteTimestamp = 0;
    uint64_t lastWriteTimestamp = 0;
} StorageVars_t;

StorageVars_t storage_vars;

// EncoderTool::PolledEncoder encoder;
RotaryEncoder encoder(ENC_A_PIN, ENC_B_PIN, RotaryEncoder::LatchMode::FOUR3);

RGBLeds rgb_leds(storage_vars.rgbSettings);

DigitalSwitch digitalKeys[] = {
    DigitalSwitch(KEY0_PIN, 0),
    DigitalSwitch(KEY1_PIN, 1),
};

AnalogSwitch analogKeys[] = {
    AnalogSwitch(KEY2_PIN, 2),
    AnalogSwitch(KEY3_PIN, 3),
    AnalogSwitch(KEY4_PIN, 4),
};

KeyLighting keyLighting[] = {
    KeyLighting(KEY0_LIGHT_PIN, digitalKeys[0].is_pressed), KeyLighting(KEY1_LIGHT_PIN, digitalKeys[1].is_pressed),
    KeyLighting(KEY2_LIGHT_PIN, analogKeys[0].is_pressed),  KeyLighting(KEY3_LIGHT_PIN, analogKeys[1].is_pressed),
    KeyLighting(KEY4_LIGHT_PIN, analogKeys[2].is_pressed),
};

// ADCInput adc_input(A0, A1, A2);

StaticJsonDocument<1024> request_msg;
StaticJsonDocument<1024> response_msg;

// bool datastream_mode = false;
uint32_t datastream_period_ms = 0;
uint32_t last_datatream_time_ms = 0;

void setup() {

    EEPROM.begin(1024);

    analogReadResolution(12);

    Serial.setTimeout(100);
    Serial.begin(115200);
    usb_service_setup(VID, PID);

    pinMode(ENC_A_PIN, INPUT_PULLUP);
    pinMode(ENC_B_PIN, INPUT_PULLUP);

    loadFlashStorage(&storage_vars);

    for (size_t i = 0; i < sizeof(digitalKeys) / sizeof(digitalKeys[0]); i++) {
        digitalKeys[i].setup();
        digitalKeys[i].applySettings(&(storage_vars.digitalSettings[i]));
    }

    for (size_t i = 0; i < sizeof(analogKeys) / sizeof(analogKeys[0]); i++) {
        analogKeys[i].setup();
        analogKeys[i].applySettings(&(storage_vars.analogSettings[i]));
    }

    int i = 0;
    for (KeyLighting &lighting : keyLighting) {
        lighting.setup();
        lighting.applySettings(storage_vars.lightingSettings[i]);
        i++;
    }

    rgb_leds.setup();

    last_time_us = time_us_64();
}

uint64_t last_blink_time_us = 0;
int blink_state = 0;
uint32_t blink_period_us = HZ_TO_PERIOD_US(50);

void loop() {

    uint64_t curr_time_us = time_us_64();
    if (curr_time_us - last_time_us < mainloop_period_us) {
        return;
    }
    last_time_us = curr_time_us;

    loop_count++;

    if (!debug_mode) {
        if (curr_time_us - last_print_us > print_period_us) {
            float loop_freq = static_cast<float>(loop_count) / (static_cast<float>(print_period_us) / 1000000.0f);
            Serial.printf("Loop freq: %f\n", loop_freq);
            loop_count = 0;
            last_print_us = curr_time_us;
        }
    }

    // Run RGB Lights
    rgb_light_service(curr_time_us);

    for (AnalogSwitch &key : analogKeys) {
        // key.setCurrentReading(adc_input.);
        key.mainLoopService();
        if (debug_mode) {
            Serial.printf("%f %f %f  ", Q22_10_TO_FLOAT(key.current_reading), Q22_10_TO_FLOAT(key.current_height_mm),
                          key.welford.get_standard_deviation());
        }

        if (storage_vars.keymap[key.id].keyType == KeyType_t::CONSUMER) { // Hack for consumer keys, fml
            if (!key.was_pressed && key.is_pressed) {
                typeHIDKey(&(storage_vars.keymap[key.id]));
            }
        } else {
            if (key.is_pressed) {
                pressHIDKey(&(storage_vars.keymap[key.id]));
            } else {
                releaseHIDKey(&(storage_vars.keymap[key.id]));
            }
        }
    }
    if (debug_mode) {
        Serial.printf("\n");
    }

    // Scan digital keys
    for (DigitalSwitch &key : digitalKeys) {
        key.mainLoopService();

        if (storage_vars.keymap[key.id].keyType == KeyType_t::CONSUMER) {
            if (!key.was_pressed && key.is_pressed) {
                typeHIDKey(&(storage_vars.keymap[key.id]));
            }
        } else {
            if (key.is_pressed) {
                pressHIDKey(&(storage_vars.keymap[key.id]));
            } else {
                releaseHIDKey(&(storage_vars.keymap[key.id]));
            }
        }
    }

    // Scan Encoder
    encoder.tick();
    if (auto encoder_step = encoder.getPosition(); encoder_step != 0) {
        switch (encoder_step) {
        case 1:
            typeHIDKey(&(storage_vars.keymap[ENC_UP_KEY_ID]));
            break;
        case -1:
            typeHIDKey(&(storage_vars.keymap[ENC_DOWN_KEY_ID]));
            break;
        default:
            break;
        }
        encoder.setPosition(0);
    }

    // Run Key Lighting
    for (KeyLighting &lighting : keyLighting) {
        lighting.lightingTask(curr_time_us);
    }

    // Keyboard.send();
    if (!debug_mode) {
        usb_service();
    }
    read_serial();

    // Send data out in datastream mode
    // datastream_mode_service();
}

void typeHIDKey(const KeyMapEntry_t *entry) {
    switch (entry->keyType) {
    case KeyType_t::KEYBOARD:
        // Keyboard.write(KeyboardKeycode(entry->keycode.keyboard));
        keyboard_device.add_key(entry->keycode.keyboard);
        keyboard_device.hid_keyboard_service(usb_hid, RID_KEYBOARD);
        keyboard_device.remove_key(entry->keycode.keyboard);
        break;
    case KeyType_t::CONSUMER:
        consumer_device.consumer_press_and_release_key(entry->keycode.consumer);
        break;
    case KeyType_t::MOUSE:
        // Unsupported for now
        break;
    default:
        break;
    }
}

void pressHIDKey(const KeyMapEntry_t *entry) {
    switch (entry->keyType) {
    case KeyType_t::KEYBOARD:
        keyboard_device.add_key(entry->keycode.keyboard);
        break;
    case KeyType_t::CONSUMER:
        // None, only type supported
        break;
    case KeyType_t::MOUSE:
        // Unsupported for now
        break;
    default:
        break;
    }
}

void releaseHIDKey(const KeyMapEntry_t *entry) {
    switch (entry->keyType) {
    case KeyType_t::KEYBOARD:
        // if (!keyboard_device.isPressed(entry->keycode.keyboard)) {
        keyboard_device.remove_key(entry->keycode.keyboard);
        // }
        break;
    case KeyType_t::CONSUMER:
        // None, only type supported
        break;
    case KeyType_t::MOUSE:
        // Unsupported for now
        break;
    default:
        break;
    }
}

void rgb_light_service(uint64_t curr_time_us) {
    if (curr_time_us - last_blink_time_us > blink_period_us) {
        last_blink_time_us = curr_time_us;

        // if (TinyUSBDevice.mounted()) {
        //     // rgb_leds.set_state(RGBState::CONNECTED);
        // } else {
        //     // rgb_leds.set_state(storage_vars.rgbSettings.connectedState);
        //     // rgb_leds.set_state(RGBState::DISCONNECTED);
        // }

        rgb_leds.loop_service();
    }
}

bool is_digital_key(uint32_t key_id) { return key_id <= 1; }

bool is_analog_key(uint32_t key_id) { return 2 <= key_id && key_id <= 4; }

bool is_encoder_key(uint32_t key_id) { return 5 <= key_id && key_id <= 6; }

bool key_has_lighting(uint32_t key_id) { return key_id <= 4; }

uint32_t key_id_to_analog_key_index(uint32_t key_id) { return (key_id - 2); }

uint32_t key_id_to_digital_key_index(uint32_t key_id) { return key_id; }

bool saveFlashStorage(const StorageVars_t *_storage_vars) {

    // Write to Flash
    EEPROM.put(storedAddress, WRITTEN_SIGNATURE);
    EEPROM.put(storedAddress + sizeof(WRITTEN_SIGNATURE), *_storage_vars);

    // if (!EEPROM.getCommitASAP()) {
    //     Serial.printf("CommitASAP not set. Need commit()");
    EEPROM.commit();
    // }

    return false;
}

void fillDefaultStorageVars(StorageVars_t *_storage_vars) {

    // Set Default keymap
    _storage_vars->keymap[0] = {
        .keycode = {HID_KEY_A},
        .keyType = KeyType_t::KEYBOARD,
    };
    _storage_vars->keymap[1] = {
        .keycode = {HID_KEY_S},
        .keyType = KeyType_t::KEYBOARD,
    };
    _storage_vars->keymap[2] = {
        .keycode = {HID_KEY_Z},
        .keyType = KeyType_t::KEYBOARD,
    };
    _storage_vars->keymap[3] = {
        .keycode = {HID_KEY_X},
        .keyType = KeyType_t::KEYBOARD,
    };
    _storage_vars->keymap[4] = {
        .keycode = {HID_KEY_C},
        .keyType = KeyType_t::KEYBOARD,
    };
    _storage_vars->keymap[5] = {
        .keycode = {HID_USAGE_CONSUMER_VOLUME_INCREMENT},
        .keyType = KeyType_t::CONSUMER,
    };
    _storage_vars->keymap[6] = {
        .keycode = {HID_USAGE_CONSUMER_VOLUME_DECREMENT},
        .keyType = KeyType_t::CONSUMER,
    };

    // Set Default Key Settings
    for (auto &digitalSetting : _storage_vars->digitalSettings) {
        digitalSetting = {
            .debounce_press_ms = 1,
            .debounce_release_ms = 10,
        };
    }

    for (auto &analogSetting : _storage_vars->analogSettings) {
        analogSetting = {
            .rapid_trigger_enable = true,
            .press_hysteresis_mm = FLOAT_TO_Q22_10(0.2),
            .release_hysteresis_mm = FLOAT_TO_Q22_10(0.2),
            .actuation_point_mm = FLOAT_TO_Q22_10(2.5),
            .release_point_mm = FLOAT_TO_Q22_10(5.5),
            .press_debounce_ms = 1,
            .release_debounce_ms = 6,
            .samples = 22,
            .calibration_up_adc = INT_TO_Q22_10(1650),
            .calibration_down_adc = INT_TO_Q22_10(1100),
        };
    }

    // Set Default Per-Key Lighting Settings
    for (auto &keyLightingSettings : _storage_vars->lightingSettings) {
        keyLightingSettings = {
            .mode = LIGHTING_MODE_FADE,
            .brightness = DUTY_CYCLE_ON,
            .duration_us = 20 * 1000,
        };
    };

    // Set RGB
    _storage_vars->rgbSettings = {
        .mode = RGBMode::RAINBOW,
        .color_1 = CRGB::Red,
        .color_2 = CRGB::Green,
        .color_3 = CRGB::Blue,
        .brightness = 255u,
        .speed_bpm = 20.0,
    };
}

/**
 * @brief Loads flash storage settings. If flash doesn't exist, returns the
 * default settings.
 *
 * @param storage_vars
 * @return true
 * @return false
 */
bool loadFlashStorage(StorageVars_t *_storage_vars) {

    // Check if flash has been written before
    int signature;
    EEPROM.get(storedAddress, signature);
    if (signature == WRITTEN_SIGNATURE) {
        // Flash has already been written
        // Read from flash and load to storage_vars

        StorageVars_t retrievedStorageVars;
        EEPROM.get(storedAddress + sizeof(signature), *_storage_vars);
        // memcpy(_storage_vars, &retrievedStorageVars, sizeof(retrievedStorageVars));
        return true;
    }

    // Flash has not been written yet, set default values
    fillDefaultStorageVars(_storage_vars);

    // Write to Flash
    saveFlashStorage(_storage_vars);

    return false;
}

void send_error_response_message(const char *error_string) {
    StaticJsonDocument<256> error_msg;
    error_msg["error"] = error_string;
    serializeJson(error_msg, Serial);
}

/**
 * @brief Datastream mode service function, called periodically in main loop
 *
 */
void datastream_mode_service() {
    // TODO implmement this

    if (datastream_period_ms > 0) {
        uint32_t curr_time_ms = millis();
        if (curr_time_ms - last_datatream_time_ms >= datastream_period_ms) {
            last_datatream_time_ms = curr_time_ms;
            // Serial.write("");
        }
    }
}

/**
 * @brief Reads and processes incoming commands
 *
 */
void read_serial() {

    if (!Serial.available()) {
        return;
    }

    // Try to deserialize from Serial stream
    DeserializationError error = deserializeJson(request_msg, Serial);

    // Detect Deserialize error
    if (error) {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.c_str());

        // Flush incoming buffer
        while (Serial.available()) {
            Serial.read();
        }
        return;
    }

    // Try to get command
    const char *cmd = request_msg["cmd"];
    if (cmd == nullptr) {
        Serial.println(F("No cmd key found"));
    }

    // Release all keys if message deals with keymap
    if (request_msg.containsKey("k_t") || request_msg.containsKey("k_c")) {
        // Keyboard.releaseAll();
        // Consumer.releaseAll();
    }

    response_msg.clear();

    // Get Token if any
    unsigned int token = 0;
    if (request_msg.containsKey("tkn")) {
        token = request_msg["tkn"].as<unsigned int>();
    }

    // w: Write command
    if (strcmp(cmd, "w") == 0) {

        response_msg["cmd"] = "W";

        if (request_msg.containsKey("key")) {
            uint32_t key_id = request_msg["key"].as<unsigned int>();

            // Keymap
            if (request_msg.containsKey("k_t")) {
                storage_vars.keymap[key_id].keyType = static_cast<KeyType_t>(request_msg["k_t"].as<unsigned int>());
            }
            if (request_msg.containsKey("k_c")) {
                storage_vars.keymap[key_id].keycode.value =
                    static_cast<uint16_t>(request_msg["k_c"].as<unsigned int>());
            }

            if (is_analog_key(key_id)) {
                // Handle analog key settings
                uint32_t analog_key_id = key_id_to_analog_key_index(key_id);
                AnalogSwitchSettings_t *currAnalogSettings = &(storage_vars.analogSettings[analog_key_id]);
                if (request_msg.containsKey("rt")) {
                    currAnalogSettings->rapid_trigger_enable = request_msg["rt"].as<bool>();
                }
                if (request_msg.containsKey("h_a")) {
                    currAnalogSettings->press_hysteresis_mm = FLOAT_TO_Q22_10(request_msg["h_a"].as<float>());
                }
                if (request_msg.containsKey("h_r")) {
                    currAnalogSettings->release_hysteresis_mm = FLOAT_TO_Q22_10(request_msg["h_r"].as<float>());
                }
                if (request_msg.containsKey("p_a")) {
                    currAnalogSettings->actuation_point_mm = FLOAT_TO_Q22_10(request_msg["p_a"].as<float>());
                }
                if (request_msg.containsKey("p_r")) {
                    currAnalogSettings->release_point_mm = FLOAT_TO_Q22_10(request_msg["p_r"].as<float>());
                }
                if (request_msg.containsKey("d_a")) {
                    currAnalogSettings->press_debounce_ms = request_msg["d_a"].as<unsigned int>();
                }
                if (request_msg.containsKey("d_r")) {
                    currAnalogSettings->release_debounce_ms = request_msg["d_r"].as<unsigned int>();
                }
                if (request_msg.containsKey("c_u")) {
                    currAnalogSettings->calibration_up_adc = FLOAT_TO_Q22_10(request_msg["c_u"].as<float>());
                }
                if (request_msg.containsKey("c_d")) {
                    currAnalogSettings->calibration_down_adc = FLOAT_TO_Q22_10(request_msg["c_d"].as<float>());
                }
                if (request_msg.containsKey("a_s")) {
                    currAnalogSettings->samples = request_msg["a_s"].as<unsigned int>();
                }

                // Apply new settings to key
                analogKeys[analog_key_id].applySettings(currAnalogSettings);

            } else if (is_digital_key(key_id)) {
                // Handle digital key settings
                uint32_t digital_key_id = key_id_to_digital_key_index(key_id);
                DigitalSwitchSettings_t *currDigitalSettings = &(storage_vars.digitalSettings[digital_key_id]);

                if (request_msg.containsKey("d_a")) {
                    currDigitalSettings->debounce_press_ms = request_msg["d_a"].as<unsigned int>();
                }
                if (request_msg.containsKey("d_r")) {
                    currDigitalSettings->debounce_release_ms = request_msg["d_r"].as<unsigned int>();
                }

                // Apply new settings to key
                digitalKeys[digital_key_id].applySettings(currDigitalSettings);
            } else if (is_encoder_key(key_id)) {
                // Handle encoder key settings
                // No encoder settings for now
            } else {
                send_error_response_message("INVALID_KEY_ID");
                return;
            }

            if (key_has_lighting(key_id)) {
                if (request_msg.containsKey("l_m")) {
                    storage_vars.lightingSettings[key_id].mode = LightingMode(request_msg["l_m"].as<unsigned int>());
                }
                if (request_msg.containsKey("l_b")) {
                    storage_vars.lightingSettings[key_id].brightness =
                        static_cast<uint8_t>(request_msg["l_b"].as<unsigned int>());
                }
                if (request_msg.containsKey("l_d")) {
                    storage_vars.lightingSettings[key_id].duration_us = request_msg["l_d"].as<unsigned int>();
                }
                keyLighting[key_id].applySettings(storage_vars.lightingSettings[key_id]);
            }
        }

        if (request_msg.containsKey("debug")) {
            uint32_t debug_mode_freq_hz = request_msg["debug"].as<unsigned int>();

            printf("debug mode freq: %d hz\n", (int)(debug_mode_freq_hz));
            if (debug_mode_freq_hz == 0) {
                debug_mode = false;
                mainloop_period_us = HZ_TO_PERIOD_US(normal_mode_freq_hz);
            } else {
                debug_mode = true;
                mainloop_period_us = HZ_TO_PERIOD_US(debug_mode_freq_hz);
            }
        }

        // Set datastream mode
        if (request_msg.containsKey("dstrm")) {
            datastream_period_ms = request_msg["dstrm"].as<unsigned int>();
        }

        // RGB Lighting settings
        if (request_msg.containsKey("rgb_m")) {
            storage_vars.rgbSettings.mode = static_cast<RGBMode>(request_msg["rgb_m"].as<unsigned int>());
            rgb_leds.new_mode();
        }
        if (request_msg.containsKey("rgb_b")) {
            storage_vars.rgbSettings.brightness = request_msg["rgb_b"].as<unsigned int>();
            rgb_leds.new_mode();
        }
        if (request_msg.containsKey("rgb_c1")) {
            storage_vars.rgbSettings.color_1 = request_msg["rgb_c1"].as<unsigned int>();
            rgb_leds.new_mode();
        }
        if (request_msg.containsKey("rgb_c2")) {
            storage_vars.rgbSettings.color_2 = request_msg["rgb_c2"].as<unsigned int>();
            rgb_leds.new_mode();
        }
        if (request_msg.containsKey("rgb_c3")) {
            storage_vars.rgbSettings.color_3 = request_msg["rgb_c3"].as<unsigned int>();
            rgb_leds.new_mode();
        }
        if (request_msg.containsKey("rgb_s")) {
            storage_vars.rgbSettings.speed_bpm = request_msg["rgb_s"].as<float>();
            rgb_leds.new_mode();
        }

        // Clear Flash Memory datastream mode
        if (request_msg.containsKey("clear")) {
            if (request_msg["clear"].as<unsigned int>() == 1234u) {
                fillDefaultStorageVars(&storage_vars);
                response_msg["clear"] = "OK";
            }
        }

        saveFlashStorage(&storage_vars);
    }

    // r: Read command
    else if (strcmp(cmd, "r") == 0) {
        response_msg["cmd"] = "r";

        if (request_msg.containsKey("key")) {
            uint32_t key_id = request_msg["key"].as<unsigned int>();
            response_msg["key"] = key_id;
            if (request_msg.containsKey("k_t")) {
                response_msg["k_t"] = static_cast<unsigned int>(storage_vars.keymap[key_id].keyType);
            }
            if (request_msg.containsKey("k_c")) {
                response_msg["k_c"] = static_cast<unsigned int>(storage_vars.keymap[key_id].keycode.value);
            }
            if (is_analog_key(key_id)) {
                // Handle analog keys
                // This repeated code is not great...
                uint32_t analog_key_id = key_id_to_analog_key_index(key_id);
                const AnalogSwitchSettings_t *currAnalogSettings = &(storage_vars.analogSettings[analog_key_id]);
                if (request_msg.containsKey("rt")) {
                    response_msg["rt"] = currAnalogSettings->rapid_trigger_enable;
                }
                if (request_msg.containsKey("h_a")) {
                    response_msg["h_a"] = Q22_10_TO_FLOAT(currAnalogSettings->press_hysteresis_mm);
                }
                if (request_msg.containsKey("h_r")) {
                    response_msg["h_r"] = Q22_10_TO_FLOAT(currAnalogSettings->release_hysteresis_mm);
                }
                if (request_msg.containsKey("p_a")) {
                    response_msg["p_a"] = Q22_10_TO_FLOAT(currAnalogSettings->actuation_point_mm);
                }
                if (request_msg.containsKey("p_r")) {
                    response_msg["p_r"] = Q22_10_TO_FLOAT(currAnalogSettings->release_point_mm);
                }
                if (request_msg.containsKey("d_a")) {
                    response_msg["d_a"] = currAnalogSettings->press_debounce_ms;
                }
                if (request_msg.containsKey("d_r")) {
                    response_msg["d_r"] = currAnalogSettings->release_debounce_ms;
                }
                if (request_msg.containsKey("c_u")) {
                    response_msg["c_u"] = Q22_10_TO_FLOAT(currAnalogSettings->calibration_up_adc);
                }
                if (request_msg.containsKey("c_d")) {
                    response_msg["c_d"] = Q22_10_TO_FLOAT(currAnalogSettings->calibration_down_adc);
                }
                if (request_msg.containsKey("a_s")) {
                    response_msg["a_s"] = currAnalogSettings->samples;
                }
                if (request_msg.containsKey("adc")) {
                    response_msg["adc"] = Q22_10_TO_FLOAT(analogKeys[analog_key_id].current_reading);
                }
                if (request_msg.containsKey("ht")) {
                    response_msg["ht"] = Q22_10_TO_FLOAT(analogKeys[analog_key_id].current_height_mm);
                }
            } else if (is_digital_key(key_id)) {
                // Handle digital keys
                uint32_t digital_key_id = key_id_to_digital_key_index(key_id);
                const DigitalSwitchSettings_t *currDigitalSettings = &(storage_vars.digitalSettings[digital_key_id]);
                if (request_msg.containsKey("d_a")) {
                    response_msg["d_a"] = currDigitalSettings->debounce_press_ms;
                }
                if (request_msg.containsKey("d_r")) {
                    response_msg["d_r"] = currDigitalSettings->debounce_release_ms;
                }
            } else if (is_encoder_key(key_id)) {
                // Handle encoder key settings
                // No encoder settings for now
            } else {
                send_error_response_message("INVALID_KEY_ID");
                return;
            }

            if (key_has_lighting(key_id)) {
                if (request_msg.containsKey("l_m")) {
                    response_msg["l_m"] = keyLighting[key_id].settings.mode;
                }
                if (request_msg.containsKey("l_b")) {
                    response_msg["l_b"] = keyLighting[key_id].settings.brightness;
                }
                if (request_msg.containsKey("l_d")) {
                    response_msg["l_d"] = keyLighting[key_id].settings.duration_us;
                }
            }
        }

        if (request_msg.containsKey("rgb_m")) {
            response_msg["rgb_m"] = static_cast<uint8_t>(storage_vars.rgbSettings.mode);
        }
        if (request_msg.containsKey("rgb_b")) {
            response_msg["rgb_b"] = static_cast<uint8_t>(storage_vars.rgbSettings.brightness);
        }
        if (request_msg.containsKey("rgb_c1")) {
            response_msg["rgb_c1"] = storage_vars.rgbSettings.color_1;
        }
        if (request_msg.containsKey("rgb_c2")) {
            response_msg["rgb_c2"] = storage_vars.rgbSettings.color_2;
        }
        if (request_msg.containsKey("rgb_c3")) {
            response_msg["rgb_c3"] = storage_vars.rgbSettings.color_3;
        }
        if (request_msg.containsKey("rgb_s")) {
            response_msg["rgb_s"] = storage_vars.rgbSettings.speed_bpm;
        }

    }

    // V: Get Version
    else if (strcmp(cmd, "v") == 0) {

        response_msg["cmd"] = "v";

        response_msg["V"] = VERSION;
    } else {
        printf("Invalid cmd: %s", cmd);
    }

    // Add token if there was one and it wasn't zero
    if (token != 0) {
        response_msg["tkn"] = token;
    }

    // Send response message
    serializeJson(response_msg, Serial);
}
