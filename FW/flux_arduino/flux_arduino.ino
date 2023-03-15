#define HID_CUSTOM_LAYOUT
#define LAYOUT_US_ENGLISH
// #define ENCODER_OPTIMIZE_INTERRUPTS

#include "AnalogSwitch.h"
#include "DigitalSwitch.h"
#include "KeyLighting.h"
#include <ArduinoJson.h>

#include <EncoderTool.h>
#include <FlashStorage_SAMD.h>
#include <HID-Project.h>
#include <HID-Settings.h>

#define HZ_TO_PERIOD_US(x) (1000000 / (x))

#define VERSION 1

#define ENC_A_PIN 1u
#define ENC_B_PIN 0u
#define KEY0_PIN 4u
#define KEY1_PIN 9u
#define KEY2_PIN 6u
#define KEY3_PIN 8u

#define KEY0_LIGHT_PIN 3u
#define KEY1_LIGHT_PIN 7u
#define KEY2_LIGHT_PIN 5u
#define KEY3_LIGHT_PIN 10u

#define ENC_UP_KEY_ID 4u
#define ENC_DOWN_KEY_ID 5u

#define LED_PIN 13u

bool debug_mode = false;

const uint32_t normal_mode_freq_hz = 1000;
uint32_t mainloop_period_us = HZ_TO_PERIOD_US(normal_mode_freq_hz);

uint32_t loop_count = 0;
uint32_t last_print_us = 0;
uint32_t print_period_us = 2 * 1000 * 1000;

unsigned long last_time_us;

const int WRITTEN_SIGNATURE = 0xABCDEF01;
const uint16_t storedAddress = 0;

enum class KeyType_t {
    NONE = 0,
    KEYBOARD = 1,
    CONSUMER = 2,
    MOUSE = 3
};

typedef struct {
    union keycode {
        uint8_t keyboard;
        uint16_t consumer;
        uint16_t value;
    } keycode = {};
    KeyType_t keyType;
} KeyMapEntry_t;

typedef struct {
    KeyMapEntry_t keymap[6];

    AnalogSwitchSettings_t analogSettings[2];
    DigitalSwitchSettings_t digitalSettings[2];

    KeyLightingSettings_t lightingSettings[4];

    uint64_t first_write_timestamp = 0;
    uint64_t last_write_timestamp = 0;
} StorageVars_t;

StorageVars_t storage_vars;

EncoderTool::PolledEncoder encoder;

DigitalSwitch digitalKeys[] = {
    DigitalSwitch(KEY0_PIN, 0),
    DigitalSwitch(KEY1_PIN, 1),
};

AnalogSwitch analogKeys[] = {
    AnalogSwitch(KEY2_PIN, 2),
    AnalogSwitch(KEY3_PIN, 3),
};

KeyLighting keyLighting[] = {
    KeyLighting(KEY0_LIGHT_PIN, &(digitalKeys[0].is_pressed)),
    KeyLighting(KEY1_LIGHT_PIN, &(digitalKeys[1].is_pressed)),
    KeyLighting(KEY2_LIGHT_PIN, &(analogKeys[0].is_pressed)),
    KeyLighting(KEY3_LIGHT_PIN, &(analogKeys[1].is_pressed)),
};

StaticJsonDocument<1024> json_doc_incoming;
StaticJsonDocument<1024> json_doc_outgoing;

void setup() {

    // DISABLE UART RX TX LEDS
    pinMode(PIN_LED2, INPUT_PULLUP);
    pinMode(PIN_LED3, INPUT_PULLUP);

    analogReadResolution(12);

    Serial.setTimeout(100);
    Serial.begin(115200);
    Keyboard.begin();
    Consumer.begin();

    encoder.begin(ENC_A_PIN, ENC_B_PIN, EncoderTool::CountMode::quarter,
                  INPUT_PULLUP);

    loadFlashStorage(&storage_vars);

    for (size_t i=0; i < sizeof(digitalKeys)/sizeof(digitalKeys[0]); i++){
        digitalKeys[i].setup();
        digitalKeys[i].applySettings(&(storage_vars.digitalSettings[i]));
    }

    for (size_t i=0; i < sizeof(analogKeys)/sizeof(analogKeys[0]); i++){
        analogKeys[i].setup();
        analogKeys[i].applySettings(&(storage_vars.analogSettings[i]));
    }

    int i = 0;
    for (KeyLighting &lighting : keyLighting) {
        lighting.setup();
        lighting.applySettings(&(storage_vars.lightingSettings[i]));
        i++;
    }

    pinMode(2, INPUT);

    last_time_us = micros();
}

