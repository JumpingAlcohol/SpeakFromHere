import unittest
from unittest.mock import patch

from chat_reader import app


class ParagraphHotkeyTests(unittest.TestCase):
    def test_paragraph_key_is_opt_in_and_uses_a_distinct_event(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), patch.object(app.keyboard, "Controller"), \
                    patch.object(app.win32gui, "RegisterHotKey") as register, \
                    patch.object(app.win32gui, "UnregisterHotKey"):
                desktop = app.WindowsDesktop(enable_paragraphs=enabled)
                try:
                    desktop.register()
                    keys = [call.args[3] for call in register.call_args_list]
                    self.assertEqual(enabled, ord("E") in keys)
                    with patch.object(app.win32gui, "PeekMessage", return_value=(
                            True, (0, app.win32con.WM_HOTKEY, 5, 0, 0, (0, 0)))):
                        self.assertEqual("paragraph" if enabled else None, desktop.next_hotkey())
                finally:
                    desktop.close()

    def test_conflict_names_alt_e_and_cleanup_releases_earlier_hotkeys(self):
        with patch.object(app.keyboard, "Controller"), \
                patch.object(app.win32gui, "RegisterHotKey", side_effect=[None] * 4 + [OSError("busy")]), \
                patch.object(app.win32gui, "UnregisterHotKey") as unregister:
            desktop = app.WindowsDesktop(enable_paragraphs=True)
            try:
                with self.assertRaisesRegex(RuntimeError, "Alt \\+ E"):
                    desktop.register()
            finally:
                desktop.close()
            self.assertEqual([1, 2, 3, 4], [call.args[1] for call in unregister.call_args_list])

    def test_pointer_position_uses_the_physical_coordinate_boundary(self):
        with patch.object(app.keyboard, "Controller"), \
                patch("chat_reader.windows_context.physical_cursor_position", return_value=(-200, 500)):
            self.assertEqual((-200, 500), app.WindowsDesktop().pointer_position())
