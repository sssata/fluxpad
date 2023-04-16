import tkinter as tk
from tkinter import ttk
from typing import Union, Optional, Callable, List
import logging
from tkinter import font
import pathlib
import re

import pynput
import darkdetect

from scancode_to_hid_code import (ScanCodeList, ScanCode, get_name_list,
                                  pynput_event_to_scancode, key_name_to_scancode, key_type_and_code_to_scancode)
import fluxpad_interface
import use_sv_ttk
from ttk_slider import SliderSetting

UpdateScancodeCallback = Callable[[ScanCode], None]

PADDING = 2
IS_DARKMODE = False

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

    def save_to_setting(self, setting: Union[fluxpad_interface.AnalogSettingsMessage, fluxpad_interface.DigitalSettingsMessage]):
        setting.key_code = self.scancode.hid_keycode
        setting.key_type = self.scancode.hid_usage

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
        if self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery()) is not None and self.is_active:
            new_scancode = pynput_event_to_scancode(key)
            logging.debug(f"Pressed {new_scancode.name}")
            self.on_scancode_update(new_scancode)

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
        self.lf_enc_ccw.set_scancode(ScanCodeList.MEDIA_VOL_UP.value)
        self.lf_enc_ccw.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_enc_ccw, event))

        self.lf_enc_cw = KeyMap(self, text="Encoder ↻")
        self.lf_enc_cw.grid(row=1, column=2, sticky="NSEW")
        self.lf_enc_cw.set_scancode(ScanCodeList.MEDIA_VOL_DOWN.value)
        self.lf_enc_cw.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_enc_cw, event))

        # Create key map
        self.lf_key1 = KeyMap(self, text="Digital Key 1")
        self.lf_key1.grid(row=2, column=1, sticky="NSEW")
        self.lf_key1.set_scancode(ScanCodeList.KEY_A.value)
        self.lf_key1.btn_key.bind("<Button-1>", lambda event: self.on_press_keymap(self.lf_key1, event))

        self.lf_key2 = KeyMap(self, text="Digital Key 2")
        self.lf_key2.grid(row=2, column=2, sticky="NSEW")
        self.lf_key2.set_scancode(ScanCodeList.KEY_S.value)
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
        self.lf_enc_ccw.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[4].key_type, fluxpad_settings.key_settings_list[4].key_code))
        self.lf_enc_cw.set_scancode(key_type_and_code_to_scancode(fluxpad_settings.key_settings_list[5].key_type, fluxpad_settings.key_settings_list[5].key_code))


    def save_to_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        self.lf_key1.save_to_setting(fluxpad_settings.key_settings_list[0])
        self.lf_key2.save_to_setting(fluxpad_settings.key_settings_list[1])
        self.lf_key3.save_to_setting(fluxpad_settings.key_settings_list[2])
        self.lf_key4.save_to_setting(fluxpad_settings.key_settings_list[3])
        self.lf_enc_ccw.save_to_setting(fluxpad_settings.key_settings_list[4])
        self.lf_enc_cw.save_to_setting(fluxpad_settings.key_settings_list[5])


