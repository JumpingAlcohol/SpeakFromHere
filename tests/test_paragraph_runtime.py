import threading
import unittest

from chat_reader.core import run_reader_loop
from test_runtime import Clock, Desktop, Speaker


class Capture:
    """External asynchronous capture boundary, never the parser under test."""
    def __init__(self):
        self.starts = []
        self.pending = None
        self.closed = False
        self.cancellations = 0
        self.outcomes = iter([("Middle.\n\nLast.", None)] * 3)
        self.delay = False

    def start(self, point):
        self.starts.append(point)
        self.pending = next(self.outcomes)

    def poll(self):
        if self.delay:
            return None
        result, self.pending = self.pending, None
        return result

    def cancel(self):
        self.pending = None
        self.cancellations += 1

    def close(self):
        self.cancel()
        self.closed = True


class ParagraphRuntimeTests(unittest.TestCase):
    def run_case(self, events, capture=None):
        clock = Clock()
        desktop = Desktop(clock)
        desktop.events = iter(events)
        desktop.pointer_position = lambda: (-1600, 420)
        speaker = Speaker()
        messages = []
        capture = capture or Capture()
        run_reader_loop(desktop, speaker, report=messages.append, paragraph_reader=capture,
                        clock=clock.monotonic, sleep=clock.sleep)
        return desktop, speaker, messages, capture

    def test_repeated_paragraphs_speak_on_the_main_thread_without_copying(self):
        desktop, speaker, messages, capture = self.run_case(["paragraph", "paragraph", "quit"])
        self.assertEqual(["Middle.\n\nLast."] * 2, speaker.spoken)
        self.assertEqual([threading.get_ident()] * 2, speaker.threads)
        self.assertEqual([(-1600, 420)] * 2, capture.starts)
        self.assertEqual(7, desktop.sequence)
        self.assertTrue(desktop.closed and capture.closed and speaker.stopped)

    def test_plan_discloses_omissions_and_speaks_only_its_prose(self):
        """Passing a plan to SAPI or omitting the notice breaks the user's transparency requirement."""
        import json
        from chat_reader.paragraphs import ReadingPlan, SkippedBlock
        capture = Capture()
        capture.outcomes = iter([(ReadingPlan("Body.", (SkippedBlock("table", 2, False),)), None)])
        desktop, speaker, messages, _ = self.run_case(["paragraph", "quit"], capture)
        self.assertEqual(["Body."], speaker.spoken)
        notices = [message[len("Skipped content: "):] for message in messages if message.startswith("Skipped content: ")]
        self.assertEqual([[{"kind": "table", "ordinal": 2, "before_start": False}]], [json.loads(item) for item in notices])
        self.assertEqual(7, desktop.sequence, "Reading plans must never copy skipped content")

    def test_stop_pause_and_selection_cancel_pending_capture_before_it_can_speak(self):
        for event in ("stop", "pause", "read"):
            with self.subTest(event=event):
                capture = Capture()
                capture.delay = True
                desktop, speaker, messages, capture = self.run_case(["paragraph", event, "quit"], capture)
                self.assertGreaterEqual(capture.cancellations, 2)
                self.assertIsNone(capture.pending)
                self.assertEqual(["Hello! This is my first Python project."] if event == "read" else [], speaker.spoken)

    def test_failure_keeps_selection_and_subsequent_paragraph_reading_available(self):
        capture = Capture()
        capture.outcomes = iter([(None, "Unsupported table"), ("New paragraph.", None)])
        desktop, speaker, messages, capture = self.run_case(["paragraph", "read", "paragraph", "quit"], capture)
        self.assertEqual(["Hello! This is my first Python project.", "New paragraph."], speaker.spoken)
        self.assertTrue(any("Unsupported table" in message for message in messages))

    def test_exit_always_closes_pending_capture(self):
        capture = Capture()
        capture.delay = True
        desktop, speaker, messages, capture = self.run_case(["paragraph", "quit"], capture)
        self.assertTrue(capture.closed)
        self.assertEqual([], speaker.spoken)

    def test_rejected_paragraph_only_reports_manual_selection_fallback_without_copying(self):
        capture = Capture()
        capture.outcomes = iter([(None, "Unsupported table")])
        desktop, speaker, messages, capture = self.run_case(["paragraph", "quit"], capture)
        self.assertEqual([], speaker.spoken)
        self.assertEqual(7, desktop.sequence)
        self.assertTrue(any("Unsupported table" in message and "Alt + S" in message for message in messages))

    def test_ctrl_c_closes_capture_even_when_windows_message_poll_is_interrupted(self):
        clock = Clock()
        desktop = Desktop(clock)
        def interrupt():
            raise KeyboardInterrupt
        desktop.next_hotkey = interrupt
        capture = Capture()
        speaker = Speaker()
        run_reader_loop(desktop, speaker, paragraph_reader=capture, report=lambda _: None,
                        clock=clock.monotonic, sleep=clock.sleep)
        self.assertTrue(capture.closed and desktop.closed and speaker.stopped)
