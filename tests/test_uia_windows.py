"""Native UIA checks read only a test-owned hidden window, never other apps."""

import os
import threading
import unittest

import win32api
import win32con
import win32gui


@unittest.skipUnless(os.environ.get("CHAT_READER_UIA_TESTS") == "1",
                     "Opt-in native UIA fixture")
class NativeProbeTests(unittest.TestCase):
    def test_native_cached_properties_preserve_text_and_identity(self):
        """Bad property IDs/cache setup would lose text or conflate different nodes."""
        from chat_reader.uia_probe import WindowsUIA
        ready = threading.Event()
        finished = threading.Event()
        handles = []
        errors = []
        def fixture():
            try:
                parent = win32gui.CreateWindowEx(0, "Static", "Reader test fixture",
                                                win32con.WS_POPUP, 0, 0, 400, 200,
                                                0, 0, win32api.GetModuleHandle(None), None)
                handles.append(parent)
                child = win32gui.CreateWindowEx(0, "Static", "Synthetic paragraph 中文.",
                                               win32con.WS_CHILD, 0, 0, 300, 40,
                                               parent, 0, win32api.GetModuleHandle(None), None)
                handles.append(child)
                ready.set()
                while not finished.wait(0.01):
                    win32gui.PumpWaitingMessages()
            except Exception as error:
                errors.append(error)
                ready.set()
            finally:
                if handles:
                    win32gui.DestroyWindow(handles[0])
        thread = threading.Thread(target=fixture, daemon=True)
        thread.start()
        try:
            self.assertTrue(ready.wait(5), "The owned fixture did not start")
            if errors:
                raise errors[0]
            uia = WindowsUIA()
            child = uia.automation.ElementFromHandle(handles[1])
            info = uia.describe(child)
            parent_info = uia.describe(uia.automation.ElementFromHandle(handles[0]))
            self.assertEqual("Synthetic paragraph 中文.", info["name"])
            self.assertFalse(info["password"])
            self.assertTrue(info["id"])
            self.assertNotEqual(info["id"], parent_info["id"])
            self.assertEqual(50020, info["control_type"])
            self.assertTrue(hasattr(uia.types, "tagPOINT"), "Screen-point COM binding is missing")
        finally:
            finished.set()
            thread.join(5)
            self.assertFalse(thread.is_alive(), "The test-owned window did not close")