class AnalogSettingsPanel(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Analog Key Settings", padding=PADDING)

        # self.scancode: Optional[ScanCode] = None
        
        # self.label_rapid_trigger = ttk.Label(self, text="Rapid Trigger")
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
        self.checkbox_rapid_trigger = ttk.Checkbutton(self, text="Rapid Trigger", variable=self.is_rapid_trigger)
        # self.checkbox_rapid_trigger.state(['!alternate'])  # Start unchecked
        self.is_rapid_trigger.set(False)  # Start unchecked
        self.checkbox_rapid_trigger.grid(row=1, column=1, sticky="W", padx=PADDING, pady=6)
        self.press_hysteresis = SliderSetting(self, text="Rapid Trigger Upstroke", var_type=float, min_value=0.05, max_value=1, resolution=0.05, units="mm")
        self.press_hysteresis.grid(row=2, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_hysteresis = SliderSetting(self, text=" Rapid Trigger Downstroke", var_type=float, min_value=0.05, max_value=1, resolution=0.05, units="mm")
        self.release_hysteresis.grid(row=3, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_point = SliderSetting(self, text="Rapid Trigger Upper Limit", var_type=float, min_value=2, max_value=4, resolution=0.05, units="mm")
        self.release_point.grid(row=4, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.actuation_point = SliderSetting(self, text="Rapid Trigger Lower Limit", var_type=float, min_value=0, max_value=2, resolution=0.05, units="mm")
        self.actuation_point.grid(row=5, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.press_debounce = SliderSetting(self, text="Rapid Trigger Press Debounce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.press_debounce.grid(row=6, column=1, sticky="EW", padx=PADDING, pady=PADDING)
        self.release_debounce = SliderSetting(self, text="Rapid Trigger Release Debounce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.release_debounce.grid(row=7, column=1, sticky="EW", padx=PADDING, pady=PADDING)

    def load_from_settings_message(self, message: fluxpad_interface.AnalogSettingsMessage):
        self.is_rapid_trigger.set(message.rapid_trigger)
        self.press_debounce.set_value(message.actuate_debounce)
        self.release_debounce.set_value(message.release_debounce)
        self.press_hysteresis.set_value(message.actuate_hysteresis)
        self.release_hysteresis.set_value(message.release_hysteresis)
        self.actuation_point.set_value(message.actuate_point - 2)  # Bottom out is 2mm in settings, while it's 0mm in GUI
        self.release_point.set_value(message.release_point - 2)

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
        
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.debounce_press = SliderSetting(self, text="Press Debouce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.debounce_press.grid(row=1, column=1, sticky="EW")

        self.debounce_release = SliderSetting(self, text="Release Debouce", var_type=int, min_value=0, max_value=20, resolution=1, decimal_places=0, units="ms")
        self.debounce_release.grid(row=2, column=1, sticky="EW")

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
        if self.key_select_frame.is_per_key_digital.get() and self.selected_settings_panel == 1:
            self.on_select_key(None, 0)
    

    def on_select_per_key_analog(self, event:tk.Event):
        logging.debug("Selected per key analog")
        if self.key_select_frame.is_per_key_analog.get() and self.selected_settings_panel == 3:
            self.on_select_key(None, 2)

    
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

        # Change Set Title of settings frame
        if isinstance(self.settings_panel_list[key_id], AnalogSettingsPanel) and not self.key_select_frame.is_per_key_analog.get():
            self.settings_panel_list[key_id].configure(text="Analog Keys")
        else:
            self.settings_panel_list[key_id].configure(text=f"Analog Key {key_id-1}")

        if isinstance(self.settings_panel_list[key_id], DigitalSettingsPanel) and not self.key_select_frame.is_per_key_digital.get():
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

    def load_from_fluxpad_settings(self, fluxpad_settings: fluxpad_interface.FluxpadSettings):
        # self.fluxpad_settings = fluxpad_settings
        self.settings_panel_list[0].load_from_settings_message(fluxpad_settings.key_settings_list[0])
        self.settings_panel_list[1].load_from_settings_message(fluxpad_settings.key_settings_list[1])
        self.settings_panel_list[2].load_from_settings_message(fluxpad_settings.key_settings_list[2])
        self.settings_panel_list[3].load_from_settings_message(fluxpad_settings.key_settings_list[3])

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


class UtilitiesFrame(ttk.Frame):
    """Represents the settings tab"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        test_label = tk.Label(self, text="Coming Soon")
        test_label.pack()


class Application(ttk.Frame):
    """Top Level application frame"""

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
        self.frame_utilities = UtilitiesFrame(self.notebook)

        # Add tabs
        self.notebook.add(self.frame_keymap, text="Keymap")
        self.notebook.add(self.frame_settings, text="Settings")
        self.notebook.add(self.frame_utilities, text="Utilities")
        
        self.notebook.grid(row=1, column=1, sticky="NSEW", pady=(0, 4), padx=4)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_notebook_tab_changed)

        self.btn_upload = ttk.Button(self, text="Upload")
        self.btn_upload.grid(row=2, column=1, sticky="NSEW")

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

        # Show menu bar
        self.master.configure(menu=self.menubar)

        # Setup Fluxpad interface
        self.fluxpad_settings = fluxpad_interface.FluxpadSettings()
        self.fluxpad: Optional[fluxpad_interface.Fluxpad] = None
        self.listener = fluxpad_interface.FluxpadListener(self.on_connected, self.on_disconnected)
        self.listener.start()

    def on_connected(self, fluxpad: fluxpad_interface.Fluxpad):
        logging.info(f"Fluxpad Connected on port {fluxpad.port.name}")
        self.fluxpad = fluxpad
        self._on_connected_gui()

    def on_disconnected(self):
        logging.info(f"Fluxpad Disconnected")
        self.fluxpad = None
        self._on_disconnected_gui()
    
    def _on_connected_gui(self):
        self.btn_upload.state(["!disabled"])
        self.save_menu.entryconfigure(1, state=tk.NORMAL)
        self.load_menu.entryconfigure(1, state=tk.NORMAL)

    def _on_disconnected_gui(self):
        self.btn_upload.state(["disabled"])
        self.save_menu.entryconfigure(1, state=tk.DISABLED)
        self.load_menu.entryconfigure(1, state=tk.DISABLED)

    def on_notebook_tab_changed(self, event: tk.Event):
        """"Turn on and off keyboard listensr based on which tab is active"""

        if self.notebook.index("current") == 0:  # Check if tab on top is keymap tab
            self.frame_keymap.lf_mapedit.is_active = True
        else: 
            self.frame_keymap.lf_mapedit.is_active = False

    def _update_from_settings(self):
        self.frame_keymap.load_from_settings(self.fluxpad_settings)
        self.frame_settings.load_from_fluxpad_settings(self.fluxpad_settings)

    def _save_to_settings(self):
        self.frame_keymap.save_to_settings(self.fluxpad_settings)
        self.frame_settings.save_to_fluxpad_settings(self.fluxpad_settings)

    def on_load_from_file(self):
        self.fluxpad_settings.load_from_file(pathlib.Path(__file__).parent / "testy.json")
        self._update_from_settings()

    def on_save_to_file(self):
        self._save_to_settings()
        self.fluxpad_settings.save_to_file(pathlib.Path(__file__).parent / "testy_out.json")
    
    def on_load_from_fluxpad(self):
        with self.fluxpad.port:
            self.fluxpad_settings.load_from_keypad(self.fluxpad)
        self._update_from_settings()
    
    def on_save_to_fluxpad(self):
        self._save_to_settings()
        with self.fluxpad.port:
            self.fluxpad_settings.save_to_fluxpad(self.fluxpad)

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
        
    # root.geometry("600x600")
    root.title("FLUXAPP")
    app = Application(master=root)
    app.pack(expand=True, fill="both", side="top")
    app.mainloop()
