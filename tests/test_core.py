import unittest

try:
    from chat_reader.core import read_selected_text
except ImportError:
    read_selected_text = None

try:
    from chat_reader.core import make_hotkey_handler
except ImportError:
    make_hotkey_handler = None


class RecordingSpeaker:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


class ReadSelectedTextTests(unittest.TestCase):
    def test_failed_copy_never_reads_the_old_clipboard_command(self):
        speaker = RecordingSpeaker()
        was_read = read_selected_text(
            copy_selection=lambda: False,
            get_clipboard_text=lambda: r".\.venv\Scripts\python.exe -m chat_reader.app",
            speaker=speaker,
        )
        self.assertFalse(was_read)
        self.assertEqual([], speaker.spoken)

    def test_copies_selected_text_and_sends_it_to_the_speaker(self):
        """A missing copy or speak step would make this test fail."""
        self.assertIsNotNone(read_selected_text, "read_selected_text has not been implemented yet")
        copied = []
        speaker = RecordingSpeaker()

        was_read = read_selected_text(
            copy_selection=lambda: copied.append(True),
            get_clipboard_text=lambda: "Read this sentence.",
            speaker=speaker,
        )

        self.assertTrue(was_read)
        self.assertEqual([True], copied)
        self.assertEqual(["Read this sentence."], speaker.spoken)

    def test_does_not_speak_when_nothing_is_selected(self):
        """Removing the empty-selection check would make this test fail."""
        self.assertIsNotNone(read_selected_text, "read_selected_text has not been implemented yet")
        speaker = RecordingSpeaker()

        was_read = read_selected_text(
            copy_selection=lambda: None,
            get_clipboard_text=lambda: "   ",
            speaker=speaker,
        )

        self.assertFalse(was_read)
        self.assertEqual([], speaker.spoken)

    def test_hotkey_handler_reports_when_it_reads_the_selection(self):
        """Removing the successful-read feedback would make this test fail."""
        self.assertIsNotNone(make_hotkey_handler, "make_hotkey_handler has not been implemented yet")
        speaker = RecordingSpeaker()
        messages = []
        handler = make_hotkey_handler(
            copy_selection=lambda: None,
            get_clipboard_text=lambda: "A selected answer.",
            speaker=speaker,
            report_status=messages.append,
        )

        handler()

        self.assertEqual(["A selected answer."], speaker.spoken)
        self.assertEqual(["Reading selected text..."], messages)


if __name__ == "__main__":
    unittest.main()
