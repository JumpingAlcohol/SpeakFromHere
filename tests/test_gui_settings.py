import inspect
import json
from pathlib import Path
import tempfile
import unittest
from chat_reader.settings import Settings, SettingsError, save_settings, load_settings


class GuiSettingsTests(unittest.TestCase):
    def test_schema_one_loads_without_rewriting_and_upgrade_preserves_controls(self):
        self.assertIn("language", inspect.signature(Settings).parameters)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            content = '{"schema_version":1,"rate":-2,"hotkeys":{"pause":"Alt+J","stop":"Alt+K","exit":"Alt+Shift+L"}}'
            path.write_text(content, encoding="utf-8")
            value = load_settings(path)
            self.assertEqual("en", value.language)
            self.assertEqual(content, path.read_text(encoding="utf-8"))
            save_settings(path, value)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(2, data["schema_version"])
            self.assertEqual(-2, data["rate"])
            self.assertEqual("Alt + J", data["hotkeys"]["pause"])

    def test_language_persists_and_unsupported_languages_are_rejected(self):
        self.assertIn("language", inspect.signature(Settings).parameters)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            save_settings(path, Settings(language="zh-CN"))
            self.assertEqual("zh-CN", load_settings(path).language)
            for language in ("other", None, 3):
                with self.subTest(language=language), self.assertRaises(SettingsError):
                    Settings(language=language)
