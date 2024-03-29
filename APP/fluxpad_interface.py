import enum
import json
from collections import deque
from typing import Deque, NamedTuple, Optional, TypedDict, Literal, Dict, Union, List, get_type_hints, Callable, TypeVar
import logging
import pathlib
import threading
import time

import serial
import serial.tools.list_ports

from scancode_to_hid_code import KeyType, ScanCodeList


def find_fluxpad_port():
    serial_ports = serial.tools.list_ports.comports()
    for serial_port in serial_ports:
        if serial_port.pid == Fluxpad.PID and serial_port.vid == Fluxpad.VID:
            return serial_port.name
    return None


class CommandType(enum.Enum):
    WRITE = "w"
    READ = "r"
    VERSION = "v"


class LightingMode(enum.IntEnum):
    Off = 0
    Static = 1
    Fade = 2
    Flash = 3


class RGBMode(enum.IntEnum):
    Off = 0
    Static = 1
    Rainbow = 2


class MessageKey:
    COMMAND = "cmd"
    VERSION = "V"
    TOKEN = "tkn"
    KEY_ID = "key"
    KEY_TYPE = "k_t"
    KEY_CODE = "k_c"
    ACTUATE_HYSTERESIS = "h_a"
    RELEASE_HYSTERESIS = "h_r"
    ACTUATE_POINT = "p_a"
    RELEASE_POINT = "p_r"
    RAPID_TRIGGER = "rt"
    RAW_ADC = "adc"
    HEIGHT = "ht"
    ACTUATE_DEBOUNCE = "d_a"
    RELEASE_DEBOUNCE = "d_r"
    ADC_SAMPLES = "a_s"
    CALIBRATION_UP = "c_u"
    CALIBRATION_DOWN = "c_d"
    DATASTREAM_MODE = "dstrm"
    DATASTREAM_FREQUENCY = "dstrm_freq"
    LIGHTING_MODE = "l_m"
    LIGHTING_FADE_BRIGHTNESS = "l_b"
    LIGHTING_FLASH_DURATION = "l_d"
    RGB_MODE = "rgb_m"
    RGB_BRIGHTNESS = "rgb_b"
    RGB_SPEED = "rgb_s"
    RGB_C1 = "rgb_c1"
    RGB_C2 = "rgb_c2"
    RGB_C3 = "rgb_c3"
    CLEAR_FLASH = "clear"


class BaseMessage:

    def __init__(self, init_dict: Optional[dict] = None) -> None:
        if init_dict is None:
            init_dict = dict()
        self.data = init_dict

    def to_string(self) -> str:
        return json.dumps(self.data, indent=None, separators=(',', ':'))

    def to_bytes(self):
        return self.to_string().encode("ASCII")
    
    def set_zeros(self):
        """Set all message values to zero"""
        for k, v in self.__class__.__dict__.items():
            # Iterate through all class members and look for properties
            if isinstance(v, property):
                # print(get_type_hints(v.fset))
                expected_type = next(iter(get_type_hints(v.fset).values()))
                setattr(self, k, expected_type(0))  # Set property to zero to set the message value
    
    @property
    def token(self):
        return self.data[MessageKey.TOKEN]

    @token.setter
    def token(self, token: int):
        self._assert_uint8(token)
        self.data[MessageKey.TOKEN] = token

    @property
    def command(self):
        return self.data[MessageKey.TOKEN]

    @command.setter
    def command(self, cmd: CommandType):
        assert isinstance(cmd, CommandType)
        self.data[MessageKey.COMMAND] = cmd.value

    @staticmethod
    def _assert_uint8(value):
        assert isinstance(value, int)
        assert 0x00 <= value <= 0xFF

    @staticmethod
    def _assert_uint16(value):
        assert isinstance(value, int)
        assert 0x00 <= value <= 0xFFFF

