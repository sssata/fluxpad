import tkinter as tk
from tkinter import ttk
from typing import Optional
import re

from tickscale import TickScale
import logging

PADDING = 2


class SliderSetting(ttk.Labelframe):

    def __init__(self, master, var_type: type = float, min_value = 0, max_value = 1, resolution = 0.1, decimal_places = 2, units: str = "", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.resolution = resolution
        self.var_type = var_type
        self.min_value = min_value
        self.max_value = max_value
        self.decimal_places = decimal_places

        # Grid config
        self.rowconfigure(1, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)
        self.columnconfigure(3, weight=0)

        self.value: Optional[var_type] = None
        self.double_var = tk.DoubleVar(self, min_value)
        self.string_var = tk.StringVar(self)
        self.slider = TickScale(self, from_=min_value/resolution, to=max_value/resolution, variable=self.double_var, length=200, showvalue=False, resolution=1.0, takefocus=True, command=self.on_slider_move)
        self.slider.grid(row=1, column=1, sticky="E", padx=PADDING)
        self.entry = ttk.Spinbox(self, textvariable=self.string_var, validate="key", validatecommand=(self.register(self.entry_validate),'%P'), width=5, from_=min_value, to=max_value, increment=resolution, name="hello")
        self.entry.grid(row=1, column=2, padx=4)

        self.units_label = ttk.Label(self, text=units)
        self.units_label.grid(row=1, column=3, padx=(2,0))

        # Wire things up
        self.trace = self.string_var.trace_add("write", lambda *args: self.on_spinbox_entry())  # Trace spinbox entry
        self.slider.scale.bind("<1>", lambda event: self.on_slider_click())  # Focus on scale click
        self.slider.scale.bind("<2>", lambda event: self.on_slider_click())  # Focus on scale click
        self.slider.scale.bind("<3>", lambda event: self.on_slider_click())  # Focus on scale click

        self.entry.bind("<Return>", self.entry_defocus)  # Defocus on enter key
        self.entry.bind("<FocusOut>", self.check_in_range)  # Enforce range on defocus
        # self.winfo_toplevel().bind("<Button -1>", self.click_event)
        self.on_slider_move(None)

    def on_slider_click(self):
        self.slider.scale.focus()


    def on_slider_move(self, a):
        self.string_var.set(f"{self.double_var.get()*self.resolution:.{self.decimal_places}f}")
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

    def check_in_range(self, event: tk.Event):
        if self.value < self.min_value:
            logging.debug("below range")
            self.double_var.set(self.min_value/self.resolution)
            self.on_slider_move(1)

        elif self.value > self.max_value:
            logging.debug("above range")
            self.double_var.set(self.max_value/self.resolution)
            self.on_slider_move(1)

        logging.debug("in range")

    def entry_validate(self, string: str):
        logging.debug(f"Entry {string}")
        regex = re.compile(r"(\+|\-)?[0-9.]*$")
        result = regex.match(string)
        return (string == ""
                or (string.count('+') <= 1
                    and string.count('-') <= 1
                    and string.count('.') <= 1
                    and result is not None
                    and result.group(0) != ""))
        
    def entry_defocus(self, event: tk.Event):
        self.entry.tk_focusNext().focus()

    def set_value(self, value):
        print(f"hello {value}")
        self.double_var.set(value/self.resolution)
        print(f"hello {self.double_var.get()}")
        self.on_slider_move(None)