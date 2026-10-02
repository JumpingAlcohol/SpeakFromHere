"""Opt-in checks of this application's own Tk window, never private apps."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
import win32con
import win32gui

from chat_reader.app import WindowsDesktop, WindowsSpeaker
from chat_reader.player import PlayerPreferences
from chat_reader.settings import Settings, load_settings
from test_app import RecordingEngine

if importlib.util.find_spec("chat_reader.gui"):
    from chat_reader import gui
else:
    gui = None


@unittest.skipUnless(os.environ.get("CHAT_READER_GUI_TESTS") == "1", "Opt-in own GUI window tests")
class GuiWindowTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gui, "Floating player is missing")
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "settings.json"
        self.speaker = WindowsSpeaker(RecordingEngine())
        self.preferences = PlayerPreferences(self.path, Settings(), self.speaker)
        self.window = gui.PlayerWindow(self.preferences, enable_paragraphs=True)
        self.desktop = gui.GuiDesktop(self.window, WindowsDesktop(enable_paragraphs=True, hwnd=self.window.hwnd))
        self.addCleanup(self.desktop.close)

    def test_visible_player_is_topmost_and_does_not_activate_or_cover_taskbar(self):
        before = win32gui.GetForegroundWindow()
        self.desktop.register()
        self.window.root.update()
        self.assertEqual(before, win32gui.GetForegroundWindow())
        styles = win32gui.GetWindowLong(self.window.hwnd, win32con.GWL_EXSTYLE)
        self.assertTrue(styles & 0x08000000, "Player must not activate on click")
        self.assertTrue(styles & win32con.WS_EX_TOPMOST)
        left, top, right, bottom = win32gui.GetWindowRect(self.window.hwnd)
        work_left, work_top, work_right, work_bottom = self.window.work_area
        self.assertGreaterEqual(left, work_left)
        self.assertGreaterEqual(top, work_top)
        self.assertLessEqual(right, work_right)
        self.assertLessEqual(bottom, work_bottom)
        self.assertEqual(3, win32gui.SendMessage(self.window.hwnd, win32con.WM_MOUSEACTIVATE, 0, 0))

    def test_real_window_hotkeys_survive_tk_message_dispatch_and_cleanup(self):
        self.desktop.register()
        win32gui.PostMessage(self.window.hwnd, win32con.WM_HOTKEY, 3, 0)
        self.assertEqual("pause", self.desktop.next_hotkey())
        self.desktop.close()
        win32gui.RegisterHotKey(None, 99, win32con.MOD_ALT | 0x4000, ord("S"))
        win32gui.UnregisterHotKey(None, 99)
        self.assertFalse(win32gui.IsWindow(self.window.hwnd))

    def test_buttons_queue_controls_and_rate_language_preferences_persist(self):
        self.speaker.speak("Synthetic GUI test.")
        self.window.refresh()
        self.window.buttons["play"].invoke()
        self.assertEqual("play", self.desktop.next_hotkey())
        self.window.buttons["stop"].invoke()
        self.assertEqual("stop", self.desktop.next_hotkey())
        self.window.buttons["faster"].invoke()
        self.window.buttons["language"].invoke()
        value = load_settings(self.path)
        self.assertEqual((1, "zh-CN"), (value.rate, value.language))
        self.assertEqual(1, self.speaker.engine.Rate)
        self.assertIn("暂停", self.window.buttons["play"].cget("text"))
        self.assertEqual([("Synthetic GUI test.", 19)], self.speaker.engine.actions)

    def test_hide_and_tray_restore_keep_reader_alive_and_exit_button_queues_quit(self):
        self.desktop.register()
        self.assertTrue(self.window.tray.added)
        self.window.buttons["hide"].invoke()
        self.assertEqual("withdrawn", self.window.root.state())
        win32gui.PostMessage(self.window.tray.hwnd, self.window.tray.callback_message, 0, win32con.WM_LBUTTONUP)
        self.desktop.next_hotkey()
        self.assertEqual("normal", self.window.root.state())
        self.window.buttons["exit"].invoke()
        self.assertEqual("quit", self.desktop.next_hotkey())

    def test_settings_dialog_saves_controls_but_keeps_current_bindings_until_restart(self):
        dialog = self.window.open_settings()
        dialog.variables["pause"].set("Alt+J")
        dialog.save()
        self.assertEqual("Alt + J", load_settings(self.path).hotkeys["pause"])
        self.assertEqual("Alt + P", self.desktop.desktop.settings.hotkeys["pause"])

    def test_status_tracks_speech_after_pre_speech_preview_and_after_completion(self):
        # core emits its preview before invoking SAPI; that must not leave the
        # player permanently showing Ready while the voice is already reading.
        self.window.report("Reading: Synthetic GUI status.")
        self.speaker.speak("Synthetic GUI status.")
        self.window.refresh()
        self.assertIn("Reading", self.window.status.cget("text"))
        self.speaker.engine.Status.RunningState = 1
        self.window.refresh()
        self.assertIn("Ready", self.window.status.cget("text"))

    def test_error_details_are_complete_selectable_and_do_not_copy_or_save_chat(self):
        """A two-line preview conceals the failure stage needed to diagnose refusal."""
        import ctypes
        sequence = ctypes.windll.user32.GetClipboardSequenceNumber()
        message = ("Could not read this paragraph: The pointed application's Windows "
                   "package identity could not be verified. GetPackageFamilyName failed "
                   "(Windows error 5). Use Alt + S for selected text.")
        self.window.report(message)
        self.assertIn("details", self.window.buttons, "No way to expand the clipped error")
        self.window.buttons["details"].invoke()
        self.window.root.update()
        dialog = self.window.details_dialog
        self.assertEqual(message, dialog.content.get("1.0", "end-1c"))
        self.assertEqual("disabled", dialog.content.cget("state"), "Details must be read-only")
        dialog.content.tag_add("sel", "1.0", "end-1c")
        self.assertEqual(message, dialog.content.get("sel.first", "sel.last"))
        self.assertEqual(sequence, ctypes.windll.user32.GetClipboardSequenceNumber())
        self.assertFalse(self.path.exists())
        dialog.close()
        self.assertIsNone(self.window.details_dialog)

    def test_skip_notice_survives_pause_language_change_and_expands_without_storing_chat(self):
        """A cleared/truncated notice makes skipped content undiscoverable during listening."""
        self.window.report("Reading paragraph: Synthetic body.")
        self.speaker.speak("Synthetic body.")
        self.window.report('Skipped content: [{"kind":"code","ordinal":1,"before_start":true},{"kind":"table","ordinal":2,"before_start":false}]')
        self.assertTrue(hasattr(self.window, "skip_notice"), "No visible skipped-content notice")
        self.assertIn("2", self.window.skip_notice.cget("text"))
        self.assertEqual("normal", self.window.buttons["details"].cget("state"))
        self.window.report("Checking paragraph...")
        self.assertEqual("", self.window.skip_notice.cget("text"))
        self.window.report("Replaying last text.")
        self.assertIn("2", self.window.skip_notice.cget("text"), "Canceled capture lost the replay's omissions")
        self.speaker.toggle_pause()
        self.window.report("Speech paused.")
        self.window.change_language()
        self.assertIn("跳过", self.window.skip_notice.cget("text"))
        self.window.buttons["details"].invoke()
        self.window.root.update()
        content = self.window.details_dialog.content.get("1.0", "end-1c")
        self.assertIn("Table", content)
        self.assertIn("before", content)
        self.assertIn("2", content)
        self.assertNotIn("Synthetic body", content, "Skip diagnostics must not include private prose")
        self.window.details_dialog.close()
        self.window.report("Reading: New selection.")
        self.assertEqual("", self.window.skip_notice.cget("text"))
        self.assertEqual("disabled", self.window.buttons["details"].cget("state"))
