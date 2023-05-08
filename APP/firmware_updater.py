import serial
import time
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional
import logging
import traceback
import pathlib

from fluxpad_interface import Fluxpad

BOSSAC_PATH = (pathlib.Path(__file__).parent / "tools" / "bossac.exe").resolve()

class FirmwareUpdateFrame(ttk.Labelframe):
    
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Firmware Update elements
        self.update_frame = ttk.Labelframe(self, text="Firmware Update")
        self.update_frame.grid(row=1, column=0, padx=5, pady=5, sticky="W")
        self.btn_update = ttk.Button(
            self.update_frame, text="Update", command=self.upload_firmware_callback
        )
        self.btn_update["state"] = "disabled"
        self.btn_update.grid(row=1, column=0, padx=5, pady=5, sticky="W")
        self.fetch_releases_button = ttk.Button(
            self.update_frame,
            text="Fetch Releases",
            # command=self.fetch_firmware_callback,
        )
        self.fetch_releases_button.grid(row=0, column=1)
        self.firmware_combobox = ttk.Combobox(
            self.update_frame,
            # textvariable=self.selected_firmware_release,
            width=10
        )
        self.firmware_combobox.grid(row=0, column=0)

        self.fluxpad: Optional[Fluxpad] = None
    
    def set_fluxpad(self, fluxpad: Fluxpad):
        self.fluxpad = fluxpad

    def disable_update(self):
        self.btn_update.state(["disabled"])

    def enable_update(self):
        self.btn_update.state(["!disabled"])


    def upload_firmware_callback(self):
        
        try:
            assert self.fluxpad is not None
            bin_path = pathlib.Path(pathlib.Path(__file__).parent / "binaries" / "flux_arduino.ino.bin").resolve()
            upload_firmware(self.fluxpad.port, str(bin_path))
        except Exception:
            logging.error(f"Failed to upload firmware", exc_info=True)
            messagebox.showerror("Exception", f"Failed to load image\n\n{traceback.format_exc()}")

def upload_firmware(port: serial.Serial, bin_path: str):
     
    _reset_port(port)
    _bossac_upload(port.name, str(BOSSAC_PATH), bin_path)


def _reset_port(port: serial.Serial):
        """Resets given port by opening and closing port twice within 500ms at 1200 baud"""
        port.close()
        time.sleep(2)
        assert not port.is_open
        port.baudrate = 1200
        port.open()
        time.sleep(0.05)
        port.close()
        time.sleep(0.05)
        port.open()
        time.sleep(0.05)
        port.close()
        # Wait for reset and enumeration
        time.sleep(2)

def _bossac_upload(port: str, bossac_path: str, bin_path: str):
    """Run Bossac to upload given bin file to given serial port"""

    args = (
        f"{bossac_path}",
        # f"--info",
        "-p",  # Select port
        f"{port}",
        "-U",
        "true",
        "-i",  # INFO
        "-e",  # Erase
        "-w",  # Write
        "-v",  # Verify
        f"{bin_path}",
        "-R",
    )
    print(args)

    popen = subprocess.run(
        args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    output = popen.stdout.decode("ASCII")
    err = popen.stderr.decode("ASCII")
    logging.info(output)
    logging.info(err)