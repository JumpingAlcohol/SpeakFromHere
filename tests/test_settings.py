"""Settings contracts: real temporary files, never the user's preferences."""

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

if importlib.util.find_spec("chat_reader.settings"):
    from chat_reader import settings
else:
    settings = None


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(settings, "Persisted reading settings are missing")
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "nested" / "settings.json"

    def test_missing_file_loads_defaults_without_creating_a_file(self):
        value = settings.load_settings(self.path)
        self.assertEqual(0, value.rate)
        self.assertEqual({"pause": "Alt + P", "stop": "Alt + X", "exit": "Alt + Shift + Q"},
                         value.hotkeys)
        self.assertFalse(self.path.exists())

    def test_saved_settings_survive_an_independent_reload(self):
        value = settings.Settings(rate=3, hotkeys={"pause": "Alt+Shift+J", "stop": "Alt+K", "exit": "Alt+Q"})
        settings.save_settings(self.path, value)
        loaded = settings.load_settings(self.path)
        self.assertEqual(3, loaded.rate)
        self.assertEqual("Alt + Shift + J", loaded.hotkeys["pause"])
        document = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual({"schema_version": 2, "rate": 3, "language": "en",
                          "hotkeys": {"pause": "Alt + Shift + J", "stop": "Alt + K", "exit": "Alt + Q"}}, document)

    def test_bad_rates_are_rejected_before_any_file_is_written(self):
        for rate in (-11, 11, True, 1.5, "3", None):
            with self.subTest(rate=rate), self.assertRaises(settings.SettingsError):
                settings.save_settings(self.path, settings.Settings(rate=rate))
        self.assertFalse(self.path.exists())
        for rate in (-10, 0, 10):
            settings.save_settings(self.path, settings.Settings(rate=rate))
            self.assertEqual(rate, settings.load_settings(self.path).rate)

    def test_reserved_duplicate_and_unsupported_bindings_are_rejected(self):
        for chord in ("Alt+S", "Alt+E", "alt+x", "Ctrl+J", "J", "Alt+1", "Alt+Shift+Shift+J", "Alt+é", ""):
            with self.subTest(chord=chord), self.assertRaises(settings.SettingsError):
                settings.Settings(hotkeys={"pause": chord, "stop": "Alt+X", "exit": "Alt+Shift+Q"})
        with self.assertRaises(settings.SettingsError):
            settings.Settings(hotkeys={"read": "Alt+J"})

    def test_chord_normalization_gives_exact_windows_modifiers(self):
        # Independent Windows contract: MOD_ALT=1, MOD_SHIFT=4 (not MOD_CONTROL=2).
        self.assertEqual((1, ord("J")), settings.parse_hotkey(" alt + j "))
        self.assertEqual((5, ord("Q")), settings.parse_hotkey("Alt+Shift+q"))

    def test_bad_documents_are_preserved_and_never_silently_migrated(self):
        self.path.parent.mkdir()
        for content in ('{broken', '[]', '{"schema_version": 0}', '{"schema_version": true}',
                        '{"schema_version": 1, "rate": 99}', '{"schema_version": 1, "voice": "unknown"}',
                        '{"schema_version":1,"hotkeys":{"pause":"Alt+S"}}'):
            with self.subTest(content=content):
                self.path.write_text(content, encoding="utf-8")
                with self.assertRaises(settings.SettingsError):
                    settings.load_settings(self.path)
                self.assertEqual(content, self.path.read_text(encoding="utf-8"))

    def test_failed_atomic_replace_preserves_previous_settings_and_removes_temp_file(self):
        settings.save_settings(self.path, settings.Settings(rate=2))
        before = self.path.read_bytes()
        with patch.object(settings.os, "replace", side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError):
                settings.save_settings(self.path, settings.Settings(rate=4))
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(["settings.json"], [p.name for p in self.path.parent.iterdir()])

    def test_default_path_is_local_user_data_not_the_executable_folder(self):
        with patch.dict(os.environ, {"LOCALAPPDATA": self.folder.name}):
            self.assertEqual(Path(self.folder.name) / "AIChatReader" / "settings.json", settings.settings_path())

    def test_invalid_encoding_and_duplicate_json_keys_are_not_silently_accepted(self):
        self.path.parent.mkdir()
        for content in (b'\xff', b'{"schema_version":1,"rate":2,"rate":3}'):
            with self.subTest(content=content):
                self.path.write_bytes(content)
                with self.assertRaises(ValueError) as raised:
                    settings.load_settings(self.path)
                self.assertIsInstance(raised.exception, settings.SettingsError)
                self.assertEqual(content, self.path.read_bytes())
