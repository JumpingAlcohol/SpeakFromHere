import io
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
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
        # Only the external COM allocation is substituted; real cue generation,
        # voice factory, speaker and paragraph/reader routing remain in use.
        class MemoryStream:
            def __init__(self):
                self.Format = SimpleNamespace(Type=0)
                self.data = None
            def SetData(self, data):
                self.data = data
        stream = MemoryStream()
        messages = iter([(True, (0, app.win32con.WM_HOTKEY, 5, 0, 0, (0, 0))),
                         (True, (0, app.win32con.WM_QUIT, 0, 0, 0, (0, 0)))])
        with tempfile.TemporaryDirectory() as folder, \
                patch("chat_reader.app.settings_path", return_value=Path(folder) / "settings.json"), \
                patch.object(sys, "frozen", frozen, create=True), \
                patch.object(app.keyboard, "Controller"), \
                patch("chat_reader.windows_audio.create_voice", return_value=engine), \
                patch("chat_reader.windows_audio.comtypes.client.CreateObject", return_value=stream), \
                patch.object(app.win32gui, "RegisterHotKey"), \
                patch.object(app.win32gui, "UnregisterHotKey"), \
                patch.object(app.win32gui, "PeekMessage", side_effect=messages), \
                patch("chat_reader.windows_context.physical_cursor_position", return_value=(15, 45)), \
                patch("chat_reader.paragraph_job.ParagraphCapture", return_value=Capture()), \
                patch.object(sys, "stdout", new=io.StringIO()):
            app.run(argv)
        self.assertEqual([("stream", 3), ("Middle.\n\nLast.", 17)], engine.actions[:2])
        self.assertEqual(("", 3), engine.actions[-1])

    def test_internal_worker_returns_unicode_json_without_starting_speech_or_hotkeys(self):
        """Routing the worker back into the reader causes recursive instances/conflicts."""
        buffer = io.BytesIO()
        output = io.TextIOWrapper(buffer, encoding="utf-8")
        from chat_reader.paragraph_worker import read_paragraph
        from test_paragraph_worker import ParagraphWorkerTests
        from probe_fixtures import snapshot, node
        data = snapshot()
        data["tree"]["children"][0]["children"][5]["children"] = [node("unicode-body", "description", name="Synthetic 中文.")]
        def captured(point, *, with_plan=False):
            self.assertEqual((15, 45), point)
            self.assertTrue(with_plan, "Worker route must preserve omission metadata")
            return read_paragraph(point, capture=lambda _: data,
                lookup_identity=lambda _: ParagraphWorkerTests().identity(), with_plan=with_plan)
        with patch("chat_reader.paragraph_worker.read_paragraph", side_effect=captured), \
                patch.object(sys, "stdout", output), \
                patch("chat_reader.windows_audio.create_voice", side_effect=AssertionError("Worker started speech")), \
                patch.object(app.win32gui, "RegisterHotKey", side_effect=AssertionError("Worker registered hotkeys")):
            with self.assertRaises(SystemExit) as raised:
                app.run(["--paragraph-worker", "15", "45"])
            output.flush()
        self.assertEqual(0, raised.exception.code)
        self.assertEqual({"point": [15, 45], "text": "Synthetic 中文.\n\nLast.",
                          "skipped": [{"kind": "code", "ordinal": 3, "before_start": False}]},
                         json.loads(buffer.getvalue().decode("utf-8")))

    def test_frozen_entries_use_the_same_lightweight_neighbor_worker(self):
        """Relaunching the whole GUI/console adds unpacking and unrelated imports."""
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
        with tempfile.TemporaryDirectory() as folder:
            worker = Path(folder) / "reader-worker" / "SpeakFromHereWorker.exe"
            worker.parent.mkdir()
            worker.touch()
            for entry in ("SpeakFromHere.exe", "SpeakFromHereConsole.exe"):
                with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(Path(folder) / entry)):
                    job = ParagraphCapture(launch=launch)
                    try:
                        job.start((15, 45))
                        for thread in job.threads:
                            thread.join(2)
                        self.assertEqual(("Synthetic reply", None), job.poll())
                    finally:
                        job.close()
            self.assertEqual([[str(worker), "15", "45"]] * 2, commands)

    def test_missing_portable_worker_reports_extract_full_zip_without_launching(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(sys, "frozen", True, create=True), \
                patch.object(sys, "executable", str(Path(folder) / "SpeakFromHere.exe")):
            def launch(command, **kwargs):
                self.fail("A missing helper must not restart the heavyweight GUI")
            job = ParagraphCapture(launch=launch)
            try:
                job.start((15, 45))
                for thread in job.threads:
                    thread.join(2)
                text, error = job.poll()
                self.assertIsNone(text)
                self.assertIn("reader-worker", error)
                self.assertIn("ZIP", error)
            finally:
                job.close()

    def test_source_pythonw_player_uses_console_python_for_redirected_worker_output(self):
        """pythonw provides no sys.stdout; its hidden worker cannot return JSON."""
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
        with tempfile.TemporaryDirectory() as folder:
            python = Path(folder) / "python.exe"
            python.touch()
            with patch.object(sys, "frozen", False, create=True), \
                    patch.object(sys, "executable", str(Path(folder) / "pythonw.exe")):
                job = ParagraphCapture(launch=launch)
                try:
                    job.start((15, 45))
                    for thread in job.threads:
                        thread.join(2)
                    self.assertEqual(("Synthetic reply", None), job.poll())
                    self.assertEqual([[str(python), "-m", "chat_reader.paragraph_worker", "15", "45"]], commands)
                finally:
                    job.close()
