"""CLI, SAPI and hotkey boundaries with test-owned settings files."""

from contextlib import redirect_stdout, redirect_stderr
import io
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chat_reader import app
from chat_reader.settings import Settings, load_settings, save_settings
from chat_reader.core import run_reader_loop
from test_app import RecordingEngine
from test_runtime import Clock, Desktop, Speaker


class SettingsRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "settings.json"

    def command(self, argv):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), \
                patch.object(app.win32com.client, "Dispatch", side_effect=AssertionError("Settings command started speech")), \
                patch.object(app.keyboard, "Controller", side_effect=AssertionError("Settings command started desktop")):
            try:
                app.run(["--settings-file", str(self.path), *argv])
            except SystemExit as error:
                return error.code, output.getvalue()
        return 0, output.getvalue()

    def test_cli_saves_rate_and_control_binding_without_starting_reader(self):
        code, output = self.command(["--set-rate", "3", "--set-hotkey", "pause=Alt+J", "--show-settings"])
        self.assertEqual(0, code, output)
        value = load_settings(self.path)
        self.assertEqual(3, value.rate)
        self.assertEqual("Alt + J", value.hotkeys["pause"])
        code, output = self.command(["--show-settings"])
        self.assertEqual(0, code, output)
        self.assertIn("Rate: 3", output)
        self.assertIn("Alt + J", output)
        self.assertIn("Alt + S", output)

    def test_conflicting_or_out_of_range_cli_change_does_not_modify_existing_file(self):
        code, output = self.command(["--show-settings"])
        self.assertEqual(0, code, "Settings commands are missing: " + output)
        save_settings(self.path, Settings(rate=2))
        before = self.path.read_bytes()
        for argv in (["--set-rate", "11"], ["--set-hotkey", "pause=Alt+S"],
                     ["--set-hotkey", "pause=Alt+X"], ["--set-hotkey", "read=Alt+J"],
                     ["--set-hotkey", "pause"], ["--set-hotkey", "pause=Alt+J", "--set-hotkey", "pause=Alt+K"]):
            with self.subTest(argv=argv):
                code, output = self.command(argv)
                self.assertNotEqual(0, code, output)
                self.assertEqual(before, self.path.read_bytes())

    def test_damaged_file_can_only_be_overwritten_by_explicit_reset(self):
        self.path.write_text("{broken", encoding="utf-8")
        code, output = self.command(["--set-rate", "3"])
        self.assertNotEqual(0, code, output)
        self.assertEqual("{broken", self.path.read_text(encoding="utf-8"))
        code, output = self.command(["--reset-settings"])
        self.assertEqual(0, code, output)
        self.assertEqual(0, load_settings(self.path).rate)

    def test_saved_settings_reach_sapi_and_source_still_does_not_register_alt_e(self):
        self.assertIn("rate", inspect.signature(app.WindowsSpeaker).parameters)
        save_settings(self.path, Settings(rate=-2, hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
        engine = RecordingEngine()
        with redirect_stdout(io.StringIO()), patch.object(app.keyboard, "Controller"), \
                patch.object(app.win32com.client, "Dispatch", return_value=engine), \
                patch.object(app.win32gui, "RegisterHotKey") as register, \
                patch.object(app.win32gui, "UnregisterHotKey") as unregister, \
                patch.object(app.win32gui, "PeekMessage", return_value=(True, (0, app.win32con.WM_QUIT, 0, 0, 0, (0, 0)))):
            app.run(["--settings-file", str(self.path)])
        self.assertEqual(-2, getattr(engine, "Rate", None))
        self.assertEqual([(1, 0x4001, 83), (2, 0x4005, 76), (3, 0x4001, 74), (4, 0x4001, 75)],
                         [call.args[1:] for call in register.call_args_list])
        self.assertEqual([1, 2, 3, 4], [call.args[1] for call in unregister.call_args_list])

    def test_corrupt_configuration_warns_and_starts_safe_defaults_without_overwriting(self):
        code, output = self.command(["--show-settings"])
        self.assertEqual(0, code, "Settings commands are missing: " + output)
        self.path.write_text("{broken", encoding="utf-8")
        output = io.StringIO()
        engine = RecordingEngine()
        with redirect_stdout(output), patch.object(app.keyboard, "Controller"), \
                patch.object(app.win32com.client, "Dispatch", return_value=engine), \
                patch.object(app.win32gui, "RegisterHotKey") as register, \
                patch.object(app.win32gui, "UnregisterHotKey"), \
                patch.object(app.win32gui, "PeekMessage", return_value=(True, (0, app.win32con.WM_QUIT, 0, 0, 0, (0, 0)))):
            app.run(["--settings-file", str(self.path)])
        self.assertIn("default", output.getvalue().lower())
        self.assertEqual(0, getattr(engine, "Rate", None))
        self.assertEqual(83, register.call_args_list[0].args[3])
        self.assertEqual("{broken", self.path.read_text(encoding="utf-8"))

    def test_speaker_applies_default_and_configured_rate_without_changing_async_speech(self):
        self.assertIn("rate", inspect.signature(app.WindowsSpeaker).parameters)
        for rate in (0, -10, 10):
            engine = RecordingEngine()
            speaker = app.WindowsSpeaker(engine, rate=rate)
            speaker.speak("Synthetic text.")
            self.assertEqual(rate, engine.Rate)
            self.assertEqual([("Synthetic text.", 19)], engine.actions)

    def test_custom_conflict_rolls_back_all_registered_hotkeys_and_names_actual_binding(self):
        self.assertIn("settings", inspect.signature(app.WindowsDesktop).parameters)
        with patch.object(app.keyboard, "Controller"), \
                patch.object(app.win32gui, "RegisterHotKey", side_effect=[None, None, OSError("busy")]), \
                patch.object(app.win32gui, "UnregisterHotKey") as unregister:
            desktop = app.WindowsDesktop(settings=Settings(hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
            with self.assertRaisesRegex(RuntimeError, "Alt \\+ J"):
                desktop.register()
            self.assertEqual([], desktop.registered)
            desktop.close()
            self.assertEqual([1, 2], [call.args[1] for call in unregister.call_args_list])

    def test_effective_control_keys_appear_in_startup_and_pause_feedback(self):
        self.assertIn("settings", inspect.signature(run_reader_loop).parameters)
        clock = Clock()
        desktop = Desktop(clock)
        desktop.events = iter(["read", "pause", "quit"])
        messages = []
        run_reader_loop(desktop, Speaker(), report=messages.append, clock=clock.monotonic,
                        sleep=clock.sleep, settings=Settings(rate=2, hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
        self.assertTrue(any("Alt + J" in message and "resume" in message for message in messages))
        self.assertTrue(any("Alt + K" in message for message in messages))
        self.assertTrue(any("Alt + Shift + L" in message for message in messages))
        self.assertTrue(any("Rate: 2" in message for message in messages))
