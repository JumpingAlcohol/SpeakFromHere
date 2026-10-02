"""Player commands and preferences: real SAPI boundary fake, real temp JSON."""
import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chat_reader.app import WindowsSpeaker
from chat_reader.settings import Settings, load_settings, save_settings
from chat_reader.core import run_reader_loop
from test_app import RecordingEngine
from test_runtime import Clock, Desktop

if importlib.util.find_spec("chat_reader.player"):
    from chat_reader import player
else:
    player = None


class PlayerTests(unittest.TestCase):
    def test_play_button_pauses_resumes_and_replays_without_recapturing(self):
        self.assertTrue(hasattr(WindowsSpeaker, "play_pause"), "Player control is missing")
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        self.assertEqual("idle", speaker.play_pause())
        speaker.speak("Synthetic passage.")
        self.assertEqual("paused", speaker.play_pause())
        self.assertEqual("resumed", speaker.play_pause())
        speaker.stop()
        self.assertEqual("replaying", speaker.play_pause())
        self.assertEqual([("Synthetic passage.", 19), ("pause",), ("resume",), ("", 3),
                          ("Synthetic passage.", 19)], engine.actions)

    def test_play_event_cancels_pending_capture_and_replays_only_last_spoken_text(self):
        self.assertTrue(hasattr(WindowsSpeaker, "play_pause"), "Player control is missing")
        from test_paragraph_runtime import Capture
        clock = Clock()
        desktop = Desktop(clock)
        desktop.events = iter(["read", "stop", "play", "quit"])
        speaker = WindowsSpeaker(RecordingEngine())
        capture = Capture()
        run_reader_loop(desktop, speaker, paragraph_reader=capture, report=lambda _: None,
                        clock=clock.monotonic, sleep=clock.sleep)
        spoken = [text for text, *rest in speaker.engine.actions if text and text not in {"pause", "resume"}]
        self.assertEqual(["Hello! This is my first Python project."] * 2, spoken)
        self.assertEqual(8, desktop.sequence, "Replay must not copy again")
        self.assertGreaterEqual(capture.cancellations, 3)

    def test_rate_change_preserves_pause_and_does_not_respeak_current_passage(self):
        self.assertTrue(hasattr(WindowsSpeaker, "set_rate"), "Player rate control is missing")
        engine = RecordingEngine()
        speaker = WindowsSpeaker(engine)
        speaker.speak("Original.")
        speaker.toggle_pause()
        speaker.set_rate(4)
        self.assertEqual(4, engine.Rate)
        self.assertTrue(speaker.paused)
        self.assertEqual([("Original.", 19), ("pause",)], engine.actions)
        with self.assertRaises(ValueError):
            speaker.set_rate(11)
        self.assertEqual(4, engine.Rate)

    def test_window_position_uses_work_area_and_supports_negative_monitor_coordinates(self):
        self.assertIsNotNone(player, "Player model is missing")
        self.assertEqual((1498, 818), player.bottom_right((0, 0, 1920, 1040), 406, 206))
        self.assertEqual((-422, 818), player.bottom_right((-1920, 0, 0, 1040), 406, 206))

    def test_gui_preferences_merge_latest_controls_and_survive_restart(self):
        self.assertIsNotNone(player, "Player model is missing")
        self.assertIn("language", inspect.signature(Settings).parameters)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            speaker = WindowsSpeaker(RecordingEngine())
            model = player.PlayerPreferences(path, Settings(), speaker)
            save_settings(path, Settings(hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
            model.update(rate=2, language="zh-CN")
            value = load_settings(path)
            self.assertEqual((2, "zh-CN", "Alt + J"), (value.rate, value.language, value.hotkeys["pause"]))
            self.assertEqual(2, speaker.engine.Rate)
            self.assertEqual([], speaker.engine.actions, "Changing preferences must not start speech")

    def test_invalid_file_is_not_overwritten_by_a_gui_rate_change(self):
        self.assertIsNotNone(player, "Player model is missing")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            speaker = WindowsSpeaker(RecordingEngine())
            model = player.PlayerPreferences(path, Settings(), speaker)
            with self.assertRaises(ValueError):
                model.update(rate=2)
            self.assertEqual("{broken", path.read_text(encoding="utf-8"))
            self.assertEqual(0, speaker.engine.Rate)

    def test_bilingual_playback_labels_follow_actual_voice_state(self):
        self.assertIsNotNone(player, "Player model is missing")
        speaker = WindowsSpeaker(RecordingEngine())
        self.assertEqual(("Play", False), player.play_button(speaker, "en"))
        speaker.speak("Synthetic.")
        self.assertEqual(("Pause", True), player.play_button(speaker, "en"))
        speaker.toggle_pause()
        self.assertEqual(("继续", True), player.play_button(speaker, "zh-CN"))
        speaker.stop()
        self.assertEqual(("播放", True), player.play_button(speaker, "zh-CN"))

    def test_cli_rate_update_preserves_saved_gui_language(self):
        self.assertIn("language", inspect.signature(Settings).parameters)
        from chat_reader import app
        import io
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            save_settings(path, Settings(language="zh-CN"))
            with patch("sys.stdout", new=io.StringIO()):
                app.run(["--settings-file", str(path), "--set-rate", "3"])
            self.assertEqual("zh-CN", load_settings(path).language)

    def test_failed_gui_save_restores_voice_rate_and_explicit_reset_can_recover_bad_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            speaker = WindowsSpeaker(RecordingEngine(), rate=2)
            save_settings(path, Settings(rate=2))
            model = player.PlayerPreferences(path, Settings(rate=2), speaker)
            with patch("chat_reader.player.save_settings", side_effect=OSError("read only")):
                with self.assertRaises(OSError):
                    model.update(rate=3)
            self.assertEqual(2, speaker.engine.Rate)
            self.assertEqual(2, load_settings(path).rate)
            self.assertTrue(hasattr(model, "reset"), "Explicit GUI reset is missing")
            path.write_text("{broken", encoding="utf-8")
            model.reset()
            self.assertEqual((0, "en"), (load_settings(path).rate, load_settings(path).language))
