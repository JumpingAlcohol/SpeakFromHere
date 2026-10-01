import io
import json
import sys
import unittest
from unittest.mock import patch

from chat_reader import app
from chat_reader.paragraph_job import ParagraphCapture
from test_app import RecordingEngine
from test_paragraph_runtime import Capture


class PortableParagraphTests(unittest.TestCase):
    def test_portable_launch_reads_a_paragraph_without_needing_a_python_flag(self):
        """Dropping frozen-default enablement leaves the download selection-only."""
        self.run_reader(frozen=True, argv=[])

    def test_explicit_paragraph_flag_also_works_in_portable_mode(self):
        self.run_reader(frozen=True, argv=["--paragraphs"])

    def run_reader(self, *, frozen, argv):
        engine = RecordingEngine()
        messages = iter([(True, (0, app.win32con.WM_HOTKEY, 5, 0, 0, (0, 0))),
                         (True, (0, app.win32con.WM_QUIT, 0, 0, 0, (0, 0)))])
        with patch.object(sys, "frozen", frozen, create=True), \
                patch.object(app.keyboard, "Controller"), \
                patch.object(app.win32com.client, "Dispatch", return_value=engine), \
                patch.object(app.win32gui, "RegisterHotKey"), \
                patch.object(app.win32gui, "UnregisterHotKey"), \
                patch.object(app.win32gui, "PeekMessage", side_effect=messages), \
                patch("chat_reader.windows_context.physical_cursor_position", return_value=(15, 45)), \
                patch("chat_reader.paragraph_job.ParagraphCapture", return_value=Capture()), \
                patch.object(sys, "stdout", new=io.StringIO()):
            app.run(argv)
        self.assertIn(("Middle.\n\nLast.", 19), engine.actions)
        self.assertEqual(("", 3), engine.actions[-1])

    def test_internal_worker_returns_unicode_json_without_starting_speech_or_hotkeys(self):
        """Routing the worker back into the reader causes recursive instances/conflicts."""
        buffer = io.BytesIO()
        output = io.TextIOWrapper(buffer, encoding="utf-8")
        with patch("chat_reader.paragraph_worker.read_paragraph", return_value="Synthetic 中文."), \
                patch.object(sys, "stdout", output), \
                patch.object(app.win32com.client, "Dispatch", side_effect=AssertionError("Worker started speech")), \
                patch.object(app.win32gui, "RegisterHotKey", side_effect=AssertionError("Worker registered hotkeys")):
            with self.assertRaises(SystemExit) as raised:
                app.run(["--paragraph-worker", "15", "45"])
            output.flush()
        self.assertEqual(0, raised.exception.code)
        self.assertEqual({"point": [15, 45], "text": "Synthetic 中文."},
                         json.loads(buffer.getvalue().decode("utf-8")))

    def test_frozen_capture_reuses_its_executable_instead_of_python_module_arguments(self):
        """A frozen executable cannot handle Python's -m command line."""
        class Child:
            returncode = 0
            def communicate(self, timeout=None):
                return '{"point": [15,45], "text": "Synthetic reply"}', ''
            def poll(self):
                return 0
        commands = []
        def launch(command, **kwargs):
            commands.append(command)
            return Child()
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", r"C:\Test\AIChatReader.exe"):
            job = ParagraphCapture(launch=launch)
            try:
                job.start((15, 45))
                for thread in job.threads:
                    thread.join(2)
                self.assertEqual(("Synthetic reply", None), job.poll())
            finally:
                job.close()
        self.assertEqual([[r"C:\Test\AIChatReader.exe", "--paragraph-worker", "15", "45"]], commands)
