import tkinter as tk
from tkinter import ttk
from typing import Union, Optional

import pynput

from scancode_to_hid_code import (KeyList, ScanCode, get_name_list,
                                  pynput_event_to_HIDKeycode)


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
        self.label_cw_key.configure(text=self.cw_scancode.Key_Name)

    def set_ccw_keycode(self, scancode: ScanCode):
        assert isinstance(scancode, ScanCode)
        self.ccw_scancode = scancode
        self.label_ccw_key.configure(text=self.ccw_scancode.Key_Name)


class KeyMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.scancode: Optional[ScanCode] = None

        self.label_key = ttk.Label(self, text="None")
        self.label_key.pack()
        self.btn_edit = ttk.Button(self, text="Edit")
        self.btn_edit.pack()

    def set_keycode(self, scancode: ScanCode):
        self.scancode = scancode
        self.label_key.configure(text=self.scancode.Key_Name)


class MapEditFrame(ttk.Labelframe):
    """Represents a keymap edit section"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Edit")

        self.label_a = ttk.Label(self, text="Press key to set...")
        self.label_a.grid(row=1, column=1)

        self.label_key = ttk.Combobox(self, text="None", state="readonly")
        self.label_key.grid(row=1, column=2)
        self.label_key['values'] = get_name_list()

        listener = pynput.keyboard.Listener(
            on_press=self.on_press)
        listener.start()

    def on_press(self, key: Union[pynput.keyboard.Key, pynput.keyboard.KeyCode]):
        self.label_key.set(pynput_event_to_HIDKeycode(key).Key_Name)

class KeymapFrame(ttk.Frame):
    """Represents a the keymap tab
    Contains the encoder map, key maps"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Create encoder map
        self.lf_encoder = EncoderMap(self)
        self.lf_encoder.grid(row=1, column=1, columnspan=2)
        self.lf_encoder.set_cw_keycode(KeyList.CONSUMER_0x00E9.value)
        self.lf_encoder.set_ccw_keycode(KeyList.CONSUMER_0x00EA.value)

        # Create key map
        self.lf_key1 = KeyMap(self, text="Digital Key 1")
        self.lf_key1.grid(row=2, column=1)
        self.lf_key1.set_keycode(KeyList.KEY_A.value)

        self.lf_key2 = KeyMap(self, text="Digital Key 2")
        self.lf_key2.grid(row=2, column=2)
        self.lf_key2.set_keycode(KeyList.KEY_S.value)

        self.lf_key3 = KeyMap(self, text="Analog Key 1")
        self.lf_key3.grid(row=3, column=1)
        self.lf_key3.set_keycode(KeyList.KEY_Z.value)

        self.lf_key4 = KeyMap(self, text="Analog Key 2")
        self.lf_key4.grid(row=3, column=2)
        self.lf_key4.set_keycode(KeyList.KEY_X.value)

        # Create Map Edit Frame
        self.lf_mapedit = MapEditFrame(self)
        self.lf_mapedit.grid(row=4, column=1, columnspan=2)


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
        # self.configure(background="green")

        self.btn_upload = ttk.Button(self, text="Upload")
        self.btn_upload.grid(row=1, column=1)

        self.notebook = ttk.Notebook(self)

        self.frame_keymap = KeymapFrame(self.notebook)
        self.frame_settings = SettingsFrame(self.notebook)

        self.notebook.add(self.frame_keymap, text="Keymap")
        self.notebook.add(self.frame_settings, text="Settings")
        self.notebook.grid(row=2, column=1)


if __name__ == "__main__":

    # keyboard.hook(callback=keyboard_callback)

    root = tk.Tk()
    # root.geometry("200x600")
    root.title("FLUXPAD Config")
    app = Application(master=root)
    app.pack()
    app.mainloop()
