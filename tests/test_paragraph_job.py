import importlib.util
import json
import subprocess
import sys
import threading
import time
import unittest


class ParagraphJobTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("chat_reader.paragraph_job"),
                             "Nonblocking paragraph capture is missing")
        from chat_reader.paragraph_job import ParagraphCapture
        self.capture_type = ParagraphCapture
        self.children = []
        self.jobs = []

    def tearDown(self):
        for job in getattr(self, "jobs", []):
            job.close()
        for child in getattr(self, "children", []):
            if child.poll() is None:
                child.kill()
            child.wait(timeout=3)

    def job(self, scripts, *, timeout=20):
        scripts = iter(scripts)
        def launch(command, **kwargs):
            self.assertEqual([sys.executable, "-m", "chat_reader.paragraph_worker", "15", "45"], command)
            child = subprocess.Popen([sys.executable, "-c", next(scripts)], **kwargs)
            self.children.append(child)
            return child
        job = self.capture_type(launch=launch, timeout=timeout)
        self.jobs.append(job)
        return job

    def wait_result(self, job):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = job.poll()
            if result is not None:
                return result
            time.sleep(0.01)
        self.fail("The paragraph capture did not return a result")

    def wait_child(self, index=0):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if len(self.children) > index:
                return self.children[index]
            time.sleep(0.01)
        self.fail("The owned worker did not launch")

    def script(self, text):
        payload = json.dumps({"point": [15, 45], "text": text}, ensure_ascii=True)
        return f"print({payload!r})"

    def test_large_unicode_reply_is_drained_without_blocking_on_pipe_capacity(self):
        text = "Paragraph 中文. " * 12000
        job = self.job(["import json; print(json.dumps({'point': [15,45], 'text': 'Paragraph \\u4e2d\\u6587. ' * 12000}))"])
        job.start((15, 45))
        self.assertEqual((text, None), self.wait_result(job))
        self.assertIsNone(job.poll())

    def test_worker_omissions_survive_the_real_pipe_and_are_not_silently_dropped(self):
        """Discarding worker metadata would make skipped content invisible to the player."""
        payload = {"point": [15, 45], "text": "Body.", "skipped": [
            {"kind": "table", "ordinal": 2, "before_start": False}]}
        job = self.job([f"print({json.dumps(payload)!r})"])
        job.start((15, 45))
        plan, error = self.wait_result(job)
        self.assertIsNone(error)
        self.assertTrue(hasattr(plan, "skipped"), "The pipe dropped skip metadata")
        self.assertEqual("Body.", plan.text)
        self.assertEqual([("table", 2, False)], [(s.kind, s.ordinal, s.before_start) for s in plan.skipped])

    def test_invalid_skip_metadata_never_delivers_a_partial_reading_result(self):
        """Accepting malformed omission metadata silently conceals content or spoofs the GUI."""
        payload = {"point": [15, 45], "text": "Body.", "skipped": [
            {"kind": "anything", "ordinal": 2, "before_start": False}]}
        job = self.job([f"print({json.dumps(payload)!r})"])
        job.start((15, 45))
        plan, error = self.wait_result(job)
        self.assertIsNone(plan)
        self.assertTrue(error)

    def test_timeout_kills_only_its_owned_worker_and_reports_failure(self):
        job = self.job(["import time; time.sleep(30)"], timeout=0.1)
        job.start((15, 45))
        text, error = self.wait_result(job)
        self.assertIsNone(text)
        self.assertIn("timed out", error)
        self.assertIsNotNone(self.children[0].poll())

    def test_replacement_discards_old_results_and_keeps_the_new_selection(self):
        job = self.job([self.script("Old reply"), self.script("New reply")])
        job.start((15, 45))
        self.wait_child().wait(timeout=3)
        job.start((15, 45))
        self.assertEqual(("New reply", None), self.wait_result(job))

    def test_cancel_prevents_late_speech_and_terminates_owned_worker(self):
        job = self.job(["import time; time.sleep(30)"])
        job.start((15, 45))
        child = self.wait_child()
        job.cancel()
        child.wait(timeout=3)
        self.assertIsNone(job.poll())

    def test_invalid_output_and_worker_error_are_reported_not_spoken(self):
        scripts = ["print('not JSON')", "print('{\"point\": [0, 0], \"text\": \"Wrong\"}')",
                   "import sys; print('Unsupported layout', file=sys.stderr); sys.exit(1)"]
        job = self.job(scripts)
        for script in scripts:
            job.start((15, 45))
            text, error = self.wait_result(job)
            self.assertIsNone(text)
            self.assertTrue(error)

    def test_start_returns_while_worker_is_waiting_so_controls_can_still_run(self):
        # Windows CreateProcess occasionally costs ~2s on this machine. Measure
        # the collector's nonblocking behavior, not external process creation.
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8",
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.children.append(child)
        def launch(command, **kwargs):
            self.assertEqual([sys.executable, "-m", "chat_reader.paragraph_worker", "15", "45"], command)
            return child
        job = self.capture_type(launch=launch)
        self.jobs.append(job)
        start = time.monotonic()
        job.start((15, 45))
        self.assertLess(time.monotonic() - start, 1)
        self.assertIsNone(job.poll())
        self.assertIsNone(child.poll(), "The slow worker must still be running")

    def test_slow_native_launch_does_not_block_controls_and_canceled_launch_is_reaped(self):
        """Synchronous Popen blocks the player; losing a pending child leaks it."""
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding="utf-8")
        self.children.append(child)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def launch(command, **kwargs):
            entered.set()
            release.wait(1.2)
            return child
        job = self.capture_type(launch=launch)
        self.jobs.append(job)
        before = time.monotonic()
        job.start((15, 45))
        try:
            self.assertLess(time.monotonic() - before, 0.5, "Native launch blocked the control thread")
            self.assertTrue(entered.wait(1))
            job.cancel()
        finally:
            release.set()
        child.wait(timeout=3)
        for thread in job.threads:
            thread.join(3)
        self.assertIsNone(job.poll(), "Canceled startup must never deliver text")

    def test_launch_failure_is_reported_as_a_result_instead_of_losing_the_job(self):
        def launch(command, **kwargs):
            raise PermissionError("Synthetic launch denied")
        job = self.capture_type(launch=launch)
        self.jobs.append(job)
        job.start((15, 45))
        text, error = self.wait_result(job)
        self.assertIsNone(text)
        self.assertIn("Synthetic launch denied", error)

    def test_replacing_a_pending_launch_reaps_it_without_discarding_the_new_result(self):
        """An old Popen returning late must not become the active request again."""
        old = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.children.append(old)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def launch(command, **kwargs):
            if command[-2:] == ["15", "45"]:
                entered.set()
                release.wait(2)
                return old
            self.assertEqual(["25", "55"], command[-2:])
            # Different coordinates must be validated against the new request.
            replacement = subprocess.Popen([sys.executable, "-c",
                "print('{\"point\": [25,55], \"text\": \"New reply\"}')"], **kwargs)
            self.children.append(replacement)
            return replacement
        job = self.capture_type(launch=launch)
        self.jobs.append(job)
        try:
            job.start((15, 45))
            self.assertTrue(entered.wait(1))
            job.start((25, 55))
            release.set()
            self.assertEqual(("New reply", None), self.wait_result(job))
            old.wait(timeout=3)
            for thread in job.threads:
                thread.join(3)
            self.assertIsNone(job.poll())
        finally:
            release.set()

    def test_timeout_includes_native_startup_not_just_result_collection(self):
        child = subprocess.Popen([sys.executable, "-c", self.script("Late reply")],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.children.append(child)
        def launch(command, **kwargs):
            time.sleep(0.1)
            return child
        job = self.capture_type(launch=launch, timeout=0.05)
        self.jobs.append(job)
        job.start((15, 45))
        text, error = self.wait_result(job)
        self.assertIsNone(text, "A reply delivered past the full deadline must not speak")
        self.assertIn("timed out", error)
