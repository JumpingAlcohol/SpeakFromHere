import importlib.util
import os
from pathlib import PureWindowsPath
import sys
from types import SimpleNamespace
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

    def identity(self, path=PACKAGE_PATH, **changes):
        fields = dict(image_path=path, package_family="OpenAI.Codex_2p2nqsd0c76g0",
                      package_full_name=PureWindowsPath(path).parent.parent.name,
                      package_path=str(PureWindowsPath(path).parent.parent))
        fields.update(changes)
        return SimpleNamespace(**fields)

    def read(self, data, path=PACKAGE_PATH, **changes):
        try:
            return self.worker.read_paragraph((15, 45), capture=lambda point: data,
                lookup_identity=lambda pid: self.identity(path, **changes))
        except TypeError as error:
            self.fail(f"The worker must use OS-backed package identity, not a version path: {error}")

    def test_compatible_codex_versions_use_the_same_bounded_paragraph_suffix(self):
        """Reintroducing an exact-version allowlist breaks updated compatible Codex."""
        for version in ("26.928.3736.0", "26.928.4866.0", "99.0.0.0"):
            with self.subTest(version=version):
                try:
                    text = self.read(snapshot(), PACKAGE_PATH.replace("26.928.3736.0", version))
                except ParagraphUnavailable as error:
                    self.fail(f"A trusted compatible Codex must not fail on version alone: {error}")
                self.assertEqual("Middle with emphasis. Link.\n\nLast.", text)

    def test_similar_layout_does_not_bypass_package_family_or_executable_membership(self):
        """Trusting any Chrome document, process name or lookalike folder leaks other apps."""
        cases = (
            {"package_family": None, "package_full_name": None, "package_path": None},
            {"package_family": "OpenAI.Codex_otherpublisher"},
            {"package_family": "OtherApp_2p2nqsd0c76g0"},
            {"package_path": r"C:\Registered\ActualPackage"},
            {"package_path": r"relative\package"},
            {"package_full_name": ""},
            {"image_path": PACKAGE_PATH.replace("ChatGPT.exe", "helper.exe")},
            {"image_path": PACKAGE_PATH.replace("app\\ChatGPT.exe", "other\\ChatGPT.exe")},
            {"image_path": r"C:\Unknown\ChatGPT.exe"},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ParagraphUnavailable):
                self.read(snapshot(), **changes)

    def test_trusted_updated_package_still_rejects_unsafe_layouts(self):
        """Accepting the new identity must not bypass reply, capture or password checks."""
        from probe_fixtures import node
        broken = snapshot()
        broken["tree"]["framework"] = "Unknown"
        protected = snapshot()
        protected["tree"]["children"][0]["children"][5]["password"] = True
        unfinished = snapshot()
        stream = unfinished["tree"]["children"][0]["children"]
        stream[:] = [item for item in stream if item["id"] != "footer-a"]
        for data in ({**snapshot(), "truncated": True}, broken, protected, unfinished,
                     snapshot(extra=(node("unknown", "textbox", name="Do not read"),))):
            with self.subTest(data=data.get("truncated")), self.assertRaises(ParagraphUnavailable):
                self.read(data, PACKAGE_PATH.replace("26.928.3736.0", "26.928.4866.0"))

    def test_identity_lookup_error_never_falls_back_to_a_named_executable(self):
        def unavailable(pid):
            raise OSError("Identity unavailable")
        try:
            with self.assertRaises(OSError):
                self.worker.read_paragraph((15, 45), capture=lambda point: snapshot(),
                                           lookup_identity=unavailable)
        except TypeError as error:
            self.fail(f"The package identity check is missing: {error}")

    def test_process_lookup_uses_the_captured_document_not_foreground_focus(self):
        queried = []
        def lookup(pid):
            queried.append(pid)
            return self.identity()
        try:
            self.worker.read_paragraph((15, 45), capture=lambda point: snapshot(), lookup_identity=lookup)
        except TypeError as error:
            self.fail(f"The worker must query captured-process package identity: {error}")
        self.assertEqual([123], queried)

    def test_capture_at_a_different_point_is_rejected(self):
        with self.assertRaises(ParagraphUnavailable):
            self.read(snapshot(point=(100, 100)))

    def test_runtime_plan_keeps_skip_types_without_exposing_the_skipped_content(self):
        """Returning only text hides omissions; including labels leaks file/editor contents."""
        from skip_fixtures import edited_files
        plan = self.worker.read_paragraph((15, 45), capture=lambda _: snapshot(extra=edited_files()),
            lookup_identity=lambda _: self.identity(), with_plan=True)
        self.assertEqual("Middle with emphasis. Link.\n\nLast.", plan.text)
        self.assertEqual(["code", "edited_files"], [item.kind for item in plan.skipped])
        self.assertNotIn("synthetic-", str(plan.to_payload()))


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
        user32 = SimpleNamespace(GetPhysicalCursorPos=get_point,
                                 SetThreadDpiAwarenessContext=lambda value: 123)
        self.assertEqual((-1600, 420), self.context.physical_cursor_position(user32=user32))

    def test_failed_physical_capture_does_not_fall_back_to_logical_coordinates(self):
        from types import SimpleNamespace
        user32 = SimpleNamespace(GetPhysicalCursorPos=lambda address: False,
                                 SetThreadDpiAwarenessContext=lambda value: 123)
        with self.assertRaises(OSError):
            self.context.physical_cursor_position(user32=user32)

    def test_native_process_path_query_reads_only_this_test_process(self):
        actual = self.context.process_image_path(os.getpid())
        # Windows venv launchers redirect to the base interpreter process.
        self.assertEqual(PureWindowsPath(sys._base_executable), PureWindowsPath(actual))