void loop() {

    uint32_t curr_time_us = micros();
    if (curr_time_us - last_time_us < mainloop_period_us) {
        return;
    }
    last_time_us = curr_time_us;

    loop_count++;

    if (!debug_mode) {
        if (curr_time_us - last_print_us > print_period_us) {
            float loop_freq =
                (static_cast<float>(loop_count) /
                 (static_cast<float>(print_period_us) / 1000000.0f));
            Serial.printf("Loop freq: %f\n", loop_freq);
            loop_count = 0;
            last_print_us += print_period_us;
        }
    }

    Keyboard.removeAll();

    // Scan analog keys
    for (AnalogSwitch &key : analogKeys) {
        key.mainLoopService();
        if (debug_mode) {
            Serial.printf(" (%d) ", key.current_reading);
            Serial.printf("%f %f ", Q22_10_TO_FLOAT(key.current_reading),
                          Q22_10_TO_FLOAT(key.current_distance_mm));
        }

        if (key.is_pressed) {
            pressHIDKey(&(storage_vars.keymap[key.id]));
        }
    }
    if (debug_mode) {
        Serial.printf("\n");
    }

    // Scan digital keys
    for (DigitalSwitch &key : digitalKeys) {
        key.mainLoopService();

        if (key.is_pressed) {
            pressHIDKey(&(storage_vars.keymap[key.id]));
        }
    }

    // Scan Encoder
    encoder.tick();
    if (encoder.valueChanged()) {
        switch (encoder.getValue()) {
        case 1:
            typeHIDKey(storage_vars.keymap[ENC_UP_KEY_ID].keycode.value,
                        storage_vars.keymap[ENC_UP_KEY_ID].keyType);
            break;
        case -1:
            typeHIDKey(storage_vars.keymap[ENC_DOWN_KEY_ID].keycode.value,
                        storage_vars.keymap[ENC_DOWN_KEY_ID].keyType);
            break;
        default:
            break;
        }
        encoder.setValue(0);
    }

    // Run Lighting
    int i = 0;
    for (KeyLighting &lighting : keyLighting) {
        lighting.lightingTask(curr_time_us);
        i++;
    }

    Keyboard.send();
    read_serial();
}

void typeHIDKey(char key, KeyType_t key_type) {
    switch (key_type) {
    case KeyType_t::KEYBOARD:
        Keyboard.write(key);
        break;
    case KeyType_t::CONSUMER:
        Consumer.write(ConsumerKeycode(key));
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
        Keyboard.add(KeyboardKeycode(entry->keycode.keyboard));
        break;
    case KeyType_t::CONSUMER:
        Consumer.press(ConsumerKeycode(entry->keycode.consumer));
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
        Keyboard.remove(KeyboardKeycode(entry->keycode.keyboard));
        break;
    case KeyType_t::CONSUMER:
        Consumer.release(ConsumerKeycode(entry->keycode.consumer));
        break;
    case KeyType_t::MOUSE:
        // Unsupported for now
        break;
    default:
        break;
    }
}

bool is_analog_key(uint32_t key_id){
    return key_id <= 1;
}

bool is_digital_key(uint32_t key_id){
    return 2 <= key_id && key_id <= 3;
}

bool is_encoder_key(uint32_t key_id){
    return 4 <= key_id && key_id <= 5;
}

uint32_t key_id_to_analog_key_index(uint32_t key_id){
    return (key_id - 2);
}

uint32_t key_id_to_digital_key_index(uint32_t key_id){
    return key_id;
}

bool saveFlashStorage(const StorageVars_t *storage_vars) {

    // Write to Flash
    EEPROM.put(storedAddress, WRITTEN_SIGNATURE);
    EEPROM.put(storedAddress + sizeof(int), *storage_vars);

    if (!EEPROM.getCommitASAP()) {
        Serial.printf("CommitASAP not set. Need commit()");
        EEPROM.commit();
    }

    return false;
}

/**
 * @brief Loads flash storage settings. If flash doesn't exist, returns the
 * default settings.
 *
 * @param storage_vars
 * @return true
 * @return false
 */