class EncoderSettingsMessage(BaseMessage):

    # KEY ID
    @property
    def key_id(self):
        return self.data[MessageKey.KEY_ID]

    @key_id.setter
    def key_id(self, key_id: int):
        self._assert_uint8(key_id)
        self.data[MessageKey.KEY_ID] = key_id

    # KEYMAP
    @property
    def key_code(self):
        return self.data[MessageKey.KEY_CODE]

    @key_code.setter
    def key_code(self, key_code: int):
        self._assert_uint16(key_code)
        self.data[MessageKey.KEY_CODE] = key_code

    @key_code.deleter
    def key_code(self):
        try:
            del self.data[MessageKey.KEY_CODE]
        except KeyError:
            pass

    @property
    def key_type(self):
        return self.data[MessageKey.KEY_TYPE]

    @key_type.setter
    def key_type(self, key_type: int):
        self._assert_uint8(key_type)
        assert key_type in list(KeyType)
        self.data[MessageKey.KEY_TYPE] = key_type
    
    @key_type.deleter
    def key_type(self):
        try:
            del self.data[MessageKey.KEY_TYPE]
        except KeyError:
            pass


class DigitalSettingsMessage(BaseMessage):

    # KEY ID
    @property
    def key_id(self):
        return self.data[MessageKey.KEY_ID]

    @key_id.setter
    def key_id(self, key_id: int):
        self._assert_uint8(key_id)
        assert key_id in list(KeyType)
        self.data[MessageKey.KEY_ID] = key_id

    # KEYMAP
    @property
    def key_code(self):
        return self.data[MessageKey.KEY_CODE]

    @key_code.setter
    def key_code(self, key_code: int):
        self._assert_uint16(key_code)
        self.data[MessageKey.KEY_CODE] = key_code

    @property
    def key_type(self):
        return self.data[MessageKey.KEY_TYPE]

    @key_type.setter
    def key_type(self, key_type: int):
        self._assert_uint8(key_type)
        assert key_type in list(KeyType)
        self.data[MessageKey.KEY_TYPE] = key_type

    # DEBOUNCE
    @property
    def actuate_debounce(self):
        return self.data[MessageKey.ACTUATE_DEBOUNCE]

    @actuate_debounce.setter
    def actuate_debounce(self, debounce_ms: int):
        self._assert_uint8(debounce_ms)
        self.data[MessageKey.ACTUATE_DEBOUNCE] = debounce_ms

    @property
    def release_debounce(self):
        return self.data[MessageKey.RELEASE_DEBOUNCE]

    @release_debounce.setter
    def release_debounce(self, debounce_ms: int):
        self._assert_uint8(debounce_ms)
        self.data[MessageKey.RELEASE_DEBOUNCE] = debounce_ms

    # LIGHTING MODE
    @property
    def mode(self):
        return int(self.data[MessageKey.LIGHTING_MODE])

    @mode.setter
    def mode(self, mode: int):
        self._assert_uint8(mode)
        self.data[MessageKey.LIGHTING_MODE] = mode

    # LIGHTING BRIGHTNESS
    @property
    def brightness(self):
        return int(self.data[MessageKey.LIGHTING_FADE_BRIGHTNESS])

    @brightness.setter
    def brightness(self, brightness: int):
        self._assert_uint8(brightness)
        self.data[MessageKey.LIGHTING_FADE_BRIGHTNESS] = brightness

    # LIGHTING FLASH DURATION
    @property
    def flash_duration(self):
        return int(self.data[MessageKey.LIGHTING_FLASH_DURATION])

    @flash_duration.setter
    def flash_duration(self, flash_duration_us: int):
        self.data[MessageKey.LIGHTING_FLASH_DURATION] = flash_duration_us


