import tkinter as tk
from tkinter import ttk
from typing import Union, Optional, Callable, NewType, TypeVar
import logging

import pynput

from scancode_to_hid_code import (ScanCodeList, ScanCode, get_name_list,
                                  pynput_event_to_scancode)

UpdateScancodeCallback = Callable[[ScanCode], None]

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

        self.btn_key = ttk.Button(self, text="None")
        self.btn_key.pack(expand=True, fill="both")

    def set_scancode(self, scancode: ScanCode):
        self.scancode = scancode
        self.btn_key.configure(text=self.scancode.name)

    @property
    def key_name(self):
        return self["text"]

    # def set_on_click_callback(self, callback: Callable[[tk.Event], int]):
    #     self.btn_key.bind("<Button-1>", callback)


class MapEditFrame(ttk.Labelframe):
    """Represents a keymap edit section"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Edit")
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.label_a = ttk.Label(self, text="Press key to set...")
        self.label_a.grid(row=1, column=1)

        self.label_key = ttk.Combobox(self, text="None", state="readonly")
        self.label_key.grid(row=1, column=2)
        self.label_key['values'] = get_name_list()

        self.on_update_scancode_callback: Optional[UpdateScancodeCallback] = None

        listener = pynput.keyboard.Listener(
            on_press=self.on_press)
        listener.start()

    def on_press(self, key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode]):

        # Only react to keyboard if pointer on applications
        logging.debug(self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery()))
        if self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery()) is not None:
            new_scancode = pynput_event_to_scancode(key)
            logging.debug(f"Pressed {new_scancode.name}")
            self.label_key.set(new_scancode.name)

            if self.on_update_scancode_callback is not None:
                self.on_update_scancode_callback(new_scancode)
    

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
        PADDING = 2
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

        self.selected_keymap: Optional[KeyMap] = None

    def on_press_keymap(self, keymap: KeyMap, event: tk.Event):
        logging.debug(f"Selected key: {keymap.key_name}")
        self.selected_keymap = keymap
        # logging.debug(type(self.currently_selected_keymap))
        
    def on_scancode_update(self, scancode: ScanCode):
        """Function that routes a selected scancode from the mapedit frame to the selected keymap frame"""
        if self.selected_keymap is not None:
            logging.debug(f"Set key {self.selected_keymap.key_name} to scancode: {scancode.name}")
            self.selected_keymap.set_scancode(scancode)

class SettingsFrame(ttk.Frame):
    """Represents the settings tab"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        test_label = tk.Label(self, text="hello")
        test_label.pack()


class Application(ttk.Frame):
    """Top Level application frame"""

    def __init__(self, master=None):
        super().__init__(master=master)
        # self.config()


        self.notebook = ttk.Notebook(self)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.frame_keymap = KeymapFrame(self.notebook)
        self.frame_settings = SettingsFrame(self.notebook)

        self.notebook.add(self.frame_keymap, text="Keymap")
        self.notebook.add(self.frame_settings, text="Settings")
        self.notebook.grid(row=1, column=1, sticky="NSEW")


        self.btn_upload = ttk.Button(self, text="Upload")
        self.btn_upload.grid(row=2, column=1, sticky="NSEW")

        # Create menubar
        self.menubar = tk.Menu(self.master)

        # Load menu
        self.load_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Load", menu=self.load_menu)
        self.load_menu.add_command(label="Load from File")
        self.load_menu.add_command(label="Load from FLUXPAD")

        # Save menu
        self.save_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Save", menu=self.save_menu)
        self.save_menu.add_command(label="Save to File")
        self.save_menu.add_command(label="Save to FLUXPAD")

        # Show menu bar
        self.master.configure(menu=self.menubar)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # keyboard.hook(callback=keyboard_callback)

    root = tk.Tk()
    # root.attributes("-alpha", 0.5)
    # root.geometry("600x600")
    root.title("FLUXAPP")
    app = Application(master=root)
    # app.grid(column=1, row=1, sticky="EW")
    # app.update
    app.pack(expand=True, fill="both", side="top")
    app.mainloop()
