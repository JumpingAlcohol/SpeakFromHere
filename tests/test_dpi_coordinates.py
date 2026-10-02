"""Scaled-desktop regression: physical input must not hit another application."""
import ctypes
import json
import os
import subprocess
import sys
import threading
import unittest
import uuid
from types import SimpleNamespace

import win32api
import win32con
import win32gui


class CoordinateContextTests(unittest.TestCase):
    def test_failed_dpi_context_refuses_capture_instead_of_guessing_coordinates(self):
        from chat_reader import windows_context
        self.assertTrue(hasattr(windows_context, "physical_coordinate_context"))
        user = SimpleNamespace(SetThreadDpiAwarenessContext=lambda value: None)
        with self.assertRaises(OSError):
            with windows_context.physical_coordinate_context(user32=user):
                self.fail("Capture must not run with an unknown DPI context")

    def test_native_exception_restores_previous_context(self):
        from chat_reader import windows_context
        self.assertTrue(hasattr(windows_context, "physical_coordinate_context"))
        contexts = []
        def set_context(value):
            contexts.append(ctypes.c_ssize_t(value.value if hasattr(value, "value") else value).value)
            return 123
        user = SimpleNamespace(SetThreadDpiAwarenessContext=set_context)
        with self.assertRaisesRegex(RuntimeError, "Synthetic failure"):
            with windows_context.physical_coordinate_context(user32=user):
                raise RuntimeError("Synthetic failure")
        self.assertEqual([-4, 123], contexts)


@unittest.skipUnless(os.environ.get("CHAT_READER_UIA_TESTS") == "1", "Opt-in scaled desktop fixture")
class PhysicalCoordinateTests(unittest.TestCase):
    def test_unaware_child_uses_physical_point_and_hits_only_the_owned_window(self):
        """Missing capture DPI context turns the physical point into another target."""
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
        ready, finished = threading.Event(), threading.Event()
        handles, errors = [], []
        name = "ReaderDpiFixture_" + uuid.uuid4().hex

        def fixture():
            old = user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
            registered = False
            try:
                window_class = win32gui.WNDCLASS()
                window_class.hInstance = win32api.GetModuleHandle(None)
                window_class.lpszClassName = name
                window_class.lpfnWndProc = win32gui.DefWindowProc
                win32gui.RegisterClass(window_class)
                registered = True
                handles.append(win32gui.CreateWindowEx(
                    win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW | 0x08000000,
                    name, "Synthetic DPI fixture", win32con.WS_POPUP | win32con.WS_VISIBLE,
                    600, 440, 160, 100, 0, 0, win32api.GetModuleHandle(None), None))
                ready.set()
                while not finished.wait(0.01):
                    win32gui.PumpWaitingMessages()
            except Exception as error:
                errors.append(error)
                ready.set()
            finally:
                if handles:
                    win32gui.DestroyWindow(handles[0])
                if registered:
                    win32gui.UnregisterClass(name, win32api.GetModuleHandle(None))
                if old:
                    user.SetThreadDpiAwarenessContext(old)

        thread = threading.Thread(target=fixture, daemon=True)
        thread.start()
        try:
            self.assertTrue(ready.wait(5))
            if errors:
                raise errors[0]
            old = user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
            try:
                self.assertEqual(handles[0], win32gui.WindowFromPoint((640, 480)),
                                 f"Owned fixture must cover the physical point: {win32gui.GetWindowRect(handles[0])}")
            finally:
                user.SetThreadDpiAwarenessContext(old)
            # Isolated child matches the GUI worker's DPI-unaware startup.
            script = '''
import ctypes,json,sys,os,types,importlib
archive_path=os.environ.get("CHAT_READER_COORDINATE_ARCHIVE")
if archive_path:
 from PyInstaller.archive.readers import CArchiveReader
 embedded=CArchiveReader(archive_path).open_embedded_archive("PYZ.pyz")
 for short in ("windows_context","uia_probe"):
  name="chat_reader."+short
  module=types.ModuleType(name)
  sys.modules[name]=module
  setattr(importlib.import_module("chat_reader"),short,module)
  exec(embedded.extract(name),module.__dict__)
from ctypes import wintypes
from chat_reader.uia_probe import WindowsUIA
u=ctypes.WinDLL("user32",use_last_error=True)
u.SetThreadDpiAwarenessContext.argtypes=[ctypes.c_void_p]
u.SetThreadDpiAwarenessContext.restype=ctypes.c_void_p
u.GetThreadDpiAwarenessContext.restype=ctypes.c_void_p
u.GetAwarenessFromDpiAwarenessContext.argtypes=[ctypes.c_void_p]
before=u.GetAwarenessFromDpiAwarenessContext(u.GetThreadDpiAwarenessContext())
client=WindowsUIA()
element=client.element_at((640,480))
# Get PID only; never describe an accidentally pointed external window.
pid=int(element.GetCurrentPropertyValue(30002))
bounds=client.describe(element)["bounds"] if pid==int(sys.argv[1]) else None
print(json.dumps({"target_pid":pid,"bounds":bounds,"awareness_before":before,"awareness_after":u.GetAwarenessFromDpiAwarenessContext(u.GetThreadDpiAwarenessContext())}))
'''
            result = subprocess.run([sys.executable, "-c", script, str(os.getpid())], capture_output=True,
                                    text=True, encoding="utf-8", timeout=15,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(0, result.returncode, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(os.getpid(), data["target_pid"],
                             "Physical point incorrectly resolves a different app on a scaled desktop")
            self.assertEqual(0, data["awareness_before"], "Child must match the unaware worker startup")
            self.assertEqual(0, data["awareness_after"], "Capture must restore caller's DPI context")
            self.assertEqual([600.0, 440.0, 160.0, 100.0], data["bounds"],
                             "Paragraph bounds must share the physical point's coordinate space")
        finally:
            finished.set()
            thread.join(5)
            self.assertFalse(thread.is_alive())

    def test_cursor_is_identical_in_unaware_and_per_monitor_contexts(self):
        """The same stationary cursor must not be halved by an unaware console/worker."""
        from chat_reader.windows_context import physical_cursor_position
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
        old = user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
        try:
            first = physical_cursor_position()
            user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-1))
            unaware = physical_cursor_position()
            user.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
            last = physical_cursor_position()
            self.assertEqual(first, last, "Mouse moved during the short coordinate check; retry")
            self.assertEqual(first, unaware, "DPI-unaware caller received scaled logical coordinates")
        finally:
            user.SetThreadDpiAwarenessContext(old)
