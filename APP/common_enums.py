import enum

class KeyType(enum.IntEnum):
    KEYBOARD = 1
    CONSUMER = 2


class ConsumerKeycodes(enum.IntEnum):
    UNASSIGNED              = 0x00
    POWER                   = 0x30
    SLEEP                   = 0x32
    RECORD                  = 0xB2
    FAST_FORWARD            = 0xB3
    REWIND                  = 0xB4
    NEXT                    = 0xB5
    PREV                    = 0xB6
    STOP                    = 0xB7
    PLAY_PAUSE              = 0xCD
    PAUSE                   = 0xB0
    VOL_MUTE                = 0xE2
    VOL_UP                  = 0xE9
    VOL_DOWN                = 0xEA
    BRIGHTNESS_UP           = 0x6F
    BRIGHTNESS_DOWN         = 0x70

class KeyboardKeycodes(enum.IntEnum):
    RESERVED        =  0
    A               =  4
    B               =  5
    C               =  6
    D               =  7
    E               =  8
    F               =  9
    G               = 10
    H               = 11
    I               = 12
    J               = 13
    K               = 14
    L               = 15
    M               = 16
    N               = 17
    O               = 18
    P               = 19
    Q               = 20
    R               = 21
    S               = 22
    T               = 23
    U               = 24
    V               = 25
    W               = 26
    X               = 27
    Y               = 28
    Z               = 29
    KEY_1             = 30
    KEY_2               = 31
    KEY_3               = 32
    KEY_4               = 33
    KEY_5               = 34
    KEY_6               = 35
    KEY_7               = 36
    KEY_8               = 37
    KEY_9               = 38
    KEY_0               = 39
    ENTER           = 40
    RETURN          = 40
    ESC             = 41
    BACKSPACE       = 42
    TAB             = 43
    SPACE           = 44
    MINUS           = 45
    EQUAL           = 46
    LEFT_BRACE      = 47
    RIGHT_BRACE     = 48
    BACKSLASH       = 49
    NON_US_NUM      = 50
    SEMICOLON       = 51
    QUOTE           = 52
    TILDE           = 53
    COMMA           = 54
    PERIOD          = 55
    SLASH           = 56
    CAPS_LOCK       = 0x39
    F1              = 0x3A
    F2              = 0x3B
    F3              = 0x3C
    F4              = 0x3D
    F5              = 0x3E
    F6              = 0x3F
    F7              = 0x40
    F8              = 0x41
    F9              = 0x42
    F10             = 0x43
    F11             = 0x44
    F12             = 0x45
    PRINT           = 0x46
    PRINTSCREEN     = 0x46
    SCROLL_LOCK     = 0x47
    PAUSE           = 0x48
    INSERT          = 0x49
    DELETE          = 0x4C
    HOME            = 0x4A
    END             = 0x4D
    PAGE_UP         = 0x4B
    PAGE_DOWN       = 0x4E
    RIGHT_ARROW     = 0x4F
    LEFT_ARROW      = 0x50
    DOWN_ARROW      = 0x51
    UP_ARROW        = 0x52
    RIGHT           = 0x4F
    LEFT            = 0x50
    DOWN            = 0x51
    UP              = 0x52
    NUM_LOCK        = 0x53
    KEYPAD_DIVIDE       = 0x54
    KEYPAD_MULTIPLY     = 0x55
    KEYPAD_SUBTRACT     = 0x56
    KEYPAD_ADD          = 0x57
    KEYPAD_ENTER        = 0x58
    KEYPAD_1            = 0x59
    KEYPAD_2            = 0x5A
    KEYPAD_3            = 0x5B
    KEYPAD_4            = 0x5C
    KEYPAD_5            = 0x5D
    KEYPAD_6            = 0x5E
    KEYPAD_7            = 0x5F
    KEYPAD_8            = 0x60
    KEYPAD_9            = 0x61
    KEYPAD_0            = 0x62
    KEYPAD_DOT          = 0x63
    KEY_NON_US          = 0x64
    KEY_APPLICATION     = 0x65
    KEY_MENU            = 0x65

KeyboardKeycodeStrings = {
    KeyboardKeycodes.KEY_1.value : "1",
    KeyboardKeycodes.KEY_2.value : "2",
    KeyboardKeycodes.KEY_3.value : "3",
    KeyboardKeycodes.KEY_4.value : "4",
    KeyboardKeycodes.KEY_5.value : "5",
    KeyboardKeycodes.KEY_6.value : "6",
    KeyboardKeycodes.KEY_7.value : "7",
    KeyboardKeycodes.KEY_8.value : "8",
    KeyboardKeycodes.KEY_9.value : "9",
    KeyboardKeycodes.KEY_0.value : "0",
}
    

def get_all_key_list():
    string_list = []
    string_list += [x.name for x in KeyboardKeycodes]
    string_list += [x.name for x in ConsumerKeycodes]
    return string_list

def keycode_to_string(keytype: int, keycode: int):

    if keytype == KeyType.CONSUMER:
        return ConsumerKeycodes(keycode).name
    
    if keytype == KeyType.KEYBOARD:
        try:
            return KeyboardKeycodeStrings[keycode]
        except KeyError:
            return KeyboardKeycodes(keycode).name

    return "Unsupported Key"