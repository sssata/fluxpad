# Built-in
import tkinter as tk
from tkinter import ttk
from typing import Union, Optional, Callable, List, Type
from collections import deque
import logging
from tkinter import font
import pathlib
import time
import threading
import statistics
from tkinter import messagebox
from tkinter import filedialog
import math
import traceback
import sys
from PIL import Image, ImageTk

# Third Party
import pynput
import darkdetect

# First Party
from scancode_to_hid_code import (ScanCodeList, ScanCode, get_name_list,
                                  pynput_event_to_scancode, key_name_to_scancode, key_type_and_code_to_scancode)
import fluxpad_interface
import use_sv_ttk
from ttk_slider import SliderSetting
import firmware_updater


UpdateScancodeCallback = Callable[[ScanCode], None]

PADDING = 2
IS_DARKMODE = False

CALIBRATION_BAR_BG_COLOR = '#a0a0a0'
CALIBRATION_BAR_FG_COLOR = '#005fb8'


if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    print('running in a PyInstaller bundle')
    IMAGE_DIR = (pathlib.Path(__file__).parent / "images").resolve()
    BOSSAC_PATH = (pathlib.Path(__file__).parent / "tools" / "bossac.exe").resolve()
else:
    print('running in a normal Python process')
    IMAGE_DIR = (pathlib.Path(__file__).parent / "images").resolve()
    BOSSAC_PATH = (pathlib.Path(__file__).parent / "tools" / "bossac.exe").resolve()


class EncoderMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Encoder")

        self.cw_scancode: Optional[ScanCode] = None
        self.ccw_scancode: Optional[ScanCode] = None

        self.label_cw = ttk.Label(self, text="↻CW")
        self.label_cw.grid(row=1, column=1)
        self.label_ccw = ttk.Label(self, text="↺CCW")
        self.label_ccw.grid(row=2, column=1)

        self.label_cw_key = ttk.Label(self, text="None")
        self.label_cw_key.grid(row=1, column=2)
        self.label_ccw_key = ttk.Label(self, text="None")
        self.label_ccw_key.grid(row=2, column=2)

        self.btn_cw_edit = ttk.Button(self, text="Edit")
        self.btn_cw_edit.grid(row=1, column=3)
        self.btn_ccw_edit = ttk.Button(self, text="Edit")
        self.btn_ccw_edit.grid(row=2, column=3)

    def set_cw_keycode(self, scancode: ScanCode):
        assert isinstance(scancode, ScanCode), f"bruh {type(scancode)}"
        self.cw_scancode = scancode
        self.label_cw_key.configure(text=self.cw_scancode.name)

    def set_ccw_keycode(self, scancode: ScanCode):
        assert isinstance(scancode, ScanCode)
        self.ccw_scancode = scancode
        self.label_ccw_key.configure(text=self.ccw_scancode.name)


class KeyMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.scancode: Optional[ScanCode] = None

        self.mystyle = ttk.Style(self)
        btn_font = font.Font(family="Segoe UI", size=14, weight="bold")
        # self.mystyle.map("Bold.Accent.TButton", foreground=[("active", "blue"), ("!active", "blue")], relief=[("active", "sunken"),("!active", "sunken")])
        # self.mystyle.map("Bold.Accent.TButton", relief=[("pressed", "sunken"),("!pressed", "sunken")])
        # self.mystyle.configure("Bold.Accent.TButton", background="blue")

        self.mystyle.configure("Bold.TButton", font=btn_font)
        self.mystyle.configure("Bold.Accent.TButton", font=btn_font)

        self.btn_key = ttk.Button(self, text="None", takefocus=False, style="Bold.TButton")
        self.btn_key.pack(expand=True, fill="both", ipady=20, pady=(4,0))


    def set_scancode(self, scancode: ScanCode):
        self.scancode = scancode
        self.btn_key.configure(text=self.scancode.name)

    @property
    def key_name(self):
        return self["text"]
    
    def set_selected(self, selected: bool):
        if selected:
            self.btn_key.configure(style="Bold.Accent.TButton")

        else:
            self.btn_key.configure(style="Bold.TButton")

    def save_to_setting(self, setting: Union[fluxpad_interface.AnalogSettingsMessage, fluxpad_interface.DigitalSettingsMessage], key_id: Optional[int] = None):
        assert self.scancode is not None
        setting.key_code = self.scancode.hid_keycode
        setting.key_type = self.scancode.hid_usage
        if key_id is not None:
            setting.key_id = key_id

