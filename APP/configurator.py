import tkinter as tk
from tkinter import ttk
from common_enums import KeyType, KeyboardKeycodes, ConsumerKeycodes, keycode_to_string, get_all_key_list
# import pygame
# import keyboard
import pynput

class EncoderMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Encoder")

        self.cw_keycode = tk.IntVar()
        self.cw_keycode.trace_add("write", self.update_cw_label_callback)
        self.cw_keytype = tk.IntVar()
        self.cw_keytype.trace_add("write", self.update_cw_label_callback)

        self.ccw_keycode = tk.IntVar()
        self.ccw_keycode.trace_add("write", self.update_ccw_label_callback)
        self.ccw_keytype = tk.IntVar()
        self.ccw_keytype.trace_add("write", self.update_cw_label_callback)
        
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

        # init keycodes to invoke trace callback
        # self.cw_keycode.set(0)
        # self.cw_keytype.set(0)
        # self.ccw_keycode.set(0)
        # self.ccw_keytype.set(0)

    
    def update_cw_label_callback(self, var: str, index: str, mode: str):
        self.label_cw_key.configure(text=keycode_to_string(self.cw_keytype.get(), self.cw_keycode.get()))
    
    def update_ccw_label_callback(self, var: str, index: str, mode: str):
        self.label_ccw_key.configure(text=keycode_to_string(self.ccw_keytype.get(), self.ccw_keycode.get()))

class KeyMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.keycode = tk.IntVar()
        self.keycode.trace_add("write", self.update_label_callback)
        self.keytype = tk.IntVar()
        self.keytype.trace_add("write", self.update_label_callback)

        self.label_key = ttk.Label(self, text="None")
        self.label_key.pack()
        self.btn_edit = ttk.Button(self, text="Edit")
        self.btn_edit.pack()

        # self.keycode.set(0)

    def update_label_callback(self, var: str, index: str, mode: str):
        self.label_key.configure(text=keycode_to_string(self.keytype.get(), self.keycode.get()))


class MapEditFrame(ttk.Labelframe):
    """Represents a keymap edit section"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Edit")

        self.label_a = ttk.Label(self, text="Press key to set...")
        self.label_a.grid(row=1, column=1)

        self.label_key = ttk.Combobox(self, text="None")
        self.label_key.grid(row=1, column=2)
        self.label_key['values'] = get_all_key_list()


class KeymapFrame(ttk.Frame):
    """Represents a the keymap tab
    Contains the encoder map, key maps"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Create encoder map
        self.lf_encoder = EncoderMap(self)
        self.lf_encoder.grid(row=1, column=1, columnspan=2)
        self.lf_encoder.ccw_keytype.set(KeyType.CONSUMER.value)
        self.lf_encoder.cw_keycode.set(ConsumerKeycodes.VOL_UP.value)
        self.lf_encoder.cw_keytype.set(KeyType.CONSUMER.value)
        self.lf_encoder.ccw_keycode.set(ConsumerKeycodes.VOL_DOWN.value)

        # Create key map
        self.lf_key1 = KeyMap(self, text="Digital Key 1")
        self.lf_key1.grid(row=2, column=1)
        self.lf_key1.keytype.set(KeyType.KEYBOARD.value)
        self.lf_key1.keycode.set(KeyboardKeycodes.A.value)
        
        self.lf_key2 = KeyMap(self, text="Digital Key 2")
        self.lf_key2.grid(row=2, column=2)
        self.lf_key2.keytype.set(KeyType.KEYBOARD.value)
        self.lf_key2.keycode.set(KeyboardKeycodes.S.value)

        self.lf_key3 = KeyMap(self, text="Analog Key 1")
        self.lf_key3.grid(row=3, column=1)
        self.lf_key3.keytype.set(KeyType.KEYBOARD.value)
        self.lf_key3.keycode.set(KeyboardKeycodes.Z.value)
        
        self.lf_key4 = KeyMap(self, text="Analog Key 2")
        self.lf_key4.grid(row=3, column=2)
        self.lf_key4.keytype.set(KeyType.KEYBOARD.value)
        self.lf_key4.keycode.set(KeyboardKeycodes.X.value)

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

    def key_test(self, event: tk.Event):
        print(event)
        print(type(event))
        print(event.char)
        print(event.keycode)
        print(event.keysym)


# def keyboard_callback(event: keyboard.KeyboardEvent):
#     print(event, event.scan_code, event.scan_code)


if __name__ == "__main__":

    # keyboard.hook(callback=keyboard_callback)

    root = tk.Tk()
    # root.geometry("200x600")
    root.title("FLUXPAD Config")
    app = Application(master=root)
    app.pack()
    # root.bind("<Key>", func=app.key_test)
    app.mainloop()
