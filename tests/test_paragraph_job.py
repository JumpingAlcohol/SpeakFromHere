import importlib.util
import json
import subprocess
import sys
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

    def script(self, text):
        payload = json.dumps({"point": [15, 45], "text": text}, ensure_ascii=True)
        return f"print({payload!r})"

    def test_large_unicode_reply_is_drained_without_blocking_on_pipe_capacity(self):
        text = "Paragraph 中文. " * 12000
        job = self.job(["import json; print(json.dumps({'point': [15,45], 'text': 'Paragraph \\u4e2d\\u6587. ' * 12000}))"])
        job.start((15, 45))
        self.assertEqual((text, None), self.wait_result(job))
        self.assertIsNone(job.poll())

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
        self.children[0].wait(timeout=3)
        job.start((15, 45))
        self.assertEqual(("New reply", None), self.wait_result(job))

    def test_cancel_prevents_late_speech_and_terminates_owned_worker(self):
        job = self.job(["import time; time.sleep(30)"])
        job.start((15, 45))
        job.cancel()
        self.children[0].wait(timeout=3)
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
        job = self.job(["import time; time.sleep(30)"])
        start = time.monotonic()
        job.start((15, 45))
        self.assertLess(time.monotonic() - start, 1)
        self.assertIsNone(job.poll())