class AnalogSettingsMessage(BaseMessage):

    # KEY ID
    @property
    def key_id(self):
        return self.data[MessageKey.KEY_ID]

    @key_id.setter
    def key_id(self, key_id: int):
        self._assert_uint8(key_id)
        self.data[MessageKey.KEY_ID] = key_id

    # KEYMAP
    @property
    def key_code(self):
        return self.data[MessageKey.KEY_CODE]

    @key_code.setter
    def key_code(self, key_code: int):
        self._assert_uint16(key_code)
        self.data[MessageKey.KEY_CODE] = key_code

    @property
    def key_type(self):
        return self.data[MessageKey.KEY_TYPE]

    @key_type.setter
    def key_type(self, key_type: int):
        self._assert_uint8(key_type)
        assert key_type in list(KeyType)
        self.data[MessageKey.KEY_TYPE] = key_type


    # HYSTERESIS
    @property
    def actuate_hysteresis(self):
        return self.data[MessageKey.ACTUATE_HYSTERESIS]

    @actuate_hysteresis.setter
    def actuate_hysteresis(self, hysteresis_mm: float):
        assert isinstance(hysteresis_mm, float)
        assert 0 <= hysteresis_mm
        self.data[MessageKey.ACTUATE_HYSTERESIS] = hysteresis_mm

    @property
    def release_hysteresis(self):
        return self.data[MessageKey.RELEASE_HYSTERESIS]

    @release_hysteresis.setter
    def release_hysteresis(self, hysteresis_mm: float):
        assert isinstance(hysteresis_mm, float)
        assert 0 <= hysteresis_mm
        self.data[MessageKey.RELEASE_HYSTERESIS] = hysteresis_mm

    # POINT
    @property
    def actuate_point(self):
        return self.data[MessageKey.ACTUATE_POINT]

    @actuate_point.setter
    def actuate_point(self, height_mm: float):
        assert isinstance(height_mm, float)
        assert 0 <= height_mm
        self.data[MessageKey.ACTUATE_POINT] = height_mm

    @property
    def release_point(self):
        return self.data[MessageKey.RELEASE_POINT]

    @release_point.setter
    def release_point(self, height_mm: float):
        assert isinstance(height_mm, float)
        assert 0 <= height_mm
        self.data[MessageKey.RELEASE_POINT] = height_mm

    # DEBOUNCE
    @property
    def actuate_debounce(self):
        return self.data[MessageKey.ACTUATE_DEBOUNCE]

    @actuate_debounce.setter
    def actuate_debounce(self, debounce_ms: int):
        self._assert_uint8(debounce_ms)
        self.data[MessageKey.ACTUATE_DEBOUNCE] = debounce_ms

    @property
    def release_debounce(self):
        return self.data[MessageKey.RELEASE_DEBOUNCE]

    @release_debounce.setter
    def release_debounce(self, debounce_ms: int):
        self._assert_uint8(debounce_ms)
        self.data[MessageKey.RELEASE_DEBOUNCE] = debounce_ms

    @property
    def adc_samples(self):
        return int(self.data[MessageKey.ADC_SAMPLES])

    @adc_samples.setter
    def adc_samples(self, adc_samples: int):
        self._assert_uint8(adc_samples)
        self.data[MessageKey.ADC_SAMPLES] = adc_samples

    @property
    def rapid_trigger(self):
        return bool(self.data[MessageKey.RAPID_TRIGGER])

    @rapid_trigger.setter
    def rapid_trigger(self, rapid_trigger_enable: bool):
        assert isinstance(rapid_trigger_enable, bool)
        self.data[MessageKey.RAPID_TRIGGER] = rapid_trigger_enable

    # LIGHTING MODE
    @property
    def mode(self):
        return int(self.data[MessageKey.LIGHTING_MODE])

    @mode.setter
    def mode(self, mode: int):
        self._assert_uint8(mode)
        self.data[MessageKey.LIGHTING_MODE] = mode

    # LIGHTING BRIGHTNESS
    @property
    def brightness(self):
        return int(self.data[MessageKey.LIGHTING_FADE_BRIGHTNESS])

    @brightness.setter
    def brightness(self, brightness: int):
        self._assert_uint8(brightness)
        self.data[MessageKey.LIGHTING_FADE_BRIGHTNESS] = brightness

    # LIGHTING FLASH DURATION
    @property
    def flash_duration(self):
        return int(self.data[MessageKey.LIGHTING_FLASH_DURATION])

    @flash_duration.setter
    def flash_duration(self, flash_duration_us: int):
        self.data[MessageKey.LIGHTING_FLASH_DURATION] = flash_duration_us