bool loadFlashStorage(StorageVars_t *storage_vars) {

    // Check if flash has been written before
    int signature;
    EEPROM.get(storedAddress, signature);
    if (signature == WRITTEN_SIGNATURE) {
        // Flash has already been written
        // Read from flash and load to storage_vars

        StorageVars_t retrievedStorageVars;
        EEPROM.get(storedAddress + sizeof(signature), *storage_vars);
        *storage_vars = retrievedStorageVars;
        return true;
    }

    // Flash has not been written yet, set default values

    // Set Default keymap
    storage_vars->keymap[0] = {
        .keycode = {KEY_A},
        .keyType = KeyType_t::KEYBOARD,
    };
    storage_vars->keymap[1] = {
        .keycode = {KEY_S},
        .keyType = KeyType_t::KEYBOARD,
    };
    storage_vars->keymap[2] = {
        .keycode = {KEY_Z},
        .keyType = KeyType_t::KEYBOARD,
    };
    storage_vars->keymap[3] = {
        .keycode = {KEY_X},
        .keyType = KeyType_t::KEYBOARD,
    };
    storage_vars->keymap[4] = {
        .keycode = {HID_CONSUMER_VOLUME_INCREMENT},
        .keyType = KeyType_t::CONSUMER,
    };
    storage_vars->keymap[5] = {
        .keycode = {HID_CONSUMER_VOLUME_DECREMENT},
        .keyType = KeyType_t::CONSUMER,
    };

    // Set Default Key Settings
    for (auto &digitalSetting : storage_vars->digitalSettings) {
        digitalSetting = {
            .debounce_press_ms = 1,
            .debounce_release_ms = 10,
        };
    }

    for (auto &analogSetting : storage_vars->analogSettings) {
        analogSetting = {
            .press_hysteresis_mm = FLOAT_TO_Q22_10(0.3),
            .release_hysteresis_mm = FLOAT_TO_Q22_10(0.3),
            .actuation_point_mm = FLOAT_TO_Q22_10(2.2),
            .release_point_mm = FLOAT_TO_Q22_10(5.8),
            .press_debounce_ms = 0,
            .release_debounce_ms = 0,
            .samples = 22,
            .calibration_up_adc = reference_up_adc,
            .calibration_down_adc = reference_down_adc,
        };
    }

    for (KeyLightingSettings_t &keyLightingSettings :
         storage_vars->lightingSettings) {
        keyLightingSettings = {
            .mode = LIGHTING_MODE_FADE,
            .fade_half_life_us = 20 * 1000,
            .flash_duration_us = 1000 * 1000,
            .static_duty_cycle = 50,
        };
    };

    // Write to Flash
    saveFlashStorage(storage_vars);

    return false;
}

