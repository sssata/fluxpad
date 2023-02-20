#include "AnalogSwitch.h"
#include "DigitalSwitch.h"
#include "KeyTypes.h"
#include <ArduinoJson.h>
#include <Encoder.h>
#include <FlashStorage_SAMD.h>
#include <HID-Project.h>
#include <HID-Settings.h>

#define VERSION 1

#define SAMPLE_FREQ_HZ 1000
#define SAMPLE_PERIOD_US 1000000 / SAMPLE_FREQ_HZ

#define KEY0_PIN 3
#define KEY1_PIN 9
#define KEY2_PIN 6
#define KEY3_PIN 8

#define LED_PIN 13

#define FIR_NUM_TAPS 32

uint32_t loop_count = 0;
uint64_t last_print_us = 0;
uint64_t print_period_us = 2*1000*1000;

unsigned long last_time_us;

const int WRITTEN_SIGNATURE = 0xABCDEF01;
uint16_t storedAddress = 0;

typedef struct {
    char keycode;
    KeyType_t keyType;
} KeyMapEntry_t;

typedef struct {
    KeyMapEntry_t keymap[4];

    AnalogSwitchSettings_t analogSettings;
    DigitalSwitchSettings_t digitalSettings;

    uint64_t first_write_timestamp = 0;
    uint64_t last_write_timestamp = 0;
} StorageVars_t;

StorageVars_t storage_vars;

DigitalSwitch digitalKeys[] = {
    DigitalSwitch(KEY0_PIN, 0),
    DigitalSwitch(KEY1_PIN, 1),
};

AnalogSwitch analogKeys[] = {
    AnalogSwitch(KEY2_PIN, 2),
    AnalogSwitch(KEY3_PIN, 3),
};

StaticJsonDocument<512> json_doc_incoming;
StaticJsonDocument<512> json_doc_outgoing;

void setup() {
    // put your setup code here, to run once:
    Serial.setTimeout(100);
    Serial.begin(115200);
    analogReadResolution(12);
    NKROKeyboard.begin();
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(PIN_LED2, INPUT_PULLUP);  // DISABLED
    pinMode(PIN_LED3, INPUT_PULLUP);

    loadFlashStorage(&storage_vars);

    for (DigitalSwitch &key : digitalKeys) {
        key.setup();
        key.applySettings(&(storage_vars.digitalSettings));
    }

    for (AnalogSwitch &key : analogKeys) {
        key.setup();
        key.applySettings(&(storage_vars.analogSettings));
    }

    last_time_us = micros();
}

void loop() {

    uint32_t curr_time_us = micros();
    if (curr_time_us - last_time_us < SAMPLE_PERIOD_US) {
        return;
    }
    last_time_us = curr_time_us;

    loop_count ++;
    if (curr_time_us - last_print_us > print_period_us){
        float loop_freq = (loop_count/(print_period_us/1000000.0));
        Serial.printf("Loop freq: %f\n", loop_freq);
        loop_count = 0;
        last_print_us += print_period_us;
    }


    // Scan analog keys
    for (AnalogSwitch &key : analogKeys) {
        key.mainLoopService();
        // Serial.printf("%f ", Q22_10_TO_FLOAT(key.current_reading));

        if (key.is_pressed) {
            NKROKeyboard.add(storage_vars.keymap[key.id].keycode);
        } else {
            NKROKeyboard.remove(storage_vars.keymap[key.id].keycode);
        }
    }
    // Serial.printf("\n");

    if (analogKeys[1].is_pressed){
        digitalWrite(LED_PIN, LOW);
    } else{
        digitalWrite(LED_PIN, HIGH);
    }

    // Scan digital keys
    for (auto key : digitalKeys) {
        key.mainLoopService();

        if (key.is_pressed) {
            NKROKeyboard.add(
                KeyboardKeycode(storage_vars.keymap[key.id].keycode));
        } else {
            NKROKeyboard.remove(
                KeyboardKeycode(storage_vars.keymap[key.id].keycode));
        }
    }
    // Keyboard.send();
    NKROKeyboard.send();
    read_serial();
    // Serial.printf("\n");
}

