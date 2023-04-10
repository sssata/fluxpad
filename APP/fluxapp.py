import tkinter as tk
from tkinter import ttk
from typing import Union, Optional, Callable, NewType, TypeVar
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
from tickscale import TickScale

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


class SliderSetting(ttk.Labelframe):

    def __init__(self, master, var_type: type = float, min_value = 0, max_value = 1, resolution = 0.1, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.resolution = resolution
        self.var_type = var_type
        self.value: Optional[var_type] = None
        self.double_var = tk.DoubleVar(self, min_value)
        self.string_var = tk.StringVar(self)
        # self.trace = self.double_var.trace_add(mode="write", callback=self.on_slider_move)
        self.slider = TickScale(self, from_=min_value/resolution, to=max_value/resolution, variable=self.double_var, length=200, showvalue=False, resolution=1.0, takefocus=True, command=self.on_slider_move)
        self.slider.grid(row=1, column=1)
        # self.slider.bind("<Button-1>", self.on_slider_click)
        vcmd = (self.register(self.entry_validate),'%P')
        self.entry = ttk.Spinbox(self, textvariable=self.string_var, validate="key", validatecommand=vcmd, width=5, from_=min_value, to=max_value, increment=resolution, command=self.on_spinbox_entry, name="hello")
        self.trace = self.string_var.trace_add("write", lambda *args: self.on_spinbox_entry())
        self.entry.grid(row=1, column=2)
        self.entry.bind("<Return>", self.entry_defocus)
        # self.winfo_toplevel().bind("<Button -1>", self.click_event)
# 

    def on_slider_move(self, a):
        self.string_var.set(f"{self.double_var.get()*self.resolution:.2f}")
        self.value = self.var_type(self.double_var.get()*self.resolution)
        logging.debug(f"Slider moved to {self.value}")

    def on_spinbox_entry(self):
        # logging.debug(self.double_var.trace_info())
        self.string_var.trace_remove("write", self.trace)
        # logging.debug(f"set trace to {self.var_type(self.string_var.get())}")
        try:
            # self.slider.set(self.var_type(float(self.string_var.get())/self.resolution))
            self.double_var.set(self.var_type(float(self.string_var.get())/self.resolution))
        except Exception:
            logging.debug(f"invalid number {self.string_var.get()}")
        self.trace = self.string_var.trace_add(mode="write", callback=lambda *args: self.on_spinbox_entry())
        self.value = self.var_type(self.double_var.get()*self.resolution)
        logging.debug(f"Spinbox moved to {self.value}")


    def entry_validate(self, string):
        logging.debug(f"entry {string}")
        regex = re.compile(r"(\+|\-)?[0-9.]*$")
        result = regex.match(string)
        # try:
        #     self.on_spinbox_entry()
        # except Exception:
        #     pass
        return (string == ""
                or (string.count('+') <= 1
                    and string.count('-') <= 1
                    and string.count('.') <= 1
                    and result is not None
                    and result.group(0) != ""))
        
    def entry_defocus(self, event: tk.Event):
        self.entry.tk_focusNext().focus()

    def click_event(self, event: tk.Event):
        # print(self.entry.)
        x,y = root.winfo_pointerxy()                   # get the mouse position on screen
        widget = root.winfo_containing(x,y)            # identify the widget at this location
        print(widget)
        widget = root.nametowidget(widget)
        if not (widget == self.entry):                 # if the mouse is not over the text widget
            root.focus()                               # focus on root

    # def on_entry(self, a, b, c):
    #     ...

class AnalogSettingsPanel(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Analog Key Settings")

        # self.scancode: Optional[ScanCode] = None
        
        # self.label_rapid_trigger = ttk.Label(self, text="Rapid Trigger")
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.columnconfigure(1, weight=1)
        # self.columnconfigure(2, weight=1)

        self.checkbox_rapid_trigger = ttk.Checkbutton(self, text="Rapid Trigger")
        self.checkbox_rapid_trigger.state(['!alternate'])  # Start unchecked
        self.checkbox_rapid_trigger.grid(row=1, column=1)
        self.press_hysteresis = SliderSetting(self, text="Press Sensitivity", var_type=float, min_value=0, max_value=2, resolution=0.01)
        self.press_hysteresis.grid(row=2, column=1, sticky="EW")
        self.release_hysteresis = SliderSetting(self, text="Release Sensitivity")
        self.release_hysteresis.grid(row=3, column=1, sticky="EW")
        self.upper_range = SliderSetting(self, text="Rapid Trigger Range Upper Limit")
        self.upper_range.grid(row=4, column=1, sticky="EW")
        self.lower_range = SliderSetting(self, text="Rapid Trigger Range Low Limit")
        self.lower_range.grid(row=5, column=1, sticky="EW")

        # self.label_sensitivity = ttk.Label(self, text="Sensitivity")
        # self.label_sensitivity.grid(row=2, column=1)
        # self.slider_sensitivity = TickScale(self, resolution=0.1, digits=2, to=2)
        # # self.slider_sensitivity = ttk.Scale(self)
        # self.slider_sensitivity.grid(row=3, column=1)
        # self.entry_sensitivity = ttk.Entry(self)
        # self.entry_sensitivity.grid(row=1, column=1)

    def load_from_digital_settings_message(self, message: fluxpad_interface.AnalogSettingsMessage):
        self.label_sensitivity = ttk.Label()


class DigitalSettingsPanel(ttk.Labelframe):

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Analog Key Settings")

        # self.scancode: Optional[ScanCode] = None
        
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.debounce_setting = SliderSetting(self, text="Debouce", var_type=float, min_value=0, max_value=2, resolution=0.01)
        self.debounce_setting.grid(row=1, column=1, sticky="EW")

    def set_scancode(self, scancode: ScanCode):
        self.scancode = scancode

    def load_from_digital_settings_message(self, message: fluxpad_interface.AnalogSettingsMessage):
        ...


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class SelectKeySettingsFrame(ttk.Labelframe):
    
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Select Key")
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)

        self.chk_per_key_digital = ttk.Checkbutton(self, text="Per Key Digital Settings")
        self.chk_per_key_digital.state(['!alternate'])  # Start unchecked
        self.chk_per_key_digital.grid(row=1, column=1, columnspan=2, sticky="W")

        self.btn_digital_1 = ttk.Button(self, text="Digital Key 1")
        self.btn_digital_1.grid(row=2, column=1, sticky="EW")
        self.btn_digital_2 = ttk.Button(self, text="Digital Key 2")
        self.btn_digital_2.grid(row=2, column=2, sticky="EW")

        self.chk_per_key_analog = ttk.Checkbutton(self, text="Per Key Analog Settings")
        self.chk_per_key_analog.state(['!alternate'])  # Start unchecked
        self.chk_per_key_analog.grid(row=3, column=1, columnspan=2, sticky="W")

        self.btn_analog_1 = ttk.Button(self, text="Analog Key 1")
        self.btn_analog_1.grid(row=4, column=1, sticky="EW")
        self.btn_analog_2 = ttk.Button(self, text="Analog Key 2")
        self.btn_analog_2.grid(row=4, column=2, sticky="EW")




class SettingsFrame(ttk.Frame):
    """Represents the settings tab"""

    def __init__(self, master, fluxpad_settings: fluxpad_interface.FluxpadSettings, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.fluxpad_settings = fluxpad_settings

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)

        self.columnconfigure(1, weight=1)

        self.key_select_frame = SelectKeySettingsFrame(self)
        self.key_select_frame.grid(row=1, column=1, sticky="NSEW")
        self.key_select_frame.btn_digital_1.bind("<Button-1>", lambda event: self.on_select_key(event, 0))
        self.key_select_frame.btn_digital_2.bind("<Button-1>", lambda event: self.on_select_key(event, 1))
        self.key_select_frame.btn_analog_1.bind("<Button-1>", lambda event: self.on_select_key(event, 2))
        self.key_select_frame.btn_analog_2.bind("<Button-1>", lambda event: self.on_select_key(event, 3))


        # self.scrollable_frame = ScrollableFrame(self)
        # self.scrollable_frame.grid(row=2, column=1, sticky="NSEW")
        self.analog_settings_panel = AnalogSettingsPanel(self)
        self.analog_settings_panel.grid(row=2, column=1, sticky="NSEW")
        self.digital_settings_panel = DigitalSettingsPanel(self)
        self.digital_settings_panel.grid(row=2, column=1, sticky="NSEW")
        
        self.on_select_key(None, 0)

    
    def on_select_key(self, event: tk.Event, key_id: int):
        if isinstance(self.fluxpad_settings.key_settings_list[key_id], fluxpad_interface.AnalogSettingsMessage):
            # self.digital_settings_panel.grid()
            logging.debug("Selected analog key")
            self.digital_settings_panel.grid_forget()
            # self.analog_settings_panel.grid_configure()
            self.analog_settings_panel.grid(row=2, column=1, sticky="NSEW")


        if isinstance(self.fluxpad_settings.key_settings_list[key_id], fluxpad_interface.DigitalSettingsMessage):
            logging.debug("Selected digital key")
            self.analog_settings_panel.grid_forget()
            self.digital_settings_panel.grid(row=2, column=1, sticky="NSEW")
            # self.digital_settings_panel.grid_configure()

        
        # self.Settings

        # test_label = tk.Label(self, text="Coming Soon")
        # test_label.pack()


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

        self.notebook = ttk.Notebook(self, takefocus=False)
        # self.config(padding=0)
        self.fluxpad_settings = fluxpad_interface.FluxpadSettings()

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
 
        self.frame_keymap = KeymapFrame(self.notebook)
        self.frame_settings = SettingsFrame(self.notebook, self.fluxpad_settings)
        self.frame_utilities = UtilitiesFrame(self.notebook)

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

    
    def on_notebook_tab_changed(self, event: tk.Event):
        """"Turn on and off keyboard listensr based on which tab is active"""

        if self.notebook.index("current") == 0:  # Check if tab on top is keymap tab
            self.frame_keymap.lf_mapedit.is_active = True
        else: 
            self.frame_keymap.lf_mapedit.is_active = False

    def _update_from_settings(self):
        self.frame_keymap.lf_key1.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[0].key_type, self.fluxpad_settings.key_settings_list[0].key_code))
        self.frame_keymap.lf_key2.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[1].key_type, self.fluxpad_settings.key_settings_list[1].key_code))
        self.frame_keymap.lf_key3.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[2].key_type, self.fluxpad_settings.key_settings_list[2].key_code))
        self.frame_keymap.lf_key4.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[3].key_type, self.fluxpad_settings.key_settings_list[3].key_code))
        self.frame_keymap.lf_enc_ccw.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[4].key_type, self.fluxpad_settings.key_settings_list[4].key_code))
        self.frame_keymap.lf_enc_cw.set_scancode(key_type_and_code_to_scancode(self.fluxpad_settings.key_settings_list[5].key_type, self.fluxpad_settings.key_settings_list[5].key_code))

    def on_load_from_file(self):
        # TODO implement this
        self.fluxpad_settings.load_from_file(pathlib.Path(__file__).parent / "testy.json")
        self._update_from_settings()
        # pass

    def on_save_to_file(self):
        # TODO implement this
        pass
    
    def on_load_from_fluxpad(self):
        # TODO implement this
        self._update_from_settings()
    
    def on_save_to_fluxpad(self):
        # TODO implement this
        pass

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
        # use_sv_ttk.set_theme("dark")
    else:
        ...
        use_sv_ttk.set_theme("light")
        
    # root.geometry("600x600")
    root.title("FLUXAPP")
    app = Application(master=root)
    app.pack(expand=True, fill="both", side="top")
    app.mainloop()