class AnalogCalibrationMessage(BaseMessage):
    """Analog key calibration message containing
    calibration up and calibration down settings"""

    # KEY ID
    @property
    def key_id(self):
        return self.data[MessageKey.KEY_ID]

    @key_id.setter
    def key_id(self, key_id: int):
        self._assert_uint8(key_id)
        self.data[MessageKey.KEY_ID] = key_id
    
    # CALIBRATION
    @property
    def calibration_up(self):
        return self.data[MessageKey.CALIBRATION_UP]

    @calibration_up.setter
    def calibration_up(self, up_adc: float):
        assert isinstance(up_adc, float)
        assert 0 <= up_adc <= 4096
        self.data[MessageKey.CALIBRATION_UP] = up_adc

    @calibration_up.deleter
    def calibration_up(self):
        try:
            del self.data[MessageKey.CALIBRATION_UP]
        except KeyError:
            pass

    @property
    def calibration_down(self):
        return float(self.data[MessageKey.CALIBRATION_DOWN])

    @calibration_down.setter
    def calibration_down(self, down_adc: float):
        assert isinstance(down_adc, float)
        assert 0 <= down_adc <= 4096
        self.data[MessageKey.CALIBRATION_DOWN] = down_adc

    @calibration_down.deleter
    def calibration_down(self):
        try:
            del self.data[MessageKey.CALIBRATION_DOWN]
        except KeyError:
            pass


class RGBSettingsMessage(BaseMessage):
    """KeyLightingMessage containing all info about a key's
    per-key lighting settings"""

    # RGB MODE
    @property
    def mode(self):
        return int(self.data[MessageKey.RGB_MODE])

    @mode.setter
    def mode(self, mode: int):
        self._assert_uint8(mode)
        self.data[MessageKey.RGB_MODE] = mode

    # RGB Color 1
    @property
    def color1(self):
        return int(self.data[MessageKey.RGB_C1])

    @color1.setter
    def color1(self, color: int):
        self.data[MessageKey.RGB_C1] = color

    # RGB Color 2
    @property
    def color2(self):
        return int(self.data[MessageKey.RGB_C2])

    @color2.setter
    def color2(self, color: int):
        self.data[MessageKey.RGB_C2] = color

    # RGB Color 3
    @property
    def color3(self):
        return int(self.data[MessageKey.RGB_C3])

    @color3.setter
    def color3(self, color: int):
        self.data[MessageKey.RGB_C3] = color

    # RGB BRIGHTNESS
    @property
    def brightness(self):
        return int(self.data[MessageKey.RGB_BRIGHTNESS])

    @brightness.setter
    def brightness(self, brightness: int):
        self.data[MessageKey.RGB_BRIGHTNESS] = brightness

    # RGB SPEED
    @property
    def speed(self):
        return int(self.data[MessageKey.RGB_SPEED])
    
    @speed.setter
    def speed(self, speed: int):
        self.data[MessageKey.RGB_SPEED] = speed
    

class AnalogReadMessage(BaseMessage):
    """Analog key read message containing """

    # KEY ID
    @property
    def key_id(self):
        return self.data[MessageKey.KEY_ID]

    @key_id.setter
    def key_id(self, key_id: int):
        self._assert_uint8(key_id)
        self.data[MessageKey.KEY_ID] = key_id

    # RAW ADC
    @property
    def raw_adc(self):
        return float(self.data[MessageKey.RAW_ADC])

    @raw_adc.setter
    def raw_adc(self, dummy: int):
        """Dummy function for read cmd, doesn't actually set raw_adc"""
        self.data[MessageKey.RAW_ADC] = 0

    @property
    def height_mm(self):
        return float(self.data[MessageKey.HEIGHT])

    @height_mm.setter
    def height_mm(self, dummy: int):
        """Dummy function for read cmd, doesn't actually set height_mm"""
        self.data[MessageKey.HEIGHT] = 0

class VersionReadMessage(BaseMessage):

    # VERSION
    @property
    def version(self):
        return self.data[MessageKey.VERSION]

    @version.setter
    def version(self, version: int):
        self._assert_uint8(version)
        self.data[MessageKey.VERSION] = version

# class KeySettingMessage(DigitalSettingsMessage, AnalogSettingsMessage, EncoderSettingsMessage, AnalogCalibrationMessage, AnalogReadMessage):
#     """Composite class of all settings types"""
#     pass

