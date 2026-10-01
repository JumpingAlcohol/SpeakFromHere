"""Small read-only Windows boundaries shared by paragraph tools."""

import ctypes
from ctypes import wintypes


def physical_cursor_position(*, user32=None):
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    get_point = user32.GetPhysicalCursorPos
    get_point.argtypes = [ctypes.POINTER(wintypes.POINT)]
    get_point.restype = wintypes.BOOL
    point = wintypes.POINT()
    if not get_point(ctypes.byref(point)):
        raise OSError("The physical mouse position could not be read.")
    return point.x, point.y


def process_image_path(pid):
    """Query executable identity without reading process memory or elevating."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError("The pointed application's identity could not be verified.")
    try:
        length = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(length.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(length)):
            raise OSError("The pointed application's path could not be verified.")
        return buffer.value
    finally:
        kernel32.CloseHandle(handle)
