# FLUXPAD Serial Communication Protocol

## Summary

The fluxpad exposes a virtual serial port over USB when plugged in to allow communication with the Flux app and other programs on the PC.

Messages to and from the fluxpad is generally serialized in JSON format. No nested objects are permitted, since the `{` and `}` characters function as message start and message end markers.

All communication is initialized by the PC, except for when the fluxpad is in datastream mode.


## Normal Mode

This is used for the majority of communication.
The PC sends a `request message` to the fluxpad, and the fluxpad will reply with a `response message`.

Every request message is either a `write request` or a `read request`. The type of request is denoted by the "cmd" key of the json message.

### Write Request

This message is used to write data to the fluxpad. The value of "cmd" is "w".

Example: Set actuation and release hysteresis of key 2 to 0.2 mm

``` json
{
    "cmd": "w",
    "key": 2,
    "h_a": 0.2,
    "h_r": 0.2,
}
```

Example: Set key 0 keyboard character "a"

``` json
{
    "cmd": "w",
    "key": 2,
    "k_t": 0.1,
    "k_c": 0.2,
}
```


### Read Request

This message is used to read data from the fluxpad. The value of "cmd" is "r".

Example: Read key type and key code of key 0
Request
``` json
{
    "cmd": "r",
    "key": 0,  // These values are unused and can be anything
    "k_t": 0,
    "k_c": 0,
}
```
Response
``` json
{
    "cmd": "r",
    "key": 0,  // These values are the actual values from the read
    "k_t": 1,
    "k_c": 4,
}
```

### Message Keys

This is a list of valid keys that can appear in a `request message`

| JSON Key | Name [units or range] | Description | Type | Notes |
| - | - | - | - | - |
| `tkn` | Message Token [uint32] | Message token that the response will echo (write only) | int
| `key` | Key ID [0,5]| Key ID that the following keys applies to | string
| `k_t` | Key Type [0,1] | HID Usage Page, Keyboard=0, Consumer=1 | int
| `k_c` | Key Code [0,255] | HID Key Usage ID (keycode) | int
| `h_a` | Actuate Hysteresis [mm] | Actuation hysteresis (Analog key only) | number
| `h_r` | Release Hysteresis [mm] | Release hysteresis (Analog key only) | number
| `p_a` | Actuate Point [mm] | Actuation point (Analog key only) | number
| `p_r` | Release Point [mm] | Release point (Analog key only) | number
| `rt` | Rapid Trigger | Enable or disable rapid trigger (Analog key only) | bool
| `adc` | Raw ADC [0,4095] | Raw ADC counts (read only) | number
| `ht` | Height [mm] | Calculated height of key ADC (read only) | number
| `d_a` | Actuate Debounce [ms] | Actuation debouce time | integer
| `d_r` | Release Debounce [ms] | Actuation debouce time | integer
| `a_s` | ADC Samples [0,32] | Number of ADC samples to take per loop | integer
| `c_u` | Calibration ADC Up | Calibration ADC value of key in up position | number
| `c_d` | Calibration ADC Down | Calibration ADC value of key in down position | number
| `l_m` | Lighting Mode [0,4] | Lighting mode, Off, Fade, Flash, Static | number
| `l_b` | Lighting Brightness [0,255] | Brightness of per-key lighting | integer
| `l_h` | Fade Half Life [us]  | Fade Mode lighting half life in us | number
| `l_f` | Flash Duration [us] | Flash Mode lighting duration in us | number
| `rgb_m` | RGB Mode [0,3] | RGB Lighting Mode, 0=Off, 1=Static, 2=Rainbow | integer
| `rgb_b` | RGB Brightness [0,255] | RGB Lighting Speed, for Static. Cycles per as a 32 bit number. | integer
| `rgb_s` | RGB Speed [0,3] | RGB Lighting Speed, for Rainbow. Cycles per minute. | integer
| `rgb_c1` | RGB Colour [0,2^32] | RGB Light 1 (right) Colour, for Static. RGB Colour as a 32 bit number. | integer
| `rgb_c2` | RGB Colour [0,2^32] | RGB Light 2 (center) Colour, for Static. Cycles per as a 32 bit number. | integer
| `rgb_c3` | RGB Colour [0,2^32] | RGB Light 3 (left) Colour, for Static. Cycles per as a 32 bit number. | integer
| `clear` | Clear Flash Memory | Factory reset the flash memory. Enter integer `1234` to clear. | integer



| `dstrm` | Datastream mode | Datastream mode enable or disable | bool
| `dstrm_freq` | Datastream Frequency [hz] | Datastream mode message frequency | int


## Datastream Mode
