from typing import Union, List
import enum
import pynput

# USB HID to PS/2 Scan Code Translation Table
# (HID Usage Page, HID Usage ID, (PS/2 Set 1 Make, PS/2 Set 1 Break, PS/2 Set 2 Make, PS/2 Set 2 Break), Key Name)

@enum.unique
class KeyType(enum.IntEnum):
    """This must be in sync with flux_arduino.KeyType_t"""
    NONE = 0
    KEYBOARD = 1
    CONSUMER = 2
    MOUSE = 3


class ScanCode:

    def __init__(self,
                 hid_usage: int,
                 hid_keycode: int,
                 ps2_set1_make: Union[int, None],
                 pynput_key_keycode: Union[int, pynput.keyboard.Key, None],
                 name: str
                 ):
        self.hid_usage = hid_usage
        self.hid_keycode = hid_keycode
        self.ps2_set1_make = ps2_set1_make
        self.pynput_key_keycode = pynput_key_keycode
        self.name = name


@enum.unique
class ScanCodeList(enum.Enum):
    # ScanCode(0x01, 0x81, 0xE05E, pynput.keyboard.Key, 'System Power'),
    # ScanCode(0x01, 0x82, 0xE05F, 'System Sleep'),
    # ScanCode(0x01, 0x83, 0xE063, 'System Wake'),
    # ScanCode(0x07, 0x00, None, 'No Event'),
    # ScanCode(0x07, 0x01, 0xFF, 'Overrun Error'),
    # ScanCode(0x07, 0x02, 0xFC, 'POST Fail'),
    # ScanCode(0x07, 0x03, None, 'ErrorUndefined'),
    KEY_A = ScanCode(KeyType.KEYBOARD, 0x04, 0x1E, None, 'A')
    KEY_B = ScanCode(KeyType.KEYBOARD, 0x05, 0x30, None, 'B')
    KEY_C = ScanCode(KeyType.KEYBOARD, 0x06, 0x2E, None, 'C')
    KEY_D = ScanCode(KeyType.KEYBOARD, 0x07, 0x20, None, 'D')
    KEY_E = ScanCode(KeyType.KEYBOARD, 0x08, 0x12, None, 'E')
    KEY_F = ScanCode(KeyType.KEYBOARD, 0x09, 0x21, None, 'F')
    KEY_G = ScanCode(KeyType.KEYBOARD, 0x0A, 0x22, None, 'G')
    KEY_H = ScanCode(KeyType.KEYBOARD, 0x0B, 0x23, None, 'H')
    KEY_I = ScanCode(KeyType.KEYBOARD, 0x0C, 0x17, None, 'I')
    KEY_J = ScanCode(KeyType.KEYBOARD, 0x0D, 0x24, None, 'J')
    KEY_K = ScanCode(KeyType.KEYBOARD, 0x0E, 0x25, None, 'K')
    KEY_L = ScanCode(KeyType.KEYBOARD, 0x0F, 0x26, None, 'L')
    KEY_M = ScanCode(KeyType.KEYBOARD, 0x10, 0x32, None, 'M')
    KEY_N = ScanCode(KeyType.KEYBOARD, 0x11, 0x31, None, 'N')
    KEY_O = ScanCode(KeyType.KEYBOARD, 0x12, 0x18, None, 'O')
    KEY_P = ScanCode(KeyType.KEYBOARD, 0x13, 0x19, None, 'P')
    KEY_Q = ScanCode(KeyType.KEYBOARD, 0x14, 0x10, None, 'Q')
    KEY_R = ScanCode(KeyType.KEYBOARD, 0x15, 0x13, None, 'R')
    KEY_S = ScanCode(KeyType.KEYBOARD, 0x16, 0x1F, None, 'S')
    KEY_T = ScanCode(KeyType.KEYBOARD, 0x17, 0x14, None, 'T')
    KEY_U = ScanCode(KeyType.KEYBOARD, 0x18, 0x16, None, 'U')
    KEY_V = ScanCode(KeyType.KEYBOARD, 0x19, 0x2F, None, 'V')
    KEY_W = ScanCode(KeyType.KEYBOARD, 0x1A, 0x11, None, 'W')
    KEY_X = ScanCode(KeyType.KEYBOARD, 0x1B, 0x2D, None, 'X')
    KEY_Y = ScanCode(KeyType.KEYBOARD, 0x1C, 0x15, None, 'Y')
    KEY_Z = ScanCode(KeyType.KEYBOARD, 0x1D, 0x2C, None, 'Z')
    KEY_1 = ScanCode(KeyType.KEYBOARD, 0x1E, 0x02, None, '1')
    KEY_2 = ScanCode(KeyType.KEYBOARD, 0x1F, 0x03, None, '2')
    KEY_3 = ScanCode(KeyType.KEYBOARD, 0x20, 0x04, None, '3')
    KEY_4 = ScanCode(KeyType.KEYBOARD, 0x21, 0x05, None, '4')
    KEY_5 = ScanCode(KeyType.KEYBOARD, 0x22, 0x06, None, '5')
    KEY_6 = ScanCode(KeyType.KEYBOARD, 0x23, 0x07, None, '6')
    KEY_7 = ScanCode(KeyType.KEYBOARD, 0x24, 0x08, None, '7')
    KEY_8 = ScanCode(KeyType.KEYBOARD, 0x25, 0x09, None, '8')
    KEY_9 = ScanCode(KeyType.KEYBOARD, 0x26, 0x0A, None, '9')
    KEY_0 = ScanCode(KeyType.KEYBOARD, 0x27, 0x0B, None, '0')
    Return = ScanCode(KeyType.KEYBOARD, 0x28, 0x1C, pynput.keyboard.Key.enter, 'Return')
    Escape = ScanCode(KeyType.KEYBOARD, 0x29, 0x01, pynput.keyboard.Key.esc, 'Escape')
    Backspace = ScanCode(KeyType.KEYBOARD, 0x2A, 0x0E, pynput.keyboard.Key.backspace, 'Backspace')
    Tab = ScanCode(KeyType.KEYBOARD, 0x2B, 0x0F, pynput.keyboard.Key.tab, 'Tab')
    Space = ScanCode(KeyType.KEYBOARD, 0x2C, 0x39, pynput.keyboard.Key.space, 'Space')
    MINUS = ScanCode(KeyType.KEYBOARD, 0x2D, 0x0C, 189, '- _')
    EQUAL = ScanCode(KeyType.KEYBOARD, 0x2E, 0x0D, 187, '= +')
    OPENBRACKET = ScanCode(KeyType.KEYBOARD, 0x2F, 0x1A, 219, '[ {')
    CLOSEBRACKET = ScanCode(KeyType.KEYBOARD, 0x30, 0x1B, 221, '] }')
    KEY_0x31 = ScanCode(KeyType.KEYBOARD, 0x31, 0x2B, 220, '\\ |')
    KEY_0x32 = ScanCode(KeyType.KEYBOARD, 0x32, 0x2B, None, 'Non-US # ~')
    KEY_0x33 = ScanCode(KeyType.KEYBOARD, 0x33, 0x27, 186, '; :')
    KEY_0x34 = ScanCode(KeyType.KEYBOARD, 0x34, 0x28, 222, '\' "')
    KEY_0x35 = ScanCode(KeyType.KEYBOARD, 0x35, 0x29, 192, '` ~')
    KEY_0x36 = ScanCode(KeyType.KEYBOARD, 0x36, 0x33, 188, ', <')
    KEY_0x37 = ScanCode(KeyType.KEYBOARD, 0x37, 0x34, 190, '. >')
    KEY_0x38 = ScanCode(KeyType.KEYBOARD, 0x38, 0x35, 191, '/ ?')
    KEY_0x39 = ScanCode(KeyType.KEYBOARD, 0x39, 0x3A, pynput.keyboard.Key.caps_lock, 'Caps Lock')
    KEY_0x3A = ScanCode(KeyType.KEYBOARD, 0x3A, 0x3B, pynput.keyboard.Key.f1, 'F1')
    KEY_0x3B = ScanCode(KeyType.KEYBOARD, 0x3B, 0x3C, pynput.keyboard.Key.f2, 'F2')
    KEY_0x3C = ScanCode(KeyType.KEYBOARD, 0x3C, 0x3D, pynput.keyboard.Key.f3, 'F3')
    KEY_0x3D = ScanCode(KeyType.KEYBOARD, 0x3D, 0x3E, pynput.keyboard.Key.f4, 'F4')
    KEY_0x3E = ScanCode(KeyType.KEYBOARD, 0x3E, 0x3F, pynput.keyboard.Key.f5, 'F5')
    KEY_0x3F = ScanCode(KeyType.KEYBOARD, 0x3F, 0x40, pynput.keyboard.Key.f6, 'F6')
    KEY_0x40 = ScanCode(KeyType.KEYBOARD, 0x40, 0x41, pynput.keyboard.Key.f7, 'F7')
    KEY_0x41 = ScanCode(KeyType.KEYBOARD, 0x41, 0x42, pynput.keyboard.Key.f8, 'F8')
    KEY_0x42 = ScanCode(KeyType.KEYBOARD, 0x42, 0x43, pynput.keyboard.Key.f9, 'F9')
    KEY_0x43 = ScanCode(KeyType.KEYBOARD, 0x43, 0x44, pynput.keyboard.Key.f10, 'F10')
    KEY_0x44 = ScanCode(KeyType.KEYBOARD, 0x44, 0x57, pynput.keyboard.Key.f11, 'F11')
    KEY_0x45 = ScanCode(KeyType.KEYBOARD, 0x45, 0x58, pynput.keyboard.Key.f12, 'F12')
    KEY_0x46 = ScanCode(KeyType.KEYBOARD, 0x46, 0xE037, pynput.keyboard.Key.print_screen, 'Print Screen')
    KEY_0x47 = ScanCode(KeyType.KEYBOARD, 0x47, 0x46, pynput.keyboard.Key.scroll_lock, 'Scroll Lock')
    KEY_0x48 = ScanCode(KeyType.KEYBOARD, 0x48, 0xE046E0C6, pynput.keyboard.Key.pause, 'Pause')
    KEY_0x49 = ScanCode(KeyType.KEYBOARD, 0x49, 0xE052, pynput.keyboard.Key.insert, 'Insert')
    KEY_0x4A = ScanCode(KeyType.KEYBOARD, 0x4A, 0xE047, pynput.keyboard.Key.home, 'Home')
    KEY_0x4B = ScanCode(KeyType.KEYBOARD, 0x4B, 0xE049, pynput.keyboard.Key.page_up, 'Page Up')
    KEY_0x4C = ScanCode(KeyType.KEYBOARD, 0x4C, 0xE053, pynput.keyboard.Key.delete, 'Delete')
    KEY_0x4D = ScanCode(KeyType.KEYBOARD, 0x4D, 0xE04F, pynput.keyboard.Key.end, 'End')
    KEY_0x4E = ScanCode(KeyType.KEYBOARD, 0x4E, 0xE051, pynput.keyboard.Key.page_down, 'Page Down')
    KEY_0x4F = ScanCode(KeyType.KEYBOARD, 0x4F, 0xE04D, pynput.keyboard.Key.right, 'Right Arrow')
    KEY_0x50 = ScanCode(KeyType.KEYBOARD, 0x50, 0xE04B, pynput.keyboard.Key.left, 'Left Arrow')
    KEY_0x51 = ScanCode(KeyType.KEYBOARD, 0x51, 0xE050, pynput.keyboard.Key.down, 'Down Arrow')
    KEY_0x52 = ScanCode(KeyType.KEYBOARD, 0x52, 0xE048, pynput.keyboard.Key.up, 'Up Arrow')
    KEY_0x53 = ScanCode(KeyType.KEYBOARD, 0x53, 0x45, pynput.keyboard.Key.num_lock, 'Num Lock')
    KEY_0x54 = ScanCode(KeyType.KEYBOARD, 0x54, 0xE035, 111, 'Keypad /')
    KEY_0x55 = ScanCode(KeyType.KEYBOARD, 0x55, 0x37, 106, 'Keypad *')
    KEY_0x56 = ScanCode(KeyType.KEYBOARD, 0x56, 0x4A, 109, 'Keypad -')
    KEY_0x57 = ScanCode(KeyType.KEYBOARD, 0x57, 0x4E, 107, 'Keypad +')
    KEY_0x58 = ScanCode(KeyType.KEYBOARD, 0x58, 0xE01C, None, 'Keypad Enter')
    KEY_0x59 = ScanCode(KeyType.KEYBOARD, 0x59, 0x4F, 97, 'Keypad 1')
    KEY_0x5A = ScanCode(KeyType.KEYBOARD, 0x5A, 0x50, 98, 'Keypad 2')
    KEY_0x5B = ScanCode(KeyType.KEYBOARD, 0x5B, 0x51, 99, 'Keypad 3')
    KEY_0x5C = ScanCode(KeyType.KEYBOARD, 0x5C, 0x4B, 100, 'Keypad 4')
    KEY_0x5D = ScanCode(KeyType.KEYBOARD, 0x5D, 0x4C, 101, 'Keypad 5')
    KEY_0x5E = ScanCode(KeyType.KEYBOARD, 0x5E, 0x4D, 102, 'Keypad 6')
    KEY_0x5F = ScanCode(KeyType.KEYBOARD, 0x5F, 0x47, 103, 'Keypad 7')
    KEY_0x60 = ScanCode(KeyType.KEYBOARD, 0x60, 0x48, 104, 'Keypad 8')
    KEY_0x61 = ScanCode(KeyType.KEYBOARD, 0x61, 0x49, 105, 'Keypad 9')
    KEY_0x62 = ScanCode(KeyType.KEYBOARD, 0x62, 0x52, 96, 'Keypad 0')
    KEY_0x63 = ScanCode(KeyType.KEYBOARD, 0x63, 0x53, 110, 'Keypad .')
    KEY_0x64 = ScanCode(KeyType.KEYBOARD, 0x64, 0x56, 226, 'Non-US \\ |')
    # ScanCode(0x07, 0x65, 0xE05D, 'App')
    # ScanCode(0x07, 0x66, None, 'Keyboard Power')
    KEY_0x67 = ScanCode(KeyType.KEYBOARD, 0x67, 0x59, 12, 'Keypad =')
    KEY_0x68 = ScanCode(KeyType.KEYBOARD, 0x68, 0x5D, pynput.keyboard.Key.f13, 'F13')
    KEY_0x69 = ScanCode(KeyType.KEYBOARD, 0x69, 0x5E, pynput.keyboard.Key.f14, 'F14')
    KEY_0x6A = ScanCode(KeyType.KEYBOARD, 0x6A, 0x5F, pynput.keyboard.Key.f15, 'F15')
    KEY_0x6B = ScanCode(KeyType.KEYBOARD, 0x6B, None, pynput.keyboard.Key.f16, 'F16')
    KEY_0x6C = ScanCode(KeyType.KEYBOARD, 0x6C, None, pynput.keyboard.Key.f17, 'F17')
    KEY_0x6D = ScanCode(KeyType.KEYBOARD, 0x6D, None, pynput.keyboard.Key.f18, 'F18')
    KEY_0x6E = ScanCode(KeyType.KEYBOARD, 0x6E, None, pynput.keyboard.Key.f19, 'F19')
    KEY_0x6F = ScanCode(KeyType.KEYBOARD, 0x6F, None, pynput.keyboard.Key.f20, 'F20')
    KEY_0x70 = ScanCode(KeyType.KEYBOARD, 0x70, None, pynput.keyboard.Key.f21, 'F21')
    KEY_0x71 = ScanCode(KeyType.KEYBOARD, 0x71, None, pynput.keyboard.Key.f22, 'F22')
    KEY_0x72 = ScanCode(KeyType.KEYBOARD, 0x72, None, pynput.keyboard.Key.f23, 'F23')
    KEY_0x73 = ScanCode(KeyType.KEYBOARD, 0x73, None, pynput.keyboard.Key.f24, 'F24')
    # ScanCode(0x07, 0x74, None, 'Keyboard Execute')
    # ScanCode(0x07, 0x75, None, 'Keyboard Help')
    # ScanCode(0x07, 0x76, None, 'Keyboard Menu')
    # ScanCode(0x07, 0x77, None, 'Keyboard Select')
    # ScanCode(0x07, 0x78, None, 'Keyboard Stop')
    # ScanCode(0x07, 0x79, None, 'Keyboard Again')
    # ScanCode(0x07, 0x7A, None, 'Keyboard Undo')
    # ScanCode(0x07, 0x7B, None, 'Keyboard Cut')
    # ScanCode(0x07, 0x7C, None, 'Keyboard Copy')
    # ScanCode(0x07, 0x7D, None, 'Keyboard Paste')
    # ScanCode(0x07, 0x7E, None, 'Keyboard Find')
    # ScanCode(0x07, 0x7F, None, 'Keyboard Mute')
    # ScanCode(0x07, 0x80, None, 'Keyboard Volume Up')
    # ScanCode(0x07, 0x81, None, 'Keyboard Volume Dn')
    # ScanCode(0x07, 0x82, None, 'Keyboard Locking Caps Lock')
    # ScanCode(0x07, 0x83, None, 'Keyboard Locking Num Lock')
    # ScanCode(0x07, 0x84, None, 'Keyboard Locking Scroll Lock')
    # ScanCode(KeyType.KEYBOARD, 0x85, 0x7E, None, 'Keypad , (Brazilian Keypad .)')
    # ScanCode(0x07, 0x86, None, 'Keyboard Equal Sign')
    KEY_0x87 = ScanCode(KeyType.KEYBOARD, 0x87, 0x73, 193, "ろ")
    KEY_0x88 = ScanCode(KeyType.KEYBOARD, 0x88, 0x70, 255, "カタカナ/ひらがな")
    KEY_0x89 = ScanCode(KeyType.KEYBOARD, 0x89, 0x7D, None, "￥")
    KEY_0x8A = ScanCode(KeyType.KEYBOARD, 0x8A, 0x79, None, "変換")
    KEY_0x8B = ScanCode(KeyType.KEYBOARD, 0x8B, 0x7B, 235, "無変換")
    # KEY_0x8C = ScanCode(KeyType.KEYBOARD, 0x8C, 0x5C, None, ",(PC9800 Keypad ,)")
    # ScanCode(0x07, 0x8D, None, "Keyboard Int'l 7")
    # ScanCode(0x07, 0x8E, None, "Keyboard Int'l 8")
    # ScanCode(0x07, 0x8F, None, "Keyboard Int'l 9")
    KEY_0x90 = ScanCode(KeyType.KEYBOARD, 0x90, 0xF2, None, '한/영')
    KEY_0x91 = ScanCode(KeyType.KEYBOARD, 0x91, 0xF1, None, '한자')
    KEY_0x92 = ScanCode(KeyType.KEYBOARD, 0x92, 0x78, None, 'カタカナ')
    KEY_0x93 = ScanCode(KeyType.KEYBOARD, 0x93, 0x77, None, 'ひらがな')
    KEY_0x94 = ScanCode(KeyType.KEYBOARD, 0x94, 0x76, None, '半角/全角')
    # ScanCode(0x07, 0x95, None, 'Keyboard Lang 6')
    # ScanCode(0x07, 0x96, None, 'Keyboard Lang 7')
    # ScanCode(0x07, 0x97, None, 'Keyboard Lang 8')
    # ScanCode(0x07, 0x98, None, 'Keyboard Lang 9')
    # ScanCode(0x07, 0x99, None, 'Keyboard Alternate Erase')
    # ScanCode(0x07, 0x9A, None, 'Keyboard SysReq/Attention')
    # ScanCode(0x07, 0x9B, None, 'Keyboard Cancel')
    # ScanCode(0x07, 0x9C, None, 'Keyboard Clear')
    # ScanCode(0x07, 0x9D, None, 'Keyboard Prior')
    # ScanCode(0x07, 0x9E, None, 'Keyboard Return')
    # ScanCode(0x07, 0x9F, None, 'Keyboard Separator')
    # ScanCode(0x07, 0xA0, None, 'Keyboard Out')
    # ScanCode(0x07, 0xA1, None, 'Keyboard Oper')
    # ScanCode(0x07, 0xA2, None, 'Keyboard Clear/Again')
    # ScanCode(0x07, 0xA3, None, 'Keyboard CrSel/Props')
    # ScanCode(0x07, 0xA4, None, 'Keyboard ExSel')
    # ScanCode('07', 'A5-DF', (', 'RESERVED',', 'RESERVED'), 'RESERVED')
    LEFT_CTRL = ScanCode(KeyType.KEYBOARD, 0xE0, 0x1D, pynput.keyboard.Key.ctrl_l, 'Left Control')
    LEFT_SHIFT = ScanCode(KeyType.KEYBOARD, 0xE1, 0x2A, pynput.keyboard.Key.shift_l, 'Left Shift')
    LEFT_ALT = ScanCode(KeyType.KEYBOARD, 0xE2, 0x38, pynput.keyboard.Key.alt_l, 'Left Alt')
    LEFT_GUI = ScanCode(KeyType.KEYBOARD, 0xE3, 0xE05B, pynput.keyboard.Key.cmd_l, 'Left GUI')
    RIGHT_CTRL = ScanCode(KeyType.KEYBOARD, 0xE4, 0xE01D, pynput.keyboard.Key.ctrl_r, 'Right Control')
    RIGHT_SHIFT = ScanCode(KeyType.KEYBOARD, 0xE5, 0x36, pynput.keyboard.Key.shift_r, 'Right Shift')
    RIGHT_ALT = ScanCode(KeyType.KEYBOARD, 0xE6, 0xE038, pynput.keyboard.Key.alt_r, 'Right Alt')
    RIGHT_GUI = ScanCode(KeyType.KEYBOARD, 0xE7, 0xE05C, pynput.keyboard.Key.cmd_r, 'Right GUI')
    # ScanCode('07', 'E8-FFFF', (', 'RESERVED',', 'RESERVED'), 'RESERVED')
    MEDIA_NEXT = ScanCode(KeyType.CONSUMER, 0x00B5, 0xE019, pynput.keyboard.Key.media_next, 'Next Track')
    MEDIA_PREVIOUS = ScanCode(KeyType.CONSUMER, 0x00B6, 0xE010, pynput.keyboard.Key.media_previous, 'Previous Track')
    MEDIA_STOP = ScanCode(KeyType.CONSUMER, 0x00B7, 0xE024, None, 'Stop')
    MEDIA_PLAY_PAUSE = ScanCode(KeyType.CONSUMER, 0x00CD, 0xE022, pynput.keyboard.Key.media_play_pause, 'Play/Pause')
    MEDIA_MUTE = ScanCode(KeyType.CONSUMER, 0x00E2, 0xE020, pynput.keyboard.Key.media_volume_mute, 'Mute')
    # ScanCode(0x0C, 0x00E5, None, None, 'Bass Boost'
    # ScanCode(0x0C, 0x00E7, (None, None, 'Loudness')
    MEDIA_VOL_UP = ScanCode(KeyType.CONSUMER, 0x00E9, 0xE030, pynput.keyboard.Key.media_volume_up, 'Volume Up')
    MEDIA_VOL_DOWN = ScanCode(KeyType.CONSUMER, 0x00EA, 0xE02E, pynput.keyboard.Key.media_volume_down, 'Volume Down')
    # ScanCode(0x0C, 0x0152, (None, None, 'Bass Up')
    # ScanCode(0x0C, 0x0153, (None, None, 'Bass Down')
    # ScanCode(0x0C, 0x0154, (None, None, 'Treble Up')
    # ScanCode(0x0C, 0x0155, (None, None, 'Treble Down')
    MEDIA_SELECT = ScanCode(KeyType.CONSUMER, 0x0183, 0xE06D, None, 'Media Select')
    MAIL = ScanCode(KeyType.CONSUMER, 0x018A, 0xE06C, 180, 'Mail')
    CALCULATOR = ScanCode(KeyType.CONSUMER, 0x0192, 0xE021, 183, 'Calculator')
    MY_COMPUTER = ScanCode(KeyType.CONSUMER, 0x0194, 0xE06B, 182, 'My Computer')
    WWW_SEARCH = ScanCode(KeyType.CONSUMER, 0x0221, 0xE065, 170, 'WWW Search')
    WWw_HOME = ScanCode(KeyType.CONSUMER, 0x0223, 0xE032, 172, 'WWW Home')
    WWW_BACK = ScanCode(KeyType.CONSUMER, 0x0224, 0xE06A, 166, 'WWW Back')
    WWW_FORWARD = ScanCode(KeyType.CONSUMER, 0x0225, 0xE069, 167, 'WWW Forward')
    WWW_STOP = ScanCode(KeyType.CONSUMER, 0x0226, 0xE068, 169, 'WWW Stop')
    WWW_REFRESH = ScanCode(KeyType.CONSUMER, 0x0227, 0xE067, 168, 'WWW Refresh')
    WWW_FAVORITES = ScanCode(KeyType.CONSUMER, 0x022A, 0xE066, 171, 'WWW Favorites')
    KEY_NONE = ScanCode(KeyType.NONE, 0x00, None, None, "No Key")



SCANCODE_LIST: List[ScanCode] = [keycode.value for keycode in ScanCodeList]

def key_name_to_keycode(key_name: str):
    """Get a ScanCode from keyname"""
    return next(filter(lambda x: x.name == key_name, SCANCODE_LIST), None)


def get_name_list():
    string_list = [x.name for x in SCANCODE_LIST]
    return string_list

def pynput_event_to_scancode(key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode]):
    """Get ScanCode from pynput event, or None if not found"""

    if isinstance(key, pynput.keyboard.Key):
        return next(filter(lambda x: x.pynput_key_keycode == key, SCANCODE_LIST), None)

    if isinstance(key, pynput.keyboard.KeyCode):
        if 65 <= key.vk <= 90 or 48 <= key.vk <= 57:
            return next(filter(lambda x: ord(x.name) == key.vk, SCANCODE_LIST), None)
        
        return next(filter(lambda x: x.pynput_key_keycode == key.vk, SCANCODE_LIST), None)
        