bool saveFlashStorage(StorageVars_t storage_vars) {

    // Write to Flash
    EEPROM.put(storedAddress, WRITTEN_SIGNATURE);
    EEPROM.put(storedAddress + sizeof(int), storage_vars);

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
        storage_vars = &retrievedStorageVars;
        return true;
    }

    // Flash has not been written yet, set default values

    // Set Default keymap
    storage_vars->keymap[0] = {
        .keycode = 'a',
        .keyType = KEY_TYPE_KEYBOARD,
    };
    storage_vars->keymap[1] = {
        .keycode = 's',
        .keyType = KEY_TYPE_KEYBOARD,
    };
    storage_vars->keymap[2] = {
        .keycode = 'z',
        .keyType = KEY_TYPE_KEYBOARD,
    };
    storage_vars->keymap[3] = {
        .keycode = 'x',
        .keyType = KEY_TYPE_KEYBOARD,
    };

    // Set Default Key Settings
    storage_vars->digitalSettings = {
        .debounce_press_ms = 1,
        .debounce_release_ms = 10,
    };
    storage_vars->analogSettings = {
        .press_hysteresis = INT_TO_Q22_10(100),
        .release_hysteresis = INT_TO_Q22_10(100),
        .actuation_point = INT_TO_Q22_10(500),
        .release_point = INT_TO_Q22_10(400),
        .samples = 20,
    };

    // Write to Flash
    // saveFlashStorage(*storage_vars);

    return false;
}

/**
 * @brief Reads and processes incoming commands
 * 
 */
