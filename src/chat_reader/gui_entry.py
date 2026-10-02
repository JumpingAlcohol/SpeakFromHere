"""Windowed bundle entry; redirected worker pipes still work without a console."""
import ctypes
import io
import msvcrt
import os
import sys

from chat_reader.app import run


def wrap_output_handle(handle):
    # Duplicate the OS handle so closing the stream never closes a handle owned
    # by another Python fd. Windowed PyInstaller leaves sys.stdout/stderr None.
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.DuplicateHandle.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                      ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint32,
                                      ctypes.c_int, ctypes.c_uint32)
    kernel.DuplicateHandle.restype = ctypes.c_int
    duplicate = ctypes.c_void_p()
    process = kernel.GetCurrentProcess()
    if not kernel.DuplicateHandle(process, handle, process, ctypes.byref(duplicate), 0, False, 2):
        raise ctypes.WinError(ctypes.get_last_error())
    descriptor = msvcrt.open_osfhandle(duplicate.value, os.O_WRONLY | os.O_BINARY)
    return io.TextIOWrapper(os.fdopen(descriptor, "wb"), encoding="utf-8", newline="\n", line_buffering=True)


def restore_redirected_streams():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = (ctypes.c_uint32,)
    kernel.GetStdHandle.restype = ctypes.c_void_p
    for name, number in (("stdout", -11), ("stderr", -12)):
        if getattr(sys, name) is None:
            handle = kernel.GetStdHandle(number & 0xffffffff)
            if handle and handle != ctypes.c_void_p(-1).value:
                setattr(sys, name, wrap_output_handle(handle))


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--paragraph-worker" in arguments:
        restore_redirected_streams()
    return run(["--gui", *arguments])


if __name__ == "__main__":
    main()
