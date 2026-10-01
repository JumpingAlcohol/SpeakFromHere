import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest


class InspectionCommandTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.inspect_paragraph"),
                             "The mouse-point inspection command is missing")
        from chat_reader import inspect_paragraph
        self.command = inspect_paragraph

    def test_worker_is_bounded_and_unicode_snapshot_is_saved_locally(self):
        """Wrong worker coordinates, an unbounded call or dropping text would break this capture."""
        result = {"schema_version": 1, "point": [100, 200], "point_id": "p",
                  "verified_reply": False, "node_count": 1, "truncated": False,
                  "tree": {"name": "Synthetic 中文."}, "ancestors": []}
        calls = []
        def worker(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout=json.dumps(result), stderr="")
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "work" / "probe.json"
            saved = self.command.inspect_and_save((100, 200), output, runner=worker)
            self.assertEqual(result, json.loads(output.read_text(encoding="utf-8")))
            self.assertEqual(result, saved)
        args, options = calls[0]
        self.assertEqual(["-m", "chat_reader.inspect_paragraph", "--worker", "100", "200"], args[1:])
        self.assertGreater(options["timeout"], 0)
        self.assertLessEqual(options["timeout"], 30)
        self.assertFalse(options.get("shell", False))

    def test_hung_worker_reports_timeout_without_overwriting_previous_capture(self):
        def hung(args, **kwargs):
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "probe.json"
            output.write_text("previous capture", encoding="utf-8")
            with self.assertRaises(self.command.ProbeUnavailable):
                self.command.inspect_and_save((100, 200), output, runner=hung)
            self.assertEqual("previous capture", output.read_text(encoding="utf-8"))

    def test_worker_failure_or_invalid_result_does_not_create_a_success_file(self):
        for result in (SimpleNamespace(returncode=1, stdout="", stderr="Unavailable."),
                       SimpleNamespace(returncode=0, stdout="not JSON", stderr=""),
                       SimpleNamespace(returncode=0, stdout='{"verified_reply":true}', stderr="")):
            with self.subTest(result=result), tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / "probe.json"
                with self.assertRaises(self.command.ProbeUnavailable):
                    self.command.inspect_and_save((100, 200), output,
                                                 runner=lambda *args, **kwargs: result)
                self.assertFalse(output.exists())