void read_serial() {

    if (!Serial.available()){
        return;
    }

    // Try to deserialize from Serial stream
    DeserializationError error = deserializeJson(json_doc_incoming, Serial);

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

    json_doc_outgoing.clear();

    // Parse command (unfortunately can't use switch/case because string comp)
    // W: Write to storage
    if (strcmp(cmd, "W") == 0) {

        json_doc_outgoing["cmd"] = "W";

        if (json_doc_incoming.containsKey("map")) {
            JsonArray array = json_doc_incoming["map"].as<JsonArray>();
            for (auto entry : array) {
                if (entry.containsKey("id") && entry.containsKey("code") &&
                    entry.containsKey("type")) {
                    uint32_t id = entry["id"].as<unsigned int>();
                    uint32_t code = entry["code"].as<int>();
                    uint32_t type = entry["type"].as<unsigned int>();

                    storage_vars.keymap[id].keycode = code;
                    storage_vars.keymap[id].keyType =
                        static_cast<KeyType_t>(type);

                    Serial.printf("Set id %d to code %d type %d", id,
                                  storage_vars.keymap[id].keycode,
                                  storage_vars.keymap[id].keyType);
                }
            }
        }

        // Digital key settings
        if (json_doc_incoming.containsKey("d_s")) {
            JsonObject digital_settings= json_doc_incoming["d_s"].as<JsonObject>();
            if (digital_settings.containsKey("t_p")) {
                storage_vars.digitalSettings.debounce_press_ms =
                    digital_settings["t_p"].as<int32_t>();
            }
            if (digital_settings.containsKey("t_r")) {
                storage_vars.digitalSettings.debounce_release_ms =
                    digital_settings["t_r"].as<int32_t>();
            }

            // Apply settings
            for (DigitalSwitch &key : digitalKeys) {
                key.applySettings(&(storage_vars.digitalSettings));
            }
            // if (id >= 1 && id <= 2){
            //     storage_vars.digitalSettings[id];
            // } else if (id >= 3 && id <= 4){
            //     storage_vars.analogSettings[id-2];
            // }
        }

        // Analog key settings
        if (json_doc_incoming.containsKey("a_s")) {
            Serial.printf("a_s\n");
            JsonObject analog_settings= json_doc_incoming["a_s"].as<JsonObject>();
            if (analog_settings.containsKey("t_a")) {
                storage_vars.analogSettings.press_hysteresis =
                    INT_TO_Q22_10(analog_settings["t_a"].as<uint32_t>());
            }
            if (analog_settings.containsKey("t_r")) {
                storage_vars.analogSettings.release_hysteresis =
                    INT_TO_Q22_10(analog_settings["t_r"].as<uint32_t>());
            }
            if (analog_settings.containsKey("s")) {
                storage_vars.analogSettings.samples =
                    analog_settings["s"].as<uint32_t>();
            }
            if (analog_settings.containsKey("PRESCALER_DIV")) {
                int prescaler_div = analog_settings["PRESCALER_DIV"].as<uint32_t>();
                for (AnalogSwitch &key : analogKeys) {
                    key.ADCsetup(prescaler_div, 0);
                }
                Serial.printf("PRESCALER_DIV: %d", prescaler_div);
            }

            if (analog_settings.containsKey("FREERUN")) {
                bool use_freerun = analog_settings["FREERUN"].as<uint32_t>();
                for (AnalogSwitch &key : analogKeys) {
                    key.use_freerun_mode = use_freerun;
                }
                Serial.printf("FREERUN: %d", use_freerun);
            }
            
            // Apply settings
            for (AnalogSwitch &key : analogKeys) {
                key.applySettings(&(storage_vars.analogSettings));
            }
        }

        saveFlashStorage(storage_vars);
    }

    // R: Read from storage
    else if (strcmp(cmd, "R") == 0) {
        json_doc_outgoing["cmd"] = "R";

        if (json_doc_incoming.containsKey("map")) {
            JsonArray array = json_doc_outgoing.createNestedArray("map");
            for (auto entry : array) {
                if (entry.containsKey("id")) {
                    uint32_t id = entry["id"].as<unsigned int>();

                    JsonObject object = array.createNestedObject();
                    object["code"] = static_cast<unsigned int>(
                        storage_vars.keymap[id].keycode);
                    object["type"] = static_cast<unsigned int>(
                        storage_vars.keymap[id].keyType);
                }
            }
        }

        if (json_doc_incoming.containsKey("adc")) {
            JsonObject adc_object = json_doc_outgoing.createNestedObject("adc");
            GCLK->CLKCTRL.bit.ID = static_cast<uint8_t>(GCLK_CLKCTRL_ID_ADC_Val);
            while(GCLK->STATUS.bit.SYNCBUSY);
            adc_object["GCLK"] = static_cast<unsigned int>(GCLK->CLKCTRL.reg);  //01 00 0000 00 011110
            adc_object["CTRLA"] = static_cast<unsigned int>(ADC->CTRLA.reg);
            adc_object["CTRLB"] = static_cast<unsigned int>(ADC->CTRLB.reg);
            adc_object["AVGCTRL"] = static_cast<unsigned int>(ADC->AVGCTRL.reg);
            adc_object["SAMPCTRL"] = static_cast<unsigned int>(ADC->SAMPCTRL.reg);
            adc_object["GAINCORR"] = static_cast<unsigned int>(ADC->GAINCORR.reg);
            adc_object["OFFSETCORR"] = static_cast<unsigned int>(ADC->OFFSETCORR.reg);
        }
    }

    // C: Calibrate
    // else if (strcmp(cmd, "C") == 0) {

    //     // json_doc_outgoing["cmd"] = "C";

    //     // storage_vars.A_0 = sensor_vars.value_a;
    //     // storage_vars.B_0 = sensor_vars.value_b;

    //     // json_doc_outgoing["a0"] = storage_vars.A_0;
    //     // json_doc_outgoing["b0"] = storage_vars.B_0;
    //     saveFlashStorage(storage_vars);
    // }

    // V: Get Version
    else if (strcmp(cmd, "V") == 0) {

        json_doc_outgoing["cmd"] = "V";

        json_doc_outgoing["V"] = VERSION;
    } else {
        Serial.printf("Invalid cmd: %s", cmd);
    }

    // Reply with json doc
    serializeJson(json_doc_outgoing, Serial);
}

// void read_serial() {
//     if (Serial.available()) {
//         DeserializationError err = deserializeJson(json_doc_incoming,
//         Serial1); if (err == DeserializationError::Ok) {
//             // Print the values
//             // (we must use as<T>() to resolve the ambiguity)
//             Serial.print("timestamp = ");
//             Serial.println(json_doc_incoming["timestamp"].as<long>());
//             Serial.print("value = ");
//             Serial.println(json_doc_incoming["value"].as<int>());
//         } else {
//             // Print error to the "debug" serial port
//             Serial.print("deserializeJson() returned ");
//             Serial.println(err.c_str());

//             // Flush all bytes in the "link" serial port buffer
//             while (Serial1.available() > 0)
//                 Serial1.read();
//         }
//     }
// }