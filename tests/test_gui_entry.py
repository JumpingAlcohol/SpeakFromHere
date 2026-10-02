"""GUI entry routing must leave capture workers and CLI commands isolated."""
import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from chat_reader import app


class GuiEntryTests(unittest.TestCase):
    def test_gui_launch_passes_preferences_without_starting_console_reader(self):
        with tempfile.TemporaryDirectory() as folder, patch("chat_reader.gui.run_gui") as gui, \
                patch.object(app, "WindowsDesktop") as desktop, patch.object(app.win32com.client, "Dispatch") as voice:
            path = str(Path(folder) / "settings.json")
            app.run(["--gui", "--settings-file", path])
            self.assertEqual(path, gui.call_args.args[0])
            self.assertEqual("en", gui.call_args.args[1].language)
            self.assertTrue(gui.call_args.kwargs["enable_paragraphs"])
            desktop.assert_not_called()
            voice.assert_not_called()

    def test_gui_invalid_file_is_preserved_and_warning_reaches_the_window(self):
        with tempfile.TemporaryDirectory() as folder, patch("chat_reader.gui.run_gui") as gui:
            path = Path(folder) / "settings.json"
            path.write_text("{broken", encoding="utf-8")
            app.run(["--gui", "--settings-file", str(path)])
            self.assertIn("Using defaults", gui.call_args.kwargs["warning"])
            self.assertEqual("{broken", path.read_text(encoding="utf-8"))

    def test_worker_route_precedes_gui_and_settings(self):
        with patch("chat_reader.paragraph_worker.main", return_value=1) as worker, \
                patch("chat_reader.gui.run_gui") as gui, patch.object(app, "load_settings") as settings:
            with self.assertRaises(SystemExit) as error:
                app.run(["--gui", "--paragraph-worker", "41", "52"])
            self.assertEqual(1, error.exception.code)
            worker.assert_called_once_with(["41", "52"])
            gui.assert_not_called()
            settings.assert_not_called()

    def test_gui_preferences_command_does_not_open_a_window(self):
        with tempfile.TemporaryDirectory() as folder, patch("chat_reader.gui.run_gui") as gui, \
                patch("sys.stdout", new_callable=io.StringIO) as output:
            app.run(["--gui", "--show-settings", "--settings-file", str(Path(folder) / "settings.json")])
            gui.assert_not_called()
            self.assertIn("Rate: 0", output.getvalue())

    def test_windowed_entry_defaults_to_gui_but_keeps_worker_arguments(self):
        from chat_reader import gui_entry
        with patch.object(gui_entry, "run") as run, patch.object(gui_entry, "restore_redirected_streams") as restore:
            gui_entry.main(["--paragraph-worker", "41", "52"])
            restore.assert_called_once()
            run.assert_called_once_with(["--gui", "--paragraph-worker", "41", "52"])

    def test_redirected_stream_wrapper_uses_utf8_and_is_readable_by_parent(self):
        from chat_reader.gui_entry import wrap_output_handle
        import os
        import msvcrt
        read_fd, write_fd = os.pipe()
        stream = wrap_output_handle(msvcrt.get_osfhandle(write_fd))
        try:
            stream.write("你好 from worker\n")
            stream.flush()
            self.assertEqual("你好 from worker\n", os.read(read_fd, 200).decode("utf-8"))
        finally:
            stream.close()
            os.close(read_fd)
            # The wrapper owns a duplicate; the original fd remains valid.
            os.close(write_fd)