class MapEditFrame(ttk.Labelframe):
    """Represents a keymap edit section"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Edit")
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.label_a = ttk.Label(self, text="Press key or select from list: ")
        self.label_a.grid(row=1, column=1, sticky="E", padx=PADDING, pady=PADDING)

        self.label_key = ttk.Combobox(self, text="None", state="readonly", takefocus=False)
        self.label_key.grid(row=1, column=2, sticky="W", padx=PADDING, pady=PADDING)
        self.label_key['values'] = get_name_list()
        self.label_key.bind('<<ComboboxSelected>>', self.on_select_combobox)

        self.on_update_scancode_callback: Optional[UpdateScancodeCallback] = None

        # self.bind("<Visibility>", self.on_visiblity_change)
        self.is_active = True
        self.listener = pynput.keyboard.Listener(
            on_press=self.on_press)
        self.listener.start()

    def on_visiblity_change(self, event: tk.Event):
        logging.debug(f"Event {event}")

    def on_press(self, key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode]):

        # Only react to keyboard if pointer on applications
        try:
            if self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery()) is not None and self.is_active:
                new_scancode = pynput_event_to_scancode(key)
                logging.debug(f"Pressed {new_scancode.name}")
                self.on_scancode_update(new_scancode)
        except Exception:
            logging.warning("Key listener error")

    def on_select_combobox(self, event: tk.Event):
        scancode = key_name_to_scancode(self.label_key.get())
        logging.debug(f"Selected {scancode}")
        self.on_scancode_update(scancode)
        self.label_key.selection_clear()

    def on_scancode_update(self, scancode: ScanCode):
            self.label_key.set(scancode.name)
            if self.on_update_scancode_callback is not None:
                self.on_update_scancode_callback(scancode)
    

class KeymapFrame(ttk.Frame):
    """Represents a the keymap tab
    Contains the encoder map, key maps"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Create encoder map
        # self.lf_encoder = EncoderMap(self)
        # self.lf_encoder.grid(row=1, column=1, columnspan=2)
        # self.lf_encoder.set_cw_keycode(ScanCodeList.MEDIA_VOL_UP.value)
        # self.lf_encoder.set_ccw_keycode(ScanCodeList.MEDIA_VOL_DOWN.value)
        self.config(padding=PADDING)
        self.rowconfigure(1, pad=PADDING, weight=1)
        self.rowconfigure(2, pad=PADDING, weight=1)
        self.rowconfigure(3, pad=PADDING, weight=1)
        self.columnconfigure(1, pad=PADDING, weight=1)
        self.columnconfigure(2, pad=PADDING, weight=1)

        # Create encoer map
        self.lf_enc_ccw = KeyMap(self, text="Encoder ↺")
        self.lf_enc_ccw.grid(row=1, column=1, sticky="NSEW")
        self.lf_enc_ccw.set_scancode(ScanCodeList.MEDIA_VOL_DOWN.value)
        self.lf_enc_ccw.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_enc_ccw, event))

        self.lf_enc_cw = KeyMap(self, text="Encoder ↻")
        self.lf_enc_cw.grid(row=1, column=2, sticky="NSEW")
        self.lf_enc_cw.set_scancode(ScanCodeList.MEDIA_VOL_UP.value)
        self.lf_enc_cw.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_enc_cw, event))

        # Create key map
        self.lf_key1 = KeyMap(self, text="Digital Key 1")
        self.lf_key1.grid(row=2, column=1, sticky="NSEW")
        self.lf_key1.set_scancode(ScanCodeList.KEY_0x35.value)
        self.lf_key1.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_key1, event))

        self.lf_key2 = KeyMap(self, text="Digital Key 2")
        self.lf_key2.grid(row=2, column=2, sticky="NSEW")
        self.lf_key2.set_scancode(ScanCodeList.KEY_C.value)
        self.lf_key2.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_key2, event))

        self.lf_key3 = KeyMap(self, text="Analog Key 1")
        self.lf_key3.grid(row=3, column=1, sticky="NSEW")
        self.lf_key3.set_scancode(ScanCodeList.KEY_Z.value)
        self.lf_key3.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_key3, event))

        self.lf_key4 = KeyMap(self, text="Analog Key 2")
        self.lf_key4.grid(row=3, column=2, sticky="NSEW")
        self.lf_key4.set_scancode(ScanCodeList.KEY_X.value)
        self.lf_key4.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_key4, event))

        # Create Map Edit Frame
        self.lf_mapedit = MapEditFrame(self)
        self.lf_mapedit.grid(row=4, column=1, columnspan=2, sticky="NSEW")
        self.lf_mapedit.on_update_scancode_callback = self.on_scancode_update
        self.lf_mapedit.label_key.configure(state="disabled")  # start off disabled because no key is selected yet


        self.selected_keymap: Optional[KeyMap] = None

        # Set padding for all widgets
        for child in self.winfo_children():
            child.grid_configure(padx=PADDING, pady=PADDING)

    def on_press_keymap(self, keymap: KeyMap, event: tk.Event):
        if self.selected_keymap == keymap:
            self.selected_keymap.set_selected(False)
            self.selected_keymap = None
            logging.debug(f"Deselected key: {keymap.key_name}")
            self.lf_mapedit.label_key.configure(state="disabled")
        else:
            if self.selected_keymap is not None:
                self.selected_keymap.set_selected(False)
            self.selected_keymap = keymap
            self.selected_keymap.set_selected(True)
            self.lf_mapedit.label_key.configure(state="readonly")


            if keymap.scancode is not None:
                self.lf_mapedit.label_key.set(keymap.scancode.name)
                logging.debug(f"Selected key {self.selected_keymap.key_name} with scancode {keymap.scancode.name}")
        # logging.debug(type(self.currently_selected_keymap))
        
    def on_scancode_update(self, scancode: ScanCode):
        """Function that routes a selected scancode from the mapedit frame to the selected keymap frame"""
        if self.selected_keymap is not None:
            logging.debug(f"Set key {self.selected_keymap.key_name} to scancode: {scancode.name}")
            self.selected_keymap.set_scancode(scancode)

    def load_from_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        self.lf_key1.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[0].key_type, fluxpad_settings.key_settings_list[0].key_code))
        self.lf_key2.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[1].key_type, fluxpad_settings.key_settings_list[1].key_code))
        self.lf_key3.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[2].key_type, fluxpad_settings.key_settings_list[2].key_code))
        self.lf_key4.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[3].key_type, fluxpad_settings.key_settings_list[3].key_code))
        self.lf_enc_cw.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[4].key_type, fluxpad_settings.key_settings_list[4].key_code))
        self.lf_enc_ccw.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[5].key_type, fluxpad_settings.key_settings_list[5].key_code))


    def save_to_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        self.lf_key1.save_to_setting(fluxpad_settings.key_settings_list[0], 0)
        self.lf_key2.save_to_setting(fluxpad_settings.key_settings_list[1], 1)
        self.lf_key3.save_to_setting(fluxpad_settings.key_settings_list[2], 2)
        self.lf_key4.save_to_setting(fluxpad_settings.key_settings_list[3], 3)
        self.lf_enc_cw.save_to_setting(fluxpad_settings.key_settings_list[4], 4)
        self.lf_enc_ccw.save_to_setting(fluxpad_settings.key_settings_list[5], 5)