void apply_analog_settings(){

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
    DeserializationError error = deserializeJson(json_doc_incoming, Serial);

    // // Flush incoming buffer
    // while (Serial.available() > 0) {
    //     Serial.read();
    // }

    // Detect Deserialize error
    if (error) {
        Serial.print(F("deserializeJson() failed: "));
        Serial.println(error.c_str());

        // Flush incoming buffer
        while (Serial.available() > 0) {
            Serial.read();
        }
        return;
    }



    // Try to get command
    const char *cmd = json_doc_incoming["cmd"];
    if (cmd == nullptr) {
        Serial.println(F("No cmd key found"));
    }

    // Release all keys
    Keyboard.releaseAll();
    Consumer.releaseAll();

    json_doc_outgoing.clear();

    // W: Write to storage
    if (strcmp(cmd, "w") == 0) {

        json_doc_outgoing["cmd"] = "W";

        if (json_doc_incoming.containsKey("key")){
            uint32_t key_id = json_doc_incoming["key"].as<unsigned int>();

            // Keymap
            if (json_doc_incoming.containsKey("k_t")){
                storage_vars.keymap[key_id].keyType = static_cast<KeyType_t>(json_doc_incoming["k_t"].as<unsigned int>());
            }
            if (json_doc_incoming.containsKey("k_c")){
                storage_vars.keymap[key_id].keycode.value = static_cast<uint16_t>(json_doc_incoming["k_c"].as<unsigned int>());
            }

            // Analog Key Settings

            if (is_analog_key(key_id)){
                uint32_t analog_key_id = key_id_to_analog_key_index(key_id);
                AnalogSwitchSettings_t *currAnalogSettings = &(storage_vars.analogSettings[analog_key_id]);

                if (json_doc_incoming.containsKey("h_a")){
                    currAnalogSettings->press_hysteresis_mm = static_cast<q22_10_t>(json_doc_incoming["h_a"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("h_r")){
                    currAnalogSettings->release_hysteresis_mm = static_cast<q22_10_t>(json_doc_incoming["h_r"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("p_a")){
                    currAnalogSettings->actuation_point_mm = static_cast<q22_10_t>(json_doc_incoming["p_a"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("p_r")){
                    currAnalogSettings->release_point_mm = static_cast<q22_10_t>(json_doc_incoming["p_r"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("d_a")){
                    currAnalogSettings->press_debounce_ms = static_cast<uint32_t>(json_doc_incoming["d_a"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("d_r")){
                    currAnalogSettings->release_debounce_ms = static_cast<uint32_t>(json_doc_incoming["d_r"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("c_u")){
                    currAnalogSettings->calibration_up_adc = static_cast<q22_10_t>(json_doc_incoming["c_u"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("c_d")){
                    currAnalogSettings->calibration_down_adc = static_cast<q22_10_t>(json_doc_incoming["c_d"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("s")){
                    currAnalogSettings->samples = static_cast<q22_10_t>(json_doc_incoming["s"].as<unsigned int>());
                }
                analogKeys[analog_key_id].applySettings(currAnalogSettings);
                
            } else if (is_digital_key(key_id))
            {
                uint32_t digital_key_id = key_id_to_analog_key_index(key_id);
                DigitalSwitchSettings_t *currDigitalSettings = &(storage_vars.digitalSettings[digital_key_id]);
                if (json_doc_incoming.containsKey("d_a")){
                    currDigitalSettings->debounce_press_ms = static_cast<uint32_t>(json_doc_incoming["d_a"].as<unsigned int>());
                }
                if (json_doc_incoming.containsKey("d_r")){
                    currDigitalSettings->debounce_release_ms = static_cast<uint32_t>(json_doc_incoming["d_r"].as<unsigned int>());
                }

                digitalKeys[digital_key_id].applySettings(currDigitalSettings);
            } else {
                json_doc_outgoing["error"] = F("INVALID_KEY_ID");
            }
        }

        // if (json_doc_incoming.containsKey("map")) {
        //     JsonArray array = json_doc_incoming["map"].as<JsonArray>();
        //     for (auto entry : array) {
        //         if (entry.containsKey("id") && entry.containsKey("code") &&
        //             entry.containsKey("type")) {
        //             uint32_t id = entry["id"].as<unsigned int>();
        //             uint32_t code = entry["code"].as<int>();
        //             uint32_t type = entry["type"].as<unsigned int>();

        //             storage_vars.keymap[id].keycode.value = static_cast<uint16_t>(code);
        //             storage_vars.keymap[id].keyType =
        //                 static_cast<KeyType_t>(type);

        //             Serial.printf("Set id %d to code %d type %d", id,
        //                           storage_vars.keymap[id].keycode,
        //                           storage_vars.keymap[id].keyType);
        //         }
        //     }
        // }

        // // Digital key settings
        // if (json_doc_incoming.containsKey("d_s")) {
        //     JsonObject digital_settings =
        //         json_doc_incoming["d_s"].as<JsonObject>();
        //     if (digital_settings.containsKey("t_p")) {
        //         storage_vars.digitalSettings.debounce_press_ms =
        //             digital_settings["t_p"].as<int32_t>();
        //     }
        //     if (digital_settings.containsKey("t_r")) {
        //         storage_vars.digitalSettings.debounce_release_ms =
        //             digital_settings["t_r"].as<int32_t>();
        //     }

        //     // Apply settings
        //     for (DigitalSwitch &key : digitalKeys) {
        //         key.applySettings(&(storage_vars.digitalSettings));
        //     }
        // }

        // Analog key settings
        // if (json_doc_incoming.containsKey("a_s")) {
        //     Serial.printf("a_s\n");
        //     JsonObject analog_settings =
        //         json_doc_incoming["a_s"].as<JsonObject>();
        //     if (analog_settings.containsKey("h_a")) {
        //         storage_vars.analogSettings.press_hysteresis_mm =
        //             FLOAT_TO_Q22_10(analog_settings["h_a"].as<float>());
        //     }
        //     if (analog_settings.containsKey("h_r")) {
        //         storage_vars.analogSettings.release_hysteresis_mm =
        //             FLOAT_TO_Q22_10(analog_settings["h_r"].as<float>());
        //     }
        //     if (analog_settings.containsKey("p_a")) {
        //         storage_vars.analogSettings.actuation_point_mm =
        //             FLOAT_TO_Q22_10(analog_settings["p_a"].as<float>());
        //     }
        //     if (analog_settings.containsKey("p_r")) {
        //         storage_vars.analogSettings.release_point_mm =
        //             FLOAT_TO_Q22_10(analog_settings["p_r"].as<float>());
        //     }
        //     if (analog_settings.containsKey("s")) {
        //         storage_vars.analogSettings.samples =
        //             analog_settings["s"].as<uint32_t>();
        //     }
        //     if (analog_settings.containsKey("PRESCALER_DIV")) {
        //         int prescaler_div =
        //             analog_settings["PRESCALER_DIV"].as<uint32_t>();
        //         for (AnalogSwitch &key : analogKeys) {
        //             key.setADCConversionTime(prescaler_div, 0);
        //         }
        //         Serial.printf("PRESCALER_DIV: %d", prescaler_div);
        //     }

        //     if (analog_settings.containsKey("FREERUN")) {
        //         bool use_freerun = analog_settings["FREERUN"].as<uint32_t>();
        //         for (AnalogSwitch &key : analogKeys) {
        //             key.use_freerun_mode = use_freerun;
        //         }
        //         Serial.printf("FREERUN: %d", use_freerun);
        //     }

        //     // Apply settings
        //     for (AnalogSwitch &key : analogKeys) {
        //         key.applySettings(&(storage_vars.analogSettings));
        //     }
        // }

        if (json_doc_incoming.containsKey("debug")) {
            uint32_t debug_mode_freq_hz = json_doc_incoming["debug"].as<unsigned int>();
            Serial.printf("debug mode freq: %d hz\n", debug_mode_freq_hz);
            if (debug_mode_freq_hz == 0) {
                debug_mode = false;
                mainloop_period_us = HZ_TO_PERIOD_US(normal_mode_freq_hz);
            } else {
                debug_mode = true;
                mainloop_period_us = HZ_TO_PERIOD_US(debug_mode_freq_hz);
            }
        }

        saveFlashStorage(&storage_vars);
    }

    // R: Read from storage
    else if (strcmp(cmd, "r") == 0) {
        json_doc_outgoing["cmd"] = "r";

        if (json_doc_incoming.containsKey("key")){
            uint32_t key_id = json_doc_incoming["key"].as<unsigned int>();
            
            json_doc_outgoing["k_t"] = static_cast<unsigned int>(storage_vars.keymap[key_id].keyType);
            json_doc_outgoing["k_c"] = static_cast<unsigned int>(storage_vars.keymap[key_id].keycode.value);

            // JsonArray incoming_array = json_doc_incoming["map"].as<JsonArray>();
            // JsonArray array = json_doc_outgoing.createNestedArray("map");
            // for (auto incoming_entry : incoming_array) {
            //     if (incoming_entry.containsKey("id")) {
            //         uint32_t id = incoming_entry["id"].as<unsigned int>();

            //         Serial.printf("id: %d \n", id);

            //         JsonObject object = array.createNestedObject();
            //         object["code"] = static_cast<unsigned int>(
            //             storage_vars.keymap[id].keycode.value);
            //         object["type"] = static_cast<unsigned int>(
            //             storage_vars.keymap[id].keyType);
            //     }
            // }
        }

        if (json_doc_incoming.containsKey("adc")) {
            JsonObject adc_object = json_doc_outgoing.createNestedObject("adc");
            GCLK->CLKCTRL.bit.ID =
                static_cast<uint8_t>(GCLK_CLKCTRL_ID_ADC_Val);
            while (GCLK->STATUS.bit.SYNCBUSY)
                ;
            adc_object["GCLK"] = static_cast<unsigned int>(
                GCLK->CLKCTRL.reg); // 01 00 0000 00 011110
            adc_object["CTRLA"] = static_cast<unsigned int>(ADC->CTRLA.reg);
            adc_object["CTRLB"] = static_cast<unsigned int>(ADC->CTRLB.reg);
            adc_object["AVGCTRL"] = static_cast<unsigned int>(ADC->AVGCTRL.reg);
            adc_object["SAMPCTRL"] =
                static_cast<unsigned int>(ADC->SAMPCTRL.reg);
            adc_object["GAINCORR"] =
                static_cast<unsigned int>(ADC->GAINCORR.reg);
            adc_object["OFFSETCORR"] =
                static_cast<unsigned int>(ADC->OFFSETCORR.reg);
        }
    }

    // V: Get Version
    else if (strcmp(cmd, "v") == 0) {

        json_doc_outgoing["cmd"] = "v";

        json_doc_outgoing["V"] = VERSION;
    } else {
        Serial.printf("Invalid cmd: %s", cmd);
    }

    // Reply with json doc
    serializeJson(json_doc_outgoing, Serial);
}
