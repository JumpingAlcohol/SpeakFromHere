import threading
import unittest

from chat_reader import core


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Desktop:
    """Controlled boundary: physical keys and clipboard belong to Windows."""
    def __init__(self, clock, copy_works=True, held_forever=False):
        self.clock = clock
        self.copy_works = copy_works
        self.held_forever = held_forever
        self.sequence = 7
        self.text = r".\.venv\Scripts\python.exe -m chat_reader.app"
        self.copied_with_alt_down = None
        self.closed = False
        self.events = iter(["read", "read", "quit"])

    def keys_down(self):
        return self.held_forever or self.clock.now < 0.05

    def clipboard_sequence(self):
        return self.sequence

    def send_copy(self):
        self.copied_with_alt_down = self.keys_down()
        if self.copy_works and not self.copied_with_alt_down:
            self.sequence += 1
            self.text = "Hello! This is my first Python project."

    def clipboard_text(self):
        return self.text

    def register(self):
        pass

    def next_hotkey(self):
        return next(self.events)

    def close(self):
        self.closed = True


class Speaker:
    def __init__(self):
        self.spoken = []
        self.stopped = False
        self.threads = []
        self.paused = False
        self.controls = []

    def speak(self, text):
        self.spoken.append(text)
        self.threads.append(threading.get_ident())

    def stop(self):
        self.stopped = True
        self.paused = False
        self.controls.append("stopped")

    def toggle_pause(self):
        self.paused = not self.paused
        state = "paused" if self.paused else "resumed"
        self.controls.append(state)
        return state


class CaptureTests(unittest.TestCase):
    def capture(self, desktop, clock):
        self.assertTrue(hasattr(core, "capture_selection"), "Verified selection capture is missing")
        return core.capture_selection(desktop, clock=clock.monotonic, sleep=clock.sleep)

    def test_waits_for_alt_release_before_copying(self):
        clock = Clock()
        desktop = Desktop(clock)
        self.assertEqual("Hello! This is my first Python project.", self.capture(desktop, clock))
        self.assertFalse(desktop.copied_with_alt_down)

    def test_failed_copy_returns_no_text_instead_of_old_command(self):
        clock = Clock()
        desktop = Desktop(clock, copy_works=False)
        self.assertEqual("", self.capture(desktop, clock))
        self.assertLess(clock.now, 3)

    def test_held_keys_time_out_without_sending_copy(self):
        clock = Clock()
        desktop = Desktop(clock, held_forever=True)
        self.assertEqual("", self.capture(desktop, clock))
        self.assertIsNone(desktop.copied_with_alt_down)


class RuntimeTests(unittest.TestCase):
    def test_playback_hotkeys_do_not_copy_text_or_exit_the_reader(self):
        clock = Clock()
        desktop = Desktop(clock)
        desktop.events = iter(["read", "pause", "pause", "stop", "read", "quit"])
        speaker = Speaker()
        messages = []
        self.run_loop(desktop, speaker, clock, messages)
        self.assertEqual(["Hello! This is my first Python project."] * 2, speaker.spoken)
        self.assertEqual(["paused", "resumed", "stopped", "stopped"], speaker.controls)
        self.assertEqual(9, desktop.sequence)  # Only the two reads should copy.
        self.assertIn("Speech paused. Alt + P to resume.", messages)
        self.assertIn("Speech resumed.", messages)
        self.assertIn("Speech stopped. Select text and press Alt + S to read again.", messages)

    def run_loop(self, desktop, speaker, clock, messages):
        self.assertTrue(hasattr(core, "run_reader_loop"), "Interruptible main loop is missing")
        core.run_reader_loop(desktop, speaker, report=messages.append,
                             clock=clock.monotonic, sleep=clock.sleep)

    def test_repeated_hotkeys_read_on_the_owning_thread_and_quit_cleans_up(self):
        clock = Clock()
        desktop = Desktop(clock)
        speaker = Speaker()
        messages = []
        self.run_loop(desktop, speaker, clock, messages)
        self.assertEqual(["Hello! This is my first Python project."] * 2, speaker.spoken)
        self.assertEqual([threading.get_ident()] * 2, speaker.threads)
        self.assertTrue(speaker.stopped)
        self.assertTrue(desktop.closed)
        self.assertTrue(any("Hello!" in message for message in messages))

    def test_ctrl_c_while_idle_stops_voice_and_releases_hotkeys(self):
        clock = Clock()
        desktop = Desktop(clock)
        def interrupt():
            raise KeyboardInterrupt
        desktop.next_hotkey = interrupt
        speaker = Speaker()
        self.run_loop(desktop, speaker, clock, [])
        self.assertTrue(speaker.stopped)
        self.assertTrue(desktop.closed)

    def test_one_copy_error_does_not_disable_subsequent_hotkeys(self):
        clock = Clock()
        desktop = Desktop(clock)
        original = desktop.send_copy
        attempts = []
        def send_copy():
            attempts.append(True)
            if len(attempts) == 1:
                raise OSError("clipboard temporarily unavailable")
            original()
        desktop.send_copy = send_copy
        speaker = Speaker()
        messages = []
        self.run_loop(desktop, speaker, clock, messages)
        self.assertEqual(["Hello! This is my first Python project."], speaker.spoken)
        self.assertTrue(any("clipboard temporarily unavailable" in message for message in messages))