AnyMessage = TypeVar("AnyMessage", DigitalSettingsMessage, AnalogSettingsMessage, EncoderSettingsMessage, AnalogCalibrationMessage, AnalogReadMessage, RGBSettingsMessage, VersionReadMessage, Union[DigitalSettingsMessage, AnalogSettingsMessage, EncoderSettingsMessage, AnalogCalibrationMessage, AnalogReadMessage, RGBSettingsMessage])


class Fluxpad:

    VID = 0x1209
    PID = 0x7272
    BAUDRATE = 115200
    SOP_TOKEN = b"{"
    EOP_TOKEN = b"}"

    def __init__(self, port: str) -> None:
        self.port = serial.Serial()
        self.port.port = port
        self.port.baudrate = self.BAUDRATE
        self.port.bytesize = 8
        self.port.timeout = 0.1  # seconds
        self.last_token = 1
        self.incoming_msgs: Deque[BaseMessage] = deque()

    def get_next_token(self):
        self.last_token += 1
        if self.last_token > 255:
            self.last_token = 1
        return self.last_token

    def open(self):
        self.port.open()

    def close(self):
        self.port.close()

    def _send_request(self, message: AnyMessage):

        message_type = type(message)

        # Add token
        message.token = self.get_next_token()

        # Send bytes
        logging.debug(f"Sending {message.__class__.__name__}: {message.to_string()}")
        self.port.write(message.to_bytes())

        # Receive bytes
        self.port.read_until(expected=self.SOP_TOKEN, size=100)
        incoming_bytes = self.SOP_TOKEN + \
            self.port.read_until(expected=self.EOP_TOKEN, size=1024)
        incoming_string = incoming_bytes.decode("ASCII")
        logging.debug(f"Received message: {incoming_string}")
        incoming_json = json.loads(incoming_string)
        incoming_message = message_type(incoming_json)
        assert incoming_message.token == message.token, f"Token mismatch, expected {incoming_message.token}, got {message.token}"
        return incoming_message

    def send_write_request(self, message: AnyMessage) -> AnyMessage:
        """Send a write request to the fluxpad"""

        message.command = CommandType.WRITE
        return self._send_request(message)

    def send_read_request(self, message: AnyMessage) -> AnyMessage:
        """Send a read request to the fluxpad"""

        message.command = CommandType.READ
        return self._send_request(message)
    
    def get_version(self) -> int:
        message = VersionReadMessage()
        message.command = CommandType.VERSION
        return self._send_request(message).version


class FluxpadListener():
    """Listener for connected/disconnected events of a fluxpad"""

    LISTEN_PERIOD_S = 0.5
    
    def __init__(self, on_connect: Callable[[Fluxpad], None], on_disconnect: Callable[[], None]) -> None:
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_request = threading.Event()
        self._prev_port: Optional[str] = None
        self._on_connect_callback = on_connect
        self._on_disconnect_callback = on_disconnect

    def start(self):
        """Start the listener thread"""
        logging.debug("Starting listener")
        self._stop_request.clear()
        self._listener_thread = threading.Thread(target=self._worker, daemon=True)
        self._listener_thread.start()

    def stop(self):
        """Stop the listener thread"""
        logging.debug("Stopping listener")
        if self._listener_thread is not None and self._listener_thread.is_alive():
            self._stop_request.set()
            self._listener_thread.join(timeout=1.0)
            assert self._listener_thread.is_alive() == False, "Worker thread not stopped"
            self._listener_thread = None

    @property
    def is_connected(self):
        if self._prev_port is None:
            return False
        return True
        
    def _worker(self):
        while True:
            
            # Handle thread stop event
            if self._stop_request.wait(timeout=self.LISTEN_PERIOD_S):
                logging.debug("Stop request event received from worker thread")
                break

            try:
                port = find_fluxpad_port()
                if port != self._prev_port:
                    if isinstance(port, str):
                        # Connected, fire on connect callback
                        try:
                            self._on_connect_callback(Fluxpad(port))
                        except Exception:
                            logging.error("on_connect callback error", exc_info=1)
                    else:
                        # Disconnected, fire on connect callback
                        try:
                            self._on_disconnect_callback()
                        except Exception:
                            logging.error("on_disconnect callback error", exc_info=1)

            except Exception:
                logging.error("Listener worker error", exc_info=1)
            finally:
                self._prev_port = port
            
        # Clear the stop request on the way out
        self._stop_request.clear()
        logging.debug("Workor thread stopped")