class AnalogSettingsPanel(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Analog Key Settings", padding=PADDING)

        # self.scancode: Optional[ScanCode] = None
        
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.rowconfigure(4, weight=0)
        self.rowconfigure(5, weight=0)
        self.rowconfigure(6, weight=0)
        self.rowconfigure(7, weight=0)
        self.columnconfigure(1, weight=1)
        # self.columnconfigure(2, weight=1)
        self.is_rapid_trigger = tk.BooleanVar(self)
        self.checkbox_rapid_trigger = ttk.Checkbutton(self, text="Rapid Trigger", variable=self.is_rapid_trigger, command=self.on_rapid_trigger_change)
        # self.checkbox_rapid_trigger.state(['!alternate'])  # Start unchecked
        self.is_rapid_trigger.set(False)  # Start unchecked
        self.checkbox_rapid_trigger.grid(row=1, column=1, sticky="W", padx=PADDING, pady=6)
        self.press_hysteresis = SliderSetting(self, text="Rapid Trigger Downstroke", var_type=float, min_value=0.05, max_value=1, resolution=0.05, units="mm")
        self.press_hysteresis.grid(row=2, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_hysteresis = SliderSetting(self, text=" Rapid Trigger Upstroke", var_type=float, min_value=0.05, max_value=1, resolution=0.05, units="mm")
        self.release_hysteresis.grid(row=3, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_point = SliderSetting(self, text="Rapid Trigger Range Upper Limit", var_type=float, min_value=2, max_value=4, resolution=0.05, units="mm")
        self.release_point.grid(row=4, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.actuation_point = SliderSetting(self, text="Rapid Trigger Range Lower Limit", var_type=float, min_value=0, max_value=2, resolution=0.05, units="mm")
        self.actuation_point.grid(row=5, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.press_debounce = SliderSetting(self, text="Rapid Trigger Press Debounce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.press_debounce.grid(row=6, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_debounce = SliderSetting(self, text="Rapid Trigger Release Debounce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.release_debounce.grid(row=7, column=1, sticky="EW", padx=PADDING, pady=PADDING)

        # Set default values
        self.press_debounce.set_value(1)
        self.release_debounce.set_value(6)
        self.press_hysteresis.set_value(0.1)
        self.release_hysteresis.set_value(0.4)
        self.release_point.set_value(3.7)
        self.actuation_point.set_value(0.3)
        self.on_rapid_trigger_change()


    def on_rapid_trigger_change(self):

        if self.is_rapid_trigger.get():
            self.release_point.configure(text="Rapid Trigger Range Upper Limit")
            self.actuation_point.configure(text="Rapid Trigger Range Lower Limit")
            self.release_hysteresis.slider.state(["!disabled"])
            self.press_hysteresis.slider.state(["!disabled"])

        else:
            self.release_point.configure(text="Release Point")
            self.actuation_point.configure(text="Actuation Point")
            self.release_hysteresis.slider.state(["disabled"])
            self.press_hysteresis.slider.state(["disabled"])


    def load_from_settings_message(self, message: fluxpad_interface.AnalogSettingsMessage):
        self.is_rapid_trigger.set(message.rapid_trigger)
        self.press_debounce.set_value(message.actuate_debounce)
        self.release_debounce.set_value(message.release_debounce)
        self.press_hysteresis.set_value(message.actuate_hysteresis)
        self.release_hysteresis.set_value(message.release_hysteresis)
        self.actuation_point.set_value(message.actuate_point - 2)  # Bottom out is 2mm in settings, while it's 0mm in GUI
        self.release_point.set_value(message.release_point - 2)
        self.on_rapid_trigger_change()

    def to_settings_message(self, message: fluxpad_interface.AnalogSettingsMessage):
        message.rapid_trigger = self.is_rapid_trigger.get()
        message.actuate_debounce = self.press_debounce.value
        message.release_debounce = self.release_debounce.value
        message.actuate_hysteresis = self.press_hysteresis.value
        message.release_hysteresis = self.release_hysteresis.value
        message.actuate_point = self.actuation_point.value + 2  # Bottom out is 2mm in settings, while it's 0mm in GUI
        message.release_point = self.release_point.value + 2

class DigitalSettingsPanel(ttk.Labelframe):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Digital Key Settings", padding=PADDING)

        # self.scancode: Optional[ScanCode] = None
        
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.debounce_press = SliderSetting(self, text="Press Debouce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.debounce_press.grid(row=1, column=1, sticky="EW", padx=PADDING, pady=PADDING)

        self.debounce_release = SliderSetting(self, text="Release Debouce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.debounce_release.grid(row=2, column=1, sticky="EW", padx=PADDING, pady=PADDING)

        self.debounce_press.set_value(1)
        self.debounce_release.set_value(6)

    def set_scancode(self, scancode: ScanCode):
        self.scancode = scancode

    def load_from_settings_message(self, message: fluxpad_interface.DigitalSettingsMessage):
        self.debounce_press.set_value(message.actuate_debounce)
        self.debounce_release.set_value(message.release_debounce)

    def to_settings_message(self, message: fluxpad_interface.DigitalSettingsMessage):
        message.actuate_debounce = self.debounce_press.value
        message.release_debounce = self.debounce_release.value


class SelectKeySettingsFrame(ttk.Labelframe):
    """Class representing the key selection panel on the setting tab"""
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Select Key", padding=PADDING)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)

        self.is_per_key_digital = tk.BooleanVar(self)
        self.is_per_key_analog = tk.BooleanVar(self)

        self.btn_list = [
            ttk.Button(self, text="Digital Key 1"),
            ttk.Button(self, text="Digital Key 2"),
            ttk.Button(self, text="Analog Key 1"),
            ttk.Button(self, text="Analog Key 2"),
        ]

        self.chk_per_key_digital = ttk.Checkbutton(self, text="Per Key Digital Settings", variable=self.is_per_key_digital, command=self.on_per_key_digital_click)
        self.chk_per_key_digital.state(['!alternate'])  # Start unchecked
        self.chk_per_key_digital.grid(row=1, column=1, columnspan=2, sticky="W", padx=PADDING)

        self.btn_list[0].grid(row=2, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.btn_list[1].grid(row=2, column=2, sticky="EW", padx=PADDING, pady=PADDING)

        self.chk_per_key_analog = ttk.Checkbutton(self, text="Per Key Analog Settings", variable=self.is_per_key_analog, command=self.on_per_key_analog_click)
        self.chk_per_key_analog.state(['!alternate'])  # Start unchecked
        self.chk_per_key_analog.grid(row=3, column=1, columnspan=2, sticky="W", padx=PADDING)

        self.btn_list[2].grid(row=4, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.btn_list[3].grid(row=4, column=2, sticky="EW", padx=PADDING, pady=PADDING)

        self.stl = ttk.Style(self)
        self.stl.configure("Sel.TButton", foreground="red")

        self.on_per_key_analog_click()
        self.on_per_key_digital_click()

    def on_per_key_analog_click(self):
        if self.is_per_key_analog.get():
            logging.debug("Set Per Key Analog")
            self.btn_list[2].grid_configure(columnspan=1)
            self.btn_list[2].configure(text="Analog Key 1")
            self.btn_list[3].grid(row=4, column=2, sticky="EW", padx=PADDING, pady=PADDING)
        else:
            logging.debug("Set Linked Analog")
            self.btn_list[2].grid_configure(columnspan=2)
            self.btn_list[3].grid_forget()
            self.btn_list[2].configure(text="Analog Keys")
        
    def on_per_key_digital_click(self):
        print( self.chk_per_key_digital.state())
        if self.is_per_key_digital.get():
            logging.debug("Set Per Key Digital")
            self.btn_list[0].grid_configure(columnspan=1)
            self.btn_list[0].configure(text="Digital Key 1")
            self.btn_list[1].grid(row=2, column=2, sticky="EW", padx=PADDING, pady=PADDING)
        else:
            logging.debug("Set Linked Digital")
            self.btn_list[1].grid_forget()
            self.btn_list[0].grid_configure(columnspan=2)
            self.btn_list[0].configure(text="Digital Keys")


class SettingsFrame(ttk.Frame):
    """Represents the settings tab"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # self.fluxpad_settings = fluxpad_settings

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(1, weight=1)

        self.key_select_frame = SelectKeySettingsFrame(self)
        self.key_select_frame.grid(row=1, column=1, sticky="NSEW")

            
        self.key_select_frame.btn_list[0].bind("<Button-1>", lambda event: self.on_select_key(event, 0))
        self.key_select_frame.btn_list[1].bind("<Button-1>", lambda event: self.on_select_key(event, 1))
        self.key_select_frame.btn_list[2].bind("<Button-1>", lambda event: self.on_select_key(event, 2))
        self.key_select_frame.btn_list[3].bind("<Button-1>", lambda event: self.on_select_key(event, 3))

        self.key_select_frame.chk_per_key_digital.bind("<Button-1>", self.on_select_per_key_digital)
        self.key_select_frame.chk_per_key_analog.bind("<Button-1>", self.on_select_per_key_analog)

        # self.scrollable_frame = ScrollableFrame(self)
        # self.scrollable_frame.grid(row=2, column=1, sticky="NSEW")
        self.settings_panel_list: List[Union[AnalogSettingsPanel, DigitalSettingsPanel]] = [
            DigitalSettingsPanel(self),
            DigitalSettingsPanel(self),
            AnalogSettingsPanel(self),
            AnalogSettingsPanel(self),
        ]

        # self.on_select_key("dummy event", 2)
        # self.analog_settings_panel = AnalogSettingsPanel(self)
        # self.analog_settings_panel.grid(row=2, column=1, sticky="NSEW")
        # self.digital_settings_panel = DigitalSettingsPanel(self)
        # self.digital_settings_panel.grid(row=2, column=1, sticky="NSEW")
        
        # Initialize State
        self.selected_settings_panel = -1
        self.on_select_key(None, 2)

    def on_select_per_key_digital(self, event:tk.Event):
        logging.debug("Selected per key digital")

        # Switch back to analog key 1 if currently on analog key 2
        if self.key_select_frame.is_per_key_digital.get() and self.selected_settings_panel == 1:
            self.on_select_key(tk.Event(), 0)
    

    def on_select_per_key_analog(self, event:tk.Event):
        logging.debug("Selected per key analog")

        # Switch back to digital key 1 if currently on digital key 2
        if self.key_select_frame.is_per_key_analog.get() and self.selected_settings_panel == 3:
            self.on_select_key(tk.Event(), 2)

    
    def on_select_key(self, event: tk.Event, key_id: int):
        """Callback for key selected"""
        logging.debug(f"Selected key {key_id}")

        # Don't do anything if we're already on the right panel
        if self.selected_settings_panel == key_id:
            return
        
        # Hide all settings frames
        self.settings_panel_list[self.selected_settings_panel].grid_forget()
        self.key_select_frame.btn_list[self.selected_settings_panel].configure(style="TButton")

        # Show selected settings frame
        self.settings_panel_list[key_id].grid(row=2, column=1, sticky="NSEW")
        self.selected_settings_panel = key_id

        # Change Title of settings frame according to circumstances
        if isinstance(self.settings_panel_list[key_id], AnalogSettingsPanel):
            if not self.key_select_frame.is_per_key_analog.get():
                self.settings_panel_list[key_id].configure(text="Analog Keys")
            else:
                self.settings_panel_list[key_id].configure(text=f"Analog Key {key_id-1}")

        elif isinstance(self.settings_panel_list[key_id], DigitalSettingsPanel):
            if not self.key_select_frame.is_per_key_digital.get():
                self.settings_panel_list[key_id].configure(text="Digital Keys")
            else:
                self.settings_panel_list[key_id].configure(text=f"Digital Key {key_id+1}")


        self.key_select_frame.btn_list[key_id].configure(style="Accent.TButton")

    def is_digital_equal(self, setting1: fluxpad_interface.DigitalSettingsMessage, setting2: fluxpad_interface.DigitalSettingsMessage):
        if (setting1.actuate_debounce == setting2.actuate_debounce and
            setting1.release_debounce == setting2.release_debounce):
            return True
        return False
    
    def is_analog_equal(self, setting1: fluxpad_interface.AnalogSettingsMessage, setting2: fluxpad_interface.AnalogSettingsMessage):
        if (setting1.actuate_debounce == setting2.actuate_debounce and
            setting1.release_debounce == setting2.release_debounce and
            setting1.actuate_hysteresis == setting2.actuate_hysteresis and
            setting1.release_hysteresis == setting2.release_hysteresis and
            setting1.actuate_point == setting2.actuate_point and 
            setting1.release_point == setting2.release_point and
            setting1.rapid_trigger == setting2.rapid_trigger):
            return True
        return False
    
    def assert_type(self, value, type: Type[fluxpad_interface.AnyMessage]):
        assert isinstance(value, type)
        return value

    def load_from_fluxpad_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        self.settings_panel_list[0].load_from_settings_message(self.assert_type(fluxpad_settings.key_settings_list[0], fluxpad_interface.DigitalSettingsMessage))
        self.settings_panel_list[1].load_from_settings_message(self.assert_type(fluxpad_settings.key_settings_list[1], fluxpad_interface.DigitalSettingsMessage))
        self.settings_panel_list[2].load_from_settings_message(self.assert_type(fluxpad_settings.key_settings_list[2], fluxpad_interface.AnalogSettingsMessage))
        self.settings_panel_list[3].load_from_settings_message(self.assert_type(fluxpad_settings.key_settings_list[3], fluxpad_interface.AnalogSettingsMessage))

        if (self.is_digital_equal(fluxpad_settings.key_settings_list[0], fluxpad_settings.key_settings_list[1])):
            self.key_select_frame.is_per_key_digital.set(False)
        else:
            self.key_select_frame.is_per_key_digital.set(True)
        self.key_select_frame.on_per_key_digital_click()

        
        if (self.is_analog_equal(fluxpad_settings.key_settings_list[2], fluxpad_settings.key_settings_list[3])):
            self.key_select_frame.is_per_key_analog.set(False)
        else:
            self.key_select_frame.is_per_key_analog.set(True)
        self.key_select_frame.on_per_key_analog_click()


    def save_to_fluxpad_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        self.settings_panel_list[0].to_settings_message(fluxpad_settings.key_settings_list[0])
        if not self.key_select_frame.is_per_key_digital.get():
            self.settings_panel_list[0].to_settings_message(fluxpad_settings.key_settings_list[1])
        else:
            self.settings_panel_list[1].to_settings_message(fluxpad_settings.key_settings_list[1])

        self.settings_panel_list[2].to_settings_message(fluxpad_settings.key_settings_list[2])
        
        if not self.key_select_frame.is_per_key_analog.get():
            self.settings_panel_list[2].to_settings_message(fluxpad_settings.key_settings_list[3])
        else:
            self.settings_panel_list[3].to_settings_message(fluxpad_settings.key_settings_list[3])


class LightingFrame(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master=master)

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(1, weight=1)

        self.key_select_frame = SelectKeySettingsFrame(self)
        self.key_select_frame.grid(row=1, column=1, sticky="NSEW")

        self.label_wip = ttk.Label(self, text="Lighting Settings Coming Soon")
        self.label_wip.grid(row=2, column=1)



class AnalogCalibrationFrame(ttk.Frame):
    BAR_WIDTH_PX = 20
    BAR_HEIGHT_PX = 100
    BAR_MAX_MM = 4

    def __init__(self, master=None):
        super().__init__(master=master)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.configure(padding=PADDING)

        self.height_bar = tk.Canvas(self, width=self.BAR_WIDTH_PX, height=self.BAR_HEIGHT_PX, background=CALIBRATION_BAR_BG_COLOR, highlightthickness=0, borderwidth=0)
        self.height_bar.grid(row=1, column=1, rowspan=2, padx=PADDING, pady=PADDING)
        self.btn_set_up = ttk.Button(self, text="Set Switch Up Position", width=20)
        self.btn_set_up.grid(row=1, column=2, sticky="W", padx=PADDING, pady=PADDING)
        self.btn_set_down = ttk.Button(self, text="Set Switch Down Position", width=20)
        self.btn_set_down.grid(row=2, column=2, sticky="W", padx=PADDING, pady=PADDING)

    def update_height(self, height_mm):
        bar_height_px = round(height_mm / self.BAR_MAX_MM * self.BAR_HEIGHT_PX)
        self.height_bar.delete("bar")
        self.height_bar.create_rectangle(0, self.BAR_HEIGHT_PX, self.BAR_WIDTH_PX, self.BAR_HEIGHT_PX - bar_height_px, tags="bar", fill=CALIBRATION_BAR_FG_COLOR, width=0)
        self.height_bar.update()
        logging.debug(f"height_mm {height_mm}")


class CalibrationLabelframe(ttk.Labelframe):

    def __init__(self, master=None):
        super().__init__(master=master)
        self.configure(text="Calibration")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        self.notebook = ttk.Notebook(self, takefocus=False)
        self.analog_cal_frame_list = [
            AnalogCalibrationFrame(self.notebook),
            AnalogCalibrationFrame(self.notebook)
        ]
        
        self.notebook.add(self.analog_cal_frame_list[0], text="Analog Button 1")
        self.notebook.add(self.analog_cal_frame_list[1], text="Analog Button 2")
        self.notebook.grid(row=1, column=1, sticky="EW")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_notebook_tab_changed)
        self.current_selected_analog_key = 0

    def on_notebook_tab_changed(self, event: tk.Event):
        """"Turn on and off keyboard listener and calibration worker based on which tab is active"""
        self.current_selected_analog_key = self.notebook.index("current")

        # if self.notebook.index("current") == 0:  # Check if tab on top is keymap tab




class UtilitiesFrame(ttk.Frame):
    """Top level frame of the utilities tab"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(1, weight=1)

        self.calibration_labelframe = CalibrationLabelframe(self)
        self.calibration_labelframe.grid(row=1, column=1, sticky="NEW")

        test_label = tk.Label(self, text="Warning: keypad may not work as expected with utilities tab open")
        test_label.grid(row=2, column=1, sticky="NEW")

        # Don't show firmware update for now
        self.firmware_update_frame = firmware_updater.FirmwareUpdateFrame(self)
        # self.firmware_update_frame.grid(row=3, column=1, sticky="NEW")


class CalibrationTopLevel(tk.Toplevel):
    """Top Level window that holds the calibration routine"""

    # Calibration settings and validation constants
    NUMBER_OF_SAMPLES = 20
    SAMPLE_PERIOD_S = 0.05

    UP_MAX_STD_DEV = 40
    UP_MAX_ADC = 1300
    UP_MIN_ADC = 0

    DOWN_MAX_STD_DEV = 200
    DOWN_MAX_ADC = 4096
    DOWN_MIN_ADC = 2100

    INSTRUCTION_WIDTH = 500
    INSTRUCTION_HEIGHT = 240

    def __init__(self, master, is_up: int, fluxpad: fluxpad_interface.Fluxpad, key_id: int, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        assert isinstance(is_up, int)
        assert isinstance(key_id, int)
        assert isinstance(fluxpad, fluxpad_interface.Fluxpad)

        self.is_up = is_up
        self.key_id = key_id
        self.fluxpad = fluxpad
        if self.is_up: 
            self.title("Calibrate Up Positon")
        else:
            self.title("Calibrate Down Positon")

        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)

        # Instructions
        self.instructions = tk.Canvas(self, width=self.INSTRUCTION_WIDTH, height=self.INSTRUCTION_HEIGHT, highlightthickness=0, borderwidth=0)
        try:
            image_name = f"cal_key{self.key_id-1}_{'up' if self.is_up else 'down'}.png"
            self.instruction_image = ImageTk.PhotoImage(Image.open(IMAGE_DIR / image_name))
            self.instructions.create_image(0,0,image=self.instruction_image, anchor=tk.NW)
        except Exception:
            logging.error(f"Failed to load image {IMAGE_DIR / image_name}", exc_info=True)
            messagebox.showerror("Exception", f"Failed to load image\n\n{traceback.format_exc()}")

        self.instructions.grid(row=1, column=1, columnspan=2)


        # Progress bar
        self.pb = ttk.Progressbar(self, maximum=100, length=200, orient='horizontal', mode='indeterminate')
        self.pb.grid(row=2, column=1, columnspan=2, sticky="EW", padx=PADDING, pady=PADDING)

        # Cancel Button
        self.btn_cancel = ttk.Button(self, text="Cancel", command=self.on_cancel)
        self.btn_cancel.grid(row=3, column=1, sticky="EW", padx=PADDING, pady=PADDING)

        # Calibrate Button
        self.btn_calibrate = ttk.Button(self, text="Calibrate", command=self.on_calibrate)
        self.btn_calibrate.grid(row=3, column=2, sticky="EW", padx=PADDING, pady=PADDING)

        # Checks
        assert not self.fluxpad.port.is_open, "Port is still open!"
        self.grab_set()
        self.update()
        self.update_idletasks()

    def on_cancel(self):
        logging.info("Canceled Calibration")
        self.destroy()
    
    def on_calibrate(self):
        """Callback that runs when calibrate button is pressed"""
        self.btn_cancel.state(["disabled"])
        self.update()
        self.update_idletasks()
        pb_step_size = 100/self.NUMBER_OF_SAMPLES
        message = fluxpad_interface.AnalogReadMessage()
        message.raw_adc = 0
        message.key_id = self.key_id

        # Collect raw adc samples
        read_adc_queue = deque()
        try:
            with self.fluxpad.port:
                for i in range(self.NUMBER_OF_SAMPLES):
                    response = self.fluxpad.send_read_request(message)
                    read_adc_queue.append(response.raw_adc)
                    self.pb.step(pb_step_size)
                    time.sleep(self.SAMPLE_PERIOD_S)
                    self.update()

        except Exception:
            logging.error("Error gathering data during calibration", exc_info=True)
            messagebox.showerror("Calibration Error", f"Exception {traceback.format_exc()}")
            self.destroy()
            return

        # Prepare calibration validation
        if self.is_up:
            max_std_dev = self.UP_MAX_STD_DEV
            max_adc = self.UP_MAX_ADC
            min_adc = self.UP_MIN_ADC

        else:
            max_std_dev = self.DOWN_MAX_STD_DEV
            max_adc = self.DOWN_MAX_ADC
            min_adc = self.DOWN_MIN_ADC

        # Run calibration validation
        std_dev = statistics.pstdev(read_adc_queue)
        mean = statistics.mean(read_adc_queue)
        logging.info(f"Std dev: {std_dev}, Mean: {mean}")
        error_str = None
        if std_dev > max_std_dev:
            error_str = f"Std Deviation is too high: {std_dev} > {max_std_dev}"
            logging.error(error_str)

        if mean > max_adc:
            error_str = f"Reading is too high: {mean:.0f} > {max_adc}, is the key fully released?"
            logging.error(error_str)
        
        if mean < min_adc:
            error_str = f"Reading is too low: {mean:.0f} < {min_adc}, is the key fully depressed?"
            logging.error(error_str)
                    
        if error_str is not None:
            messagebox.showerror("Calibration Error", f"Failed to calibrate:\n{error_str}")
            self.destroy()
            return
        
        # Prepare calibration message
        calibrate_message = fluxpad_interface.AnalogCalibrationMessage()
        calibrate_message.key_id = self.key_id
        if self.is_up:
            calibrate_message.calibration_up = mean
        else:
            calibrate_message.calibration_down = mean

        # Send calibration message
        try:
            with self.fluxpad.port:
                self.fluxpad.send_write_request(calibrate_message)
                calibrate_echo = self.fluxpad.send_read_request(calibrate_message)
                if self.is_up:
                    assert math.isclose(mean, calibrate_echo.calibration_up, rel_tol=1e-4), f"{mean} not equal to {calibrate_echo.calibration_up}"
                else:
                    assert math.isclose(mean, calibrate_echo.calibration_down, rel_tol=1e-4), f"{mean} not equal to {calibrate_echo.calibration_down}"
        except Exception:
            messagebox.showerror("Calibration Error", f"Exception {traceback.format_exc()}")
            self.destroy()
            return
        

        messagebox.showinfo("Calibration Complete", f"Analog Key {self.key_id-1} {'up' if self.is_up else 'down'} position calibrated to\n{mean:.0f} ADC counts")
        self.destroy()



class Application(ttk.Frame):
    """Top Level application frame"""

    CALIBRATION_MODE_UPDATE_PERIOD_S = 0.05

    def __init__(self, master=None):
        super().__init__(master=master)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # Create notebook
        self.notebook = ttk.Notebook(self, takefocus=False)

        # Create tabs
        self.frame_keymap = KeymapFrame(self.notebook)
        self.frame_settings = SettingsFrame(self.notebook)
        self.frame_lighting = LightingFrame(self.notebook)
        self.frame_utilities = UtilitiesFrame(self.notebook)

        # Add tabs
        self.notebook.add(self.frame_keymap, text="Keymap")
        self.notebook.add(self.frame_settings, text="Settings")
        self.notebook.add(self.frame_lighting, text="Lighting")
        self.notebook.add(self.frame_utilities, text="Utilities")
        
        self.notebook.grid(row=1, column=1, sticky="NSEW", pady=(0, 4), padx=4)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_notebook_tab_changed)

        self.btn_upload = ttk.Button(self, text="Save to Fluxpad", command=self.on_save_to_fluxpad)
        self.btn_upload.grid(row=2, column=1, sticky="NSEW", padx=PADDING, pady=PADDING)

        # Create menubar
        self.menubar = tk.Menu(self.master)

        # Load menu
        self.load_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Load", menu=self.load_menu)
        self.load_menu.add_command(label="Load from File", command=self.on_load_from_file)
        self.load_menu.add_command(label="Load from FLUXPAD", command=self.on_load_from_fluxpad)

        # Save menu
        self.save_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Save", menu=self.save_menu)
        self.save_menu.add_command(label="Save to File", command=self.on_save_to_file)
        self.save_menu.add_command(label="Save to FLUXPAD", command=self.on_save_to_fluxpad)

        # Wire calibration button to callback
        self.frame_utilities.calibration_labelframe.analog_cal_frame_list[0].btn_set_up.configure(command=lambda: self.on_calibrate_button(is_up=True, key_id=2))
        self.frame_utilities.calibration_labelframe.analog_cal_frame_list[0].btn_set_down.configure(command=lambda: self.on_calibrate_button(is_up=False, key_id=2))

        self.frame_utilities.calibration_labelframe.analog_cal_frame_list[1].btn_set_up.configure(command=lambda: self.on_calibrate_button(is_up=True, key_id=3))
        self.frame_utilities.calibration_labelframe.analog_cal_frame_list[1].btn_set_down.configure(command=lambda: self.on_calibrate_button(is_up=False, key_id=3))

        # Show menu bar
        self.master.configure(menu=self.menubar)

        # Default GUI state to fluxpad disconnected
        self.on_disconnected()

        # Setup Fluxpad interface and connection listener
        self.fluxpad_settings = fluxpad_interface.FluxpadSettings()
        self._save_to_settings()
        self.fluxpad: Optional[fluxpad_interface.Fluxpad] = None
        self.listener = fluxpad_interface.FluxpadListener(self.on_connected, self.on_disconnected)
        self.listener.start()

        self.calibration_worker_thread = threading.Thread(target=self._calibration_worker, daemon=True)
        self.calibration_worker_thread.start()
        self.worker_busy = True

    def on_connected(self, fluxpad: fluxpad_interface.Fluxpad):
        logging.info(f"Fluxpad Connected on port {fluxpad.port.name}")
        self.fluxpad = fluxpad
        self._on_connected_gui()

    def on_disconnected(self):
        logging.info("Fluxpad Disconnected")
        self.fluxpad = None
        self._on_disconnected_gui()
    
    def _on_connected_gui(self):
        self.btn_upload.state(["!disabled"])
        self.save_menu.entryconfigure(1, state=tk.NORMAL)
        self.load_menu.entryconfigure(1, state=tk.NORMAL)
        self.ask_load_from_fluxpad()

        # Wire firmware update button to callback
        self.frame_utilities.firmware_update_frame.enable_update()
        self.frame_utilities.firmware_update_frame.set_fluxpad(self.fluxpad)

    def _on_disconnected_gui(self):
        self.btn_upload.state(["disabled"])
        self.save_menu.entryconfigure(1, state=tk.DISABLED)
        self.load_menu.entryconfigure(1, state=tk.DISABLED)
        self.frame_utilities.firmware_update_frame.disable_update()


    def ask_load_from_fluxpad(self):
        should_load = messagebox.askyesno("Fluxpad Connected", "Load settings from connected FLUXPAD?")
        if should_load:
            self.on_load_from_fluxpad()

    def _calibration_worker(self):
        while True:

            # Wait for fluxpad connection and calibration tap open
            if self.fluxpad is not None and self.on_calibration_tab:
                while True:
                    
                    if self.fluxpad is None or not self.on_calibration_tab:
                        logging.debug("Stopping")
                        try:
                            if self.fluxpad is not None and self.fluxpad.port.is_open:
                                self.fluxpad.port.close()
                        except fluxpad_interface.serial.SerialException:
                            logging.info(f"Serial exception {self.fluxpad.port.name}")
                        else:
                            logging.info(f"Closed port")
                        break

                    self.worker_busy = True
                    try:
                        if not self.fluxpad.port.is_open:
                            self.fluxpad.port.open()
                            logging.info(f"Opened port {self.fluxpad.port.name}")
                        selected_analog_key = self.frame_utilities.calibration_labelframe.current_selected_analog_key
                        message = fluxpad_interface.AnalogReadMessage()
                        message.height_mm = 0
                        message.key_id = selected_analog_key + 2  # convert from analog key name (ie analog key 1 or 2) to key id
                        response = self.fluxpad.send_read_request(message)
                        self.frame_utilities.calibration_labelframe.analog_cal_frame_list[selected_analog_key].update_height(response.height_mm - 2)
                    except fluxpad_interface.serial.SerialException:
                        logging.info(f"Serial exception {self.fluxpad.port.name}")
                    except Exception:
                        logging.error("Exception at calibration worker", exc_info=1)
                    finally:
                        self.worker_busy = False
                    time.sleep(self.CALIBRATION_MODE_UPDATE_PERIOD_S)
                

            time.sleep(self.CALIBRATION_MODE_UPDATE_PERIOD_S)

    def on_calibrate_button(self, is_up, key_id):
        logging.info("Calibration button clicked")
        assert 2 <= key_id <=3, "Invalid key id"
        self.on_calibration_tab = False
        while self.fluxpad.port.is_open or self.worker_busy:
            self.on_calibration_tab = False
            logging.debug("Waiting for port to close")
            time.sleep(0.1)
        newWindow = CalibrationTopLevel(self, is_up, self.fluxpad, key_id)
        newWindow.wait_window()
        self.grab_set()
        logging.info("Calibration complete")
        self.on_notebook_tab_changed(tk.Event())
        self.update()

    def on_notebook_tab_changed(self, event: tk.Event):
        """"Turn on and off keyboard listener and calibration worker based on which tab is active"""

        if self.notebook.index("current") == 0:  # Check if tab on top is keymap tab
            self.frame_keymap.lf_mapedit.is_active = True
        else: 
            self.frame_keymap.lf_mapedit.is_active = False
        
        if self.notebook.index("current") == 3:  # Check if tab on top is utilities tab
            self.on_calibration_tab = True
        else:
            self.on_calibration_tab = False

    def _update_from_settings(self):
        self.frame_keymap.load_from_settings(self.fluxpad_settings)
        self.frame_settings.load_from_fluxpad_settings(self.fluxpad_settings)

    def _save_to_settings(self):
        """Take all settings currently set in the GUI and load them to the self.fluxpad_settings object"""
        self.frame_keymap.save_to_settings(self.fluxpad_settings)
        self.frame_settings.save_to_fluxpad_settings(self.fluxpad_settings)

    def on_load_from_file(self):
        try:
            load_file = filedialog.askopenfilename(
                parent=self,
                filetypes=[("Fluxpad settings file", ".json")]
            )
            pathlib.Path(load_file)
            self.fluxpad_settings.load_from_file(pathlib.Path(load_file))
            self._update_from_settings()
        except Exception:
            logging.error("Exception occoured while loading from fluxpad", exc_info=True)
            messagebox.showerror("Error Loading from fluxpad", f"Exception:\n{traceback.format_exc()}")
        else:
            messagebox.showinfo("Loaded settings",f"Loaded settings from file: {load_file}")

    def on_load_from_fluxpad(self):
        try:
            with self.fluxpad.port:
                self.fluxpad_settings.load_from_keypad(self.fluxpad)
            self._update_from_settings()
        except Exception:
            logging.error("Exception occoured while loading from FLUXPAD", exc_info=True)
            messagebox.showerror("Error Loading from FLUXPAD", f"Exception:\n{traceback.format_exc()}")
        else:
            messagebox.showinfo("Loaded settings","Loaded settings from FLUXPAD")
    
    def on_save_to_file(self):
        try:
            save_file = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".json",
                filetypes=[("Fluxpad settings file", ".json")]
            )
            self._save_to_settings()
            self.fluxpad_settings.save_to_file(pathlib.Path(save_file))
        except Exception:
            logging.error("Exception occoured while saving to file", exc_info=True)
            messagebox.showerror("Error Saving to FLUXPAD", f"Exception:\n{traceback.format_exc()}")
        else:
            messagebox.showinfo("Saved settings", f"Saved settings to {save_file}")

    def on_save_to_fluxpad(self):
        try:
            self._save_to_settings()
            with self.fluxpad.port:
                self.fluxpad_settings.save_to_fluxpad(self.fluxpad)
        except Exception:
            logging.error("Exception occoured while saving to FLUXPAD", exc_info=True)
            messagebox.showerror("Error Saving to FLUXPAD", f"Exception:\n{traceback.format_exc}")
        else:
            messagebox.showinfo("Saved settings", "Saved settings to FLUXPAD")

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # keyboard.hook(callback=keyboard_callback)

    root = tk.Tk()
    
    try:
        IS_DARKMODE = darkdetect.isDark()
    except Exception:
        logging.warning("Cannot determine darkmode")

    if IS_DARKMODE:
        ...
        use_sv_ttk.set_theme("dark")
    else:
        ...
        use_sv_ttk.set_theme("light")

    WIDTH = 400
    HEIGHT = 580

    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = int((ws/2) - (WIDTH/2))
    y = int((hs/2) - (HEIGHT/2))
        
    root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
    root.resizable(width=False, height=False)
    root.title("FLUXAPP")
    root.iconbitmap((IMAGE_DIR / "FluxappIcon.ico").resolve())
    app = Application(master=root)
    app.pack(expand=True, fill="both", side="top")
    app.mainloop()
