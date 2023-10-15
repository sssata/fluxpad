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
import threading
import os
import shutil
import traceback

from fluxpad_interface import Fluxpad

# BOSSAC_PATH = (pathlib.Path(__file__).parent / "tools" / "bossac.exe").resolve()

BUFFER_SIZE = 128 * 1024

class SameFileError(OSError):
    """Raised when source and destination are the same file."""


def copy_with_callback(
    src, dest, callback=None, buffer_size=BUFFER_SIZE
):
    """ Copy file with a callback. 
        callback, if provided, must be a callable and will be 
        called after ever buffer_size bytes are copied.
    Args:
        src: source file, must exist
        dest: destination path; if an existing directory, 
            file will be copied to the directory; 
            if it is not a directory, assumed to be destination filename
        callback: callable to call after every buffer_size bytes are copied
            callback will called as callback(bytes_copied since last callback, total bytes copied, total bytes in source file)
        buffer_size: how many bytes to copy before each call to the callback, default = 4Mb
    Returns:
        Full path to destination file
    Raises:
        FileNotFoundError if src doesn't exist
        SameFileError if src and dest are the same file
    Note: Does not copy extended attributes, resource forks or other metadata.
    """

    srcfile = pathlib.Path(src)
    destpath = pathlib.Path(dest)

    if not srcfile.is_file():
        raise FileNotFoundError(f"src file `{src}` doesn't exist")

    destfile = destpath / srcfile.name if destpath.is_dir() else destpath

    if destfile.exists() and srcfile.samefile(destfile):
        raise SameFileError(
            f"source file `{src}` and destinaton file `{dest}` are the same file."
        )

    if callback is not None and not callable(callback):
        raise ValueError("callback is not callable")

    size = os.stat(src).st_size
    with open(srcfile, "rb") as fsrc:
        with open(destfile, "wb") as fdest:
            _copyfileobj(
                fsrc, fdest, callback=callback, total=size, length=buffer_size
            )
    return str(destfile)


def _copyfileobj(fsrc, fdest, callback, total, length):
    """ copy from fsrc to fdest
    Args:
        fsrc: filehandle to source file
        fdest: filehandle to destination file
        callback: callable callback that will be called after every length bytes copied
        total: total bytes in source file (will be passed to callback)
        length: how many bytes to copy at once (between calls to callback)
    """
    copied = 0
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdest.write(buf)
        copied += len(buf)
        if callback is not None:
            callback(len(buf), copied, total)

class FirmwareUploadProgress:
    # Object to hold upload progress info

    def __init__(self):
        self.lock = threading.RLock()
        self.progress_percent = 0.0
        self.current_step = "None"
        self.is_done = False
        self.error_string = ""
        self.update_event = threading.Event()


def upload_firmware_threaded(port: serial.Serial, bin_path: pathlib.Path):
    progress = FirmwareUploadProgress()
    fw_upload_thread = threading.Thread(target=_upload_firmware, args=(progress, port, bin_path), name="fwupdatethread", daemon=True)
    fw_upload_thread.start()
    return progress

def _upload_firmware(progress: FirmwareUploadProgress, port: serial.Serial, bin_path: pathlib.Path):

    def copy_progress_callback(buf_size, copied, total):
        with progress.lock:
            progress.progress_percent = 30 + 70 * copied / total
            progress.update_event.set()
            print(progress.progress_percent)

    try:
        with progress.lock:
            progress.current_step = "Resetting to bootloader"
            progress.progress_percent = 10
            progress.update_event.set()
        _reset_port(port)

        with progress.lock:
            progress.current_step = "Waiting for enumeration"
            progress.progress_percent = 20
            progress.update_event.set()
        rpi_drive = _listen_for_rpi_drive()

        with progress.lock:
            progress.current_step = "Uploading firmware"
            progress.progress_percent = 30
            progress.update_event.set()

        dest_file = rpi_drive / bin_path.name
        copy_with_callback(bin_path, dest_file, copy_progress_callback)

        with progress.lock:
            progress.current_step = "Done"
            progress.is_done = True
            progress.progress_percent = 100
            progress.update_event.set()

    except Exception:
        with progress.lock:
            progress.error_string = traceback.format_exc()
            progress.is_done = True
            progress.update_event.set()