# class DigitalSettings:
#     MESSAGE_KEY_LIST = [
#         MessageKey.ACTUATE_DEBOUNCE,
#         MessageKey.ACTUATE_HYSTERESIS,
#         MessageKey.ACTUATE_POINT,
#         MessageKey.RELEASE_DEBOUNCE,
#         MessageKey.RELEASE_HYSTERESIS,
#         MessageKey.RELEASE_POINT,
#         MessageKey.KEY_CODE,
#         MessageKey.KEY_TYPE
#     ]

#     def __init__(self, key_id) -> None:
#         self.d = dict()
#         self.d[MessageKey.KEY_ID] = key_id

# class AnalogSettings:
#     MESSAGE_KEY_LIST = [
#         MessageKey.ACTUATE_DEBOUNCE,
#         MessageKey.RELEASE_DEBOUNCE,
#         MessageKey.KEY_CODE,
#         MessageKey.KEY_TYPE
#     ]

#     def __init__(self, key_id) -> None:
#         self.d = dict()
#         self.d[MessageKey.KEY_ID] = key_id


# class EncoderSettings:
#     """Wrapper around Message object"""

#     MESSAGE_KEY_LIST = [
#         MessageKey.KEY_CODE,
#         MessageKey.KEY_TYPE
#     ]

#     def __init__(self, key_id) -> None:
#         self.d = dict()
#         self.d[MessageKey.KEY_ID] = key_id

class FluxpadSettings:

    KEY_SETTINGS_KEY = "key_settings"
    RGB_SETTINGS_KEY = "rgb_settings"
    
    def __init__(self) -> None:
        self.key_settings_list: List[Union[EncoderSettingsMessage, AnalogSettingsMessage, DigitalSettingsMessage]] = [
            DigitalSettingsMessage(),
            DigitalSettingsMessage(),
            AnalogSettingsMessage(),
            AnalogSettingsMessage(),
            AnalogSettingsMessage(),
            EncoderSettingsMessage(),
            EncoderSettingsMessage(),
        ]
        self.rgb_settings = RGBSettingsMessage()

    def _set_key_ids(self):
        key_id = 0
        for key_settings in self.key_settings_list:
            key_settings.key_id = key_id
            key_id += 1

    def get_version(self, fluxpad: Fluxpad):
        return fluxpad.get_version()

    def load_from_keypad(self, fluxpad: Fluxpad):
        """Load all settings from the given connected fluxpad"""

        if not fluxpad.port.is_open:
            raise ConnectionError("Fluxpad not connected")
        
        for key_settings in self.key_settings_list:
            try:
                # Read Settings
                key_settings.set_zeros()
                self._set_key_ids()
                response = fluxpad.send_read_request(key_settings)

                # Check all requested keys exist
                assert set(response.data.keys()) == set(key_settings.data.keys()), f"Difference: {set(response.data.keys()).symmetric_difference(set(key_settings.data.keys()))}"
                logging.debug(f"Got settings for Key ID {key_settings.key_id}")
            except Exception:
                logging.error(f"Failed to get settings for Key ID {key_settings.key_id} with message {key_settings.data}", exc_info=True)
            else:
                key_settings.data = response.data.copy()

        try:
            # Read RGB Settings
            self.rgb_settings.set_zeros()
            response = fluxpad.send_read_request(self.rgb_settings)

            # Check all requested keys exist
            assert set(response.data.keys()) == set(self.rgb_settings.data.keys()), f"Difference: {set(response.data.keys()).symmetric_difference(set(self.rgb_settings.data.keys()))}"
            logging.debug("Got RGB settings")
        except Exception:
            logging.error(f"Failed to get RGB settings {self.rgb_settings.data}", exc_info=True)
        else:
            self.rgb_settings.data = response.data.copy()

    def save_to_fluxpad(self, fluxpad: Fluxpad, include_calibration: bool = False):
        """Save all settings to the given connected fluxpad"""
        if not fluxpad.port.is_open:
            raise ConnectionError("Fluxpad not connected")
        
        for current_key_settings in self.key_settings_list:
            key_settings = current_key_settings
            try:
                assert isinstance(key_settings.key_id, int)  # check key id exists
                response = fluxpad.send_write_request(key_settings)
                logging.debug(f"Wrote settings for Key ID {key_settings.key_id}")
            except Exception:
                logging.error(f"Failed to write settings for Key ID {key_settings.key_id} with message {key_settings.data}", exc_info=True)

        rgb_settings = self.rgb_settings
        try:
            response = fluxpad.send_write_request(rgb_settings)
            logging.debug(f"Wrote rgb settings")
        except Exception:
            logging.error(f"Failed to write rgb settings with message {rgb_settings.data}", exc_info=True)
        
    def load_from_file(self, path: pathlib.Path):
        """Load all settings from the given file"""
        try:
            with path.open("r") as f:
                root_json = json.load(f)
        except Exception:
            logging.error(f"Failed to load settings from {path}", exc_info=True)
            return

        try:
            for json_object in root_json[self.KEY_SETTINGS_KEY]:
                self.key_settings_list[json_object[MessageKey.KEY_ID]].data = json_object
        except Exception:
            logging.error(f"Failed to parse key settings from {path}", exc_info=True)

        try:
            self.rgb_settings.data = root_json[self.RGB_SETTINGS_KEY]
        except Exception:
            logging.error(f"Failed to parse rgb settings from {path}", exc_info=True)
    
    def save_to_file(self, path: pathlib.Path):
        """Save all settings to the given file"""
        if path.exists():
            logging.info(f"File at {path} will be overwritten")
        else:
            logging.info(f"File at {path} will be created")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)

        # Construct master json to store all settings
        root_dict = dict()
        root_dict[self.KEY_SETTINGS_KEY] = [key_settings.data for key_settings in self.key_settings_list]
        root_dict[self.RGB_SETTINGS_KEY] = self.rgb_settings.data
        
        with path.open("w") as f:
            json.dump(root_dict, f, indent=4)


