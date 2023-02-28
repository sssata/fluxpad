import tkinter as tk
from tkinter import ttk
from common_enums import KeyType, KeyboardKeycodes, ConsumerKeycodes



class EncoderMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.configure(text="Encoder")

        self.cw_keycode = tk.IntVar()
        self.cw_keycode.trace_add("write", self.update_cw_label)
        self.cw_keytype = tk.IntVar()

        self.ccw_keycode = tk.IntVar()
        self.ccw_keycode.trace_add("write", self.update_ccw_label)
        self.ccw_keytype = tk.IntVar()
        
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
        self.cw_keycode.set(1)
        self.ccw_keycode.set(2)

    
    def update_cw_label(self, var: str, index: str, mode: str):
        self.label_cw_key.configure(text=ConsumerKeycodes(self.cw_keycode.get()).name)
    
    def update_ccw_label(self, var: str, index: str, mode: str):
        self.label_ccw_key.configure(text=ConsumerKeycodes(self.ccw_keycode.get()).name)


class KeyMap(ttk.Labelframe):
    """Class for an encoder keymap gui
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.keycode = tk.IntVar()
        self.keycode.trace_add("write", self.update_label)
        self.keytype = tk.IntVar()

        self.label_key = ttk.Label(self, text="None")
        self.label_key.grid(row=1, column=1)
        self.btn_edit = ttk.Button(self, text="Edit")
        self.btn_edit.grid(row=2, column=1)

        self.keycode.set(97)

    def update_label(self, var: str, index: str, mode: str):
        self.label_key.configure(text=chr(self.keycode.get()))
        

class KeymapFrame(ttk.Frame):
    """Represents a the keymap tab
    Contains the encoder map, key maps"""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Create encoder map
        self.labelframe_encoder = EncoderMap(self)
        self.labelframe_encoder.grid(row=1, column=1, columnspan=2)

        # Create key map
        self.lf_key1 = KeyMap(self, text="Digital Key 1")
        self.lf_key1.grid(row=2, column=1)
        
        self.lf_key2 = KeyMap(self, text="Digital Key 2")
        self.lf_key2.grid(row=2, column=2)

        self.lf_key3 = KeyMap(self, text="Analog Key 1")
        self.lf_key3.grid(row=3, column=1)
        
        self.lf_key4 = KeyMap(self, text="Analog Key 2")
        self.lf_key4.grid(row=3, column=2)

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

        self.btn_upload = tk.Button(self, text="Upload")
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


root = tk.Tk()
# root.geometry("200x600")
root.title("FLUXPAD Config")
app = Application(master=root)
app.pack()
root.bind("<KeyPress>", func=app.key_test)
app.mainloop()
