import unittest
from types import SimpleNamespace

try:
    from chat_reader.app import WindowsSpeaker
except ImportError:
    WindowsSpeaker = None


class RecordingEngine:
    def __init__(self):
        self.actions = []
        self.Volume = 100
        self.Status = SimpleNamespace(RunningState=1)

    def Speak(self, text, flags):
        self.actions.append((text, flags))
        self.Status.RunningState = 2 if text else 1

    def SpeakStream(self, stream, flags):
        self.actions.append(("stream", flags))
        self.Status.RunningState = 2

    def Pause(self):
        self.actions.append(("pause",))

    def Resume(self):
        self.actions.append(("resume",))

    def WaitUntilDone(self, timeout):
        if timeout != 0:
            raise AssertionError("Checking speech state must not block hotkey handling")
        return self.Status.RunningState == 1


class WindowsSpeakerTests(unittest.TestCase):
    def test_pause_then_resume_preserves_the_current_utterance(self):
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        speaker.speak("Keep my reading position.")
        self.assertTrue(hasattr(speaker, "toggle_pause"), "Pause control is missing")
        self.assertEqual("paused", speaker.toggle_pause())
        self.assertEqual("resumed", speaker.toggle_pause())
        self.assertEqual(
            [("Keep my reading position.", 19), ("pause",), ("resume",)],
            engine.actions,
        )

    def test_pause_while_idle_does_not_block_the_next_utterance(self):
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        self.assertTrue(hasattr(speaker, "toggle_pause"), "Pause control is missing")
        self.assertEqual("idle", speaker.toggle_pause())
        speaker.speak("The next selection.")
        self.assertEqual([("The next selection.", 19)], engine.actions)

    def test_new_selection_clears_pause_before_replacing_the_old_speech(self):
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        speaker.speak("Old selection.")
        self.assertTrue(hasattr(speaker, "toggle_pause"), "Pause control is missing")
        speaker.toggle_pause()
        speaker.speak("New selection.")
        self.assertEqual(
            [("Old selection.", 19), ("pause",), ("resume",), ("New selection.", 19)],
            engine.actions,
        )
        self.assertEqual("paused", speaker.toggle_pause())

    def test_stop_while_paused_does_not_leave_the_next_selection_paused(self):
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        speaker.speak("First selection.")
        self.assertTrue(hasattr(speaker, "toggle_pause"), "Pause control is missing")
        speaker.toggle_pause()
        speaker.stop()
        speaker.speak("Another selection.")
        self.assertEqual(
            [("First selection.", 19), ("pause",), ("resume",), ("", 3),
             ("Another selection.", 19)], engine.actions,
        )

    def test_two_selections_can_be_spoken_without_blocking_the_event_loop(self):
        """The external speech boundary must accept repeated asynchronous requests."""
        self.assertIsNotNone(WindowsSpeaker, "WindowsSpeaker has not been implemented yet")
        engine = RecordingEngine()

        speaker = WindowsSpeaker(engine)
        speaker.speak("First selection.")
        speaker.speak("Second selection.")

        self.assertEqual(
            [("First selection.", 19), ("Second selection.", 19)],
            engine.actions,
        )

    def test_shutdown_cancels_any_remaining_speech(self):
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        self.assertTrue(hasattr(speaker, "stop"), "Exit must also stop the voice")
        speaker.stop()
        self.assertEqual([("", 3)], engine.actions)


if __name__ == "__main__":
    unittest.main()