def _listen_for_rpi_drive(timeout_s: float = 5, period_s: float = 0.3):

    start_time_s = time.monotonic()
    while start_time_s - time.monotonic() < timeout_s :
        for drive in _list_available_drives():
            print(drive)
            if _has_info_uf2_file(drive):
                return drive

        time.sleep(period_s)


def _list_available_drives():
    """
    Detects and returns a list of available drives on the system.
    This function finds available drives on Unix/Linux/MacOS in common mount points like '/media' and '/mnt',
    and on Windows, by iterating through drive letters from 'A' to 'Z'.
    Returns:
        list of pathlib.Path objects: A list of pathlib.Path objects representing available drives.
    """
    drives = []
    if os.name == 'posix':  # Unix/Linux/MacOS
        # On Unix-based systems, drives are typically mounted in /media or /mnt
        mounts = ['/media', '/mnt']
        for mount in mounts:
            mount_path = pathlib.Path(mount)
            if mount_path.is_dir():
                drives.extend([entry for entry in mount_path.iterdir() if entry.is_dir() and not entry.name.startswith('.')])
    elif os.name == 'nt':  # Windows
        # On Windows, you can list drives by iterating from 'A' to 'Z'
        drives = [pathlib.Path(f'{chr(d)}:') for d in range(65, 91) if pathlib.Path(f'{chr(d)}:').is_dir()]
    return drives


def _has_info_uf2_file(directory_path: pathlib.Path):
    """
    Checks if the given pathlib directory contains a file named 'INFO_UF2.TXT'.
    Parameters:
        directory_path (pathlib.Path): The path to the directory to be checked.
    Returns:
        bool: True if 'INFO_UF2.TXT' file exists in the directory, False otherwise.
    """
    info_uf2_file_path = directory_path / 'INFO_UF2.TXT'
    return info_uf2_file_path.is_file()

def _reset_port(port: serial.Serial):
        """Resets given port by opening and closing port at 1200 baud"""
        port.close()
        time.sleep(0.1)
        # assert not port.is_open
        port.baudrate = 1200
        port.open()
        time.sleep(0.5)
        port.close()
        time.sleep(0.2)


class FirmwareUpdateFrame(ttk.Labelframe):
    
    def __init__(self, master, firmware_dir: pathlib.Path, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Firmware Update elements
        # self.update_frame = ttk.Labelframe(self, text="Firmware Update")
        self.configure(text="Firmware Update")
        # self.update_frame.grid(row=1, column=0, padx=5, pady=5, sticky="W")

        self.label_progress = ttk.Label(self, text="FW Update Progress")
        self.label_progress.grid(row=1, column=0, padx=5, pady=5, sticky="W")

        self.progressbar_update = ttk.Progressbar(self, mode="determinate", orient="horizontal", length=200, maximum=100)
        self.progressbar_update.grid(row=2, column=0, padx=5, pady=5, sticky="W")

        self.btn_update = ttk.Button(
            self, text="Update", command=self.upload_firmware_callback
        )
        self.btn_update["state"] = "disabled"
        self.btn_update.grid(row=3, column=0, padx=5, pady=5, sticky="W")

        self.fluxpad: Optional[Fluxpad] = None
        self.stop_listener_callback = None
        
        self.fw_bin_path = (firmware_dir / "firmware.uf2").resolve()
    
    def set_fluxpad(self, fluxpad: Optional[Fluxpad]):
        self.fluxpad = fluxpad

    def disable_update(self):
        self.btn_update.state(["disabled"])

    def enable_update(self):
        self.btn_update.state(["!disabled"])

    def set_stop_listener_callback(self, callback):
        self.stop_listener_callback = callback

    def upload_firmware_callback(self):
        try:
            self.stop_listener_callback()
            assert self.fluxpad is not None
            progress = upload_firmware_threaded(self.fluxpad.port, self.fw_bin_path)
            while progress.update_event.wait(timeout=10):
                print("waited")
                with progress.lock:
                    self.label_progress.configure(text=progress.current_step)
                    self.progressbar_update.configure(value=progress.progress_percent)
                    progress.update_event.clear()
                    self.progressbar_update.update()
                    self.label_progress.update()
                    if progress.is_done:
                        print("isdone")
                        break
            if progress.error_string:
                raise Exception(progress.error_string)
            
            self.label_progress.configure(text="Done")
            self.progressbar_update.configure(value=0)

        except Exception:
            logging.error(f"Failed to upload firmware", exc_info=True)
            messagebox.showerror("Exception", f"Failed to update firmware\n\n{traceback.format_exc()}")
