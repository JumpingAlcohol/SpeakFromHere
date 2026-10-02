"""Small read-only Windows boundaries shared by paragraph tools."""

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass(frozen=True)
class ProcessIdentity:
    image_path: str
    package_family: str | None
    package_full_name: str | None
    package_path: str | None


def process_identity(pid, *, kernel32=None):
    """Read image and registered package membership from one process handle.

    Windows package identity is not inferred from a filename or directory.
    An unpackaged process returns no membership; query errors never fall back.
    """
    kernel32 = kernel32 or ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    for function, owner_type in ((kernel32.GetPackageFamilyName, wintypes.HANDLE),
                                 (kernel32.GetPackageFullName, wintypes.HANDLE),
                                 (kernel32.GetPackagePathByFullName, wintypes.LPCWSTR)):
        function.argtypes = [owner_type, ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR]
        function.restype = wintypes.LONG

    def package_string(function, owner, stage, *, allow_unpacked=False):
        size = wintypes.DWORD(0)
        result = function(owner, ctypes.byref(size), None)
        if allow_unpacked and result == 15700:  # APPMODEL_ERROR_NO_PACKAGE
            return None
        if result != 122 or not 1 < size.value <= 32768:  # ERROR_INSUFFICIENT_BUFFER
            raise OSError(f"The pointed application's Windows package identity could not be verified. {stage} failed (Windows error {result}; buffer length {size.value}). Use Alt + S.")
        buffer = ctypes.create_unicode_buffer(size.value)
        result = function(owner, ctypes.byref(size), buffer)
        if result != 0 or not buffer.value:
            raise OSError(f"The pointed application's Windows package identity could not be verified. {stage} failed (Windows error {result}; empty/incomplete response). Use Alt + S.")
        return buffer.value

    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        raise OSError(f"The pointed application's identity could not be verified. OpenProcess failed (Windows error {ctypes.get_last_error()}). Use Alt + S.")
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            raise OSError(f"The pointed application's path could not be verified. QueryFullProcessImageNameW failed (Windows error {ctypes.get_last_error()}). Use Alt + S.")
        image = buffer.value
        family = package_string(kernel32.GetPackageFamilyName, handle, "GetPackageFamilyName", allow_unpacked=True)
        if family is None:
            return ProcessIdentity(image, None, None, None)
        full_name = package_string(kernel32.GetPackageFullName, handle, "GetPackageFullName")
        package_path = package_string(kernel32.GetPackagePathByFullName, full_name, "GetPackagePathByFullName")
        return ProcessIdentity(image, family, full_name, package_path)
    finally:
        kernel32.CloseHandle(handle)


@contextmanager
def physical_coordinate_context(*, user32=None):
    """Use physical pixels only for this native call, then restore the caller.

    GUI and fresh workers can have different DPI defaults. Never change Tk's
    process/window scaling or multiply coordinates by a guessed screen ratio.
    """
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    set_context = user32.SetThreadDpiAwarenessContext
    set_context.argtypes = [ctypes.c_void_p]
    set_context.restype = ctypes.c_void_p
    previous = set_context(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    if not previous:
        raise OSError("Physical screen coordinates could not be verified. Use Alt + S.")
    try:
        yield
    finally:
        if not set_context(previous):
            raise OSError("The screen coordinate context could not be restored. Use Alt + S.")


def physical_cursor_position(*, user32=None):
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    get_point = user32.GetPhysicalCursorPos
    get_point.argtypes = [ctypes.POINTER(wintypes.POINT)]
    get_point.restype = wintypes.BOOL
    point = wintypes.POINT()
    with physical_coordinate_context(user32=user32):
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
