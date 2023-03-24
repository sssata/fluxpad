import enum
import json
from collections import deque
from typing import Deque, NamedTuple, Optional, TypedDict

import serial
import serial.tools.list_ports

from scancode_to_hid_code import KeyType


def find_fluxpad_port():
    serial_ports = serial.tools.list_ports.comports()
    for serial_port in serial_ports:
        if serial_port.pid == Fluxpad.PID and serial_port.vid == Fluxpad.VID:
            return serial_port.name
    return None


class MessageKey:
    TOKEN = "tkn"
    KEY_ID = "key"
    KEY_TYPE = "k_t"
    KEY_CODE = "k_c"
    ACTUATE_HYSTERESIS = "h_a"
    RELEASE_HYSTERESIS = "h_r"
    ACTUATE_POINT = "p_a"
    RELEASE_POINT = "p_a"
    RAPID_TRIGGER = "rt"
    RAW_ADC = "adc"
    HEIGHT = "ht"
    ACTUATE_DEBOUNCE = "d_a"
    RELEASE_DEBOUNCE = "d_a"
    ADC_SAMPLES = "a_s"
    CALIBRATION_UP = "c_u"
    CALIBRATION_DOWN = "c_d"
    DATASTREAM_MODE = "dstrm"
    DATASTREAM_FREQUENCY = "dstrm_freq"


class Message:

    def __init__(self, init_dict: Optional[dict] = None) -> None:
        if init_dict is None:
            init_dict = dict()
        self.data = init_dict

    def to_string(self) -> str:
        return json.dumps(self.data, indent=None, separators=(',', ':'))
    
    def to_bytes(self):
        return self.to_string().encode("ASCII")

    @property
    def token(self):
        return self.data[MessageKey.TOKEN]
    
    @token.setter
    def token(self, token: int):
        self._assert_uint8(token)
        self.data[MessageKey.TOKEN] = token

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
        self._assert_uint8(key_code)
        self.data[MessageKey.KEY_CODE] = key_code

    @property
    def key_type(self):
        return self.data[MessageKey.KEY_TYPE]
    
    @key_type.setter
    def key_type(self, key_type: int):
        self._assert_uint8(key_type)
        self.data[MessageKey.KEY_TYPE] = key_type

    # HYSTERESIS
    @property
    def actuate_hysteresis(self):
        return self.data[MessageKey.ACTUATE_HYSTERESIS]
    
    @actuate_hysteresis.setter
    def actuate_hysteresis(self, hysteresis_mm: float):
        assert isinstance(hysteresis_mm, float)
        assert 0 < hysteresis_mm
        self.data[MessageKey.ACTUATE_HYSTERESIS] = hysteresis_mm

    @property
    def release_hysteresis(self):
        return self.data[MessageKey.ACTUATE_HYSTERESIS]
    
    @release_hysteresis.setter
    def release_hysteresis(self, hysteresis_mm: float):
        assert isinstance(hysteresis_mm, float)
        assert 0 < hysteresis_mm
        self.data[MessageKey.RELEASE_HYSTERESIS] = hysteresis_mm

    # POINT
    @property
    def actuate_point(self):
        return self.data[MessageKey.ACTUATE_POINT]
    
    @actuate_point.setter
    def actuate_point(self, height_mm: float):
        assert isinstance(height_mm, float)
        assert 0 < height_mm
        self.data[MessageKey.ACTUATE_POINT] = height_mm

    @property
    def release_point(self):
        return self.data[MessageKey.RELEASE_POINT]
    
    @release_point.setter
    def release_point(self, height_mm: float):
        assert isinstance(height_mm, float)
        assert 0 < height_mm
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
    def release_debounce(self, debounce_ms: float):
        self._assert_uint8(debounce_ms)
        self.data[MessageKey.RELEASE_DEBOUNCE] = debounce_ms

    # CALIBRATION
    @property
    def calibration_up(self):
        return self.data[MessageKey.CALIBRATION_UP]
    
    @calibration_up.setter
    def calibration_up(self, up_adc: int):
        assert isinstance(up_adc, float)
        assert 0 < up_adc < 4096
        self.data[MessageKey.CALIBRATION_UP] = up_adc

    @property
    def calibration_down(self):
        return self.data[MessageKey.CALIBRATION_DOWN]
    
    @calibration_down.setter
    def calibration_down(self, down_adc: float):
        assert isinstance(down_adc, float)
        assert 0 < down_adc < 4096
        self.data[MessageKey.CALIBRATION_DOWN] = down_adc

    @property
    def adc_samples(self):
        return self.data[MessageKey.ADC_SAMPLES]
    
    @adc_samples.setter
    def adc_samples(self, adc_samples: float):
        self._assert_uint8(adc_samples)
        self.data[MessageKey.ADC_SAMPLES] = adc_samples

    # ANALOG KEY
    @property
    def raw_adc(self):
        return self.data[MessageKey.RAW_ADC]

    @property
    def height_mm(self):
        return self.data[MessageKey.HEIGHT]
    
    @property
    def rapid_trigger(self):
        return self.data[MessageKey.ADC_SAMPLES]
    
    @rapid_trigger.setter
    def rapid_trigger(self, rapid_trigger_enable: bool):
        assert isinstance(rapid_trigger_enable, bool)
        self.data[MessageKey.RAPID_TRIGGER] = rapid_trigger_enable

    @staticmethod
    def _assert_uint8(value):
        assert isinstance(value, int)
        assert 0x00 <= value <= 0xFF

class Fluxpad:

    VID = 0x1209
    PID = 0x7272
    BAUDRATE = 115200

    def __init__(self, port: str) -> None:
        self.port = serial.Serial()
        self.port.port = port
        self.port.baudrate = self.BAUDRATE
        self.port.bytesize = 8
        self.port.timeout = 0.1  # seconds
        self.last_token = 1
        self.incoming_msgs:Deque[Message] = deque()

    def get_next_token(self):
        self.last_token += 1
        if self.last_token > 255:
            self.last_token = 1
        return self.last_token
    
    def open(self):
        self.port.open()

    def close(self):
        self.port.close()

    def send_request(self, message: Message):
        message.token = self.get_next_token()
        self.port.write(message.to_bytes())
        self.port.read_until(expected="{", size=100)
        incoming_json_bytes = self.port.read_until(expected="}", size=1024)
        incoming_json = json.loads(incoming_json_bytes)
        return Message(incoming_json)


        
