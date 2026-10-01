import importlib.util
import os
from pathlib import PureWindowsPath
import sys
import unittest

from chat_reader.paragraphs import ParagraphUnavailable
from probe_fixtures import snapshot


PACKAGE_PATH = r"C:\Program Files\WindowsApps\OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0\app\ChatGPT.exe"


class ParagraphWorkerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.paragraph_worker"),
                             "The isolated paragraph worker is missing")
        from chat_reader import paragraph_worker
        self.worker = paragraph_worker

    def read(self, data, path=PACKAGE_PATH):
        return self.worker.read_paragraph((15, 45), capture=lambda point: data,
                                          lookup_process=lambda pid: path)

    def test_only_the_inspected_desktop_package_can_supply_speech(self):
        """Trusting any Chromium document would accidentally read unrelated apps."""
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", self.read(snapshot()))
        for path in (r"C:\Browser\chrome.exe", r"C:\Unknown\ChatGPT.exe",
                     PACKAGE_PATH.replace("26.928.3736.0", "99.0.0.0")):
            with self.subTest(path=path), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(), path)

    def test_process_lookup_uses_the_captured_document_not_foreground_focus(self):
        queried = []
        def lookup(pid):
            queried.append(pid)
            return PACKAGE_PATH
        self.worker.read_paragraph((15, 45), capture=lambda point: snapshot(), lookup_process=lookup)
        self.assertEqual([123], queried)

    def test_capture_at_a_different_point_is_rejected(self):
        with self.assertRaises(ParagraphUnavailable):
            self.read(snapshot(point=(100, 100)))


class PhysicalPointerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.windows_context"),
                             "Physical-screen coordinate support is missing")
        from chat_reader import windows_context
        self.context = windows_context

    def test_physical_coordinates_preserve_negative_monitor_offsets(self):
        import ctypes
        from ctypes import wintypes
        from types import SimpleNamespace
        def get_point(address):
            point = ctypes.cast(address, ctypes.POINTER(wintypes.POINT)).contents
            point.x, point.y = -1600, 420
            return True
        user32 = SimpleNamespace(GetPhysicalCursorPos=get_point)
        self.assertEqual((-1600, 420), self.context.physical_cursor_position(user32=user32))

    def test_failed_physical_capture_does_not_fall_back_to_logical_coordinates(self):
        from types import SimpleNamespace
        user32 = SimpleNamespace(GetPhysicalCursorPos=lambda address: False)
        with self.assertRaises(OSError):
            self.context.physical_cursor_position(user32=user32)

    def test_native_process_path_query_reads_only_this_test_process(self):
        actual = self.context.process_image_path(os.getpid())
        # Windows venv launchers redirect to the base interpreter process.
        self.assertEqual(PureWindowsPath(sys._base_executable), PureWindowsPath(actual))