# FOR TESTING
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    fluxpad = Fluxpad(find_fluxpad_port())
    # fluxpad.open()

    settings = FluxpadSettings()
    try:
        with fluxpad.port as port:
            message = DigitalSettingsMessage()
            message.key_id = 0
            message.key_type = KeyType.KEYBOARD
            message.key_code = ScanCodeList.KEY_A.value.hid_keycode
            response = fluxpad.send_write_request(message)
            print(response.data)

            message = DigitalSettingsMessage()
            message.key_id = 0
            message.key_type = KeyType.NONE
            message.key_code = 0
            response = fluxpad.send_read_request(message)
            print(response.data)

            message = AnalogSettingsMessage()
            message.key_id = 2
            response = fluxpad.send_read_request(message)
            print(response.data)

            message = AnalogCalibrationMessage()
            message.set_zeros()
            message.key_id = 2
            response = fluxpad.send_read_request(message)
            print(response.data)

            message = AnalogReadMessage()
            message.set_zeros()
            message.key_id = 2
            response = fluxpad.send_read_request(message)
            print(response.data)

            new_message = DigitalSettingsMessage()
            new_message.set_zeros()
            print(new_message.data)

            response = fluxpad.send_read_request(new_message)
            print(response.data)
        
            settings.load_from_keypad(fluxpad)

            for key_settings in settings.key_settings_list:
                print(key_settings.data)

            filepath = pathlib.Path("testing/testy.json")
            settings.save_to_file(filepath)

            new_settings = FluxpadSettings()
            new_settings.load_from_file(filepath)
            new_settings.save_to_file(filepath.with_name("testy2.json"))

    except Exception:
        logging.exception("Exception encountered")

    def on_connect(fluxpad: Fluxpad):
        print(f"Connected to fluxpad {fluxpad.port.name}")

    def on_disconnect():
        print("Disconnected from fluxpad")

    listener = FluxpadListener(on_connect, on_disconnect)

    listener.start()

    time.sleep(10)

    listener.stop()