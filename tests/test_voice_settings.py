"""Voice preferences: real local JSON and migration, never a user profile."""
import inspect
import json
from pathlib import Path
import tempfile
import unittest

from chat_reader.settings import Settings, SettingsError, load_settings, save_settings


class VoiceSettingsTests(unittest.TestCase):
    def setUp(self):
        self.assertIn('voice_id', inspect.signature(Settings).parameters,
                      'No persisted voice selection')
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'settings.json'

    def test_voice_id_survives_save_without_losing_other_preferences(self):
        """Dropping voice_id from serialization loses selection on restart."""
        value = Settings(rate=3, language='zh-CN', voice_id='local-token-B')
        save_settings(self.path, value)
        loaded = load_settings(self.path)
        self.assertEqual(('local-token-B', 3, 'zh-CN'),
                         (loaded.voice_id, loaded.rate, loaded.language))
        self.assertEqual(3, json.loads(self.path.read_text())['schema_version'])

    def test_old_schemas_load_default_voice_without_implicit_write(self):
        """Reading old settings must not migrate or discard existing choices."""
        for version, language in ((1, 'en'), (2, 'zh-CN')):
            document = {'schema_version': version, 'rate': -2}
            if version == 2:
                document['language'] = language
            original = json.dumps(document)
            self.path.write_text(original)
            value = load_settings(self.path)
            self.assertEqual(('', -2, language), (value.voice_id, value.rate, value.language))
            self.assertEqual(original, self.path.read_text())
            save_settings(self.path, value)
            self.assertEqual(3, json.loads(self.path.read_text())['schema_version'])

    def test_malformed_voice_ids_are_not_saved_or_loaded(self):
        """Nontext/control/oversize IDs must not be silently accepted."""
        for token in (None, 3, True, [], ' ', 'a\x00b', 'a\nb', 'x' * 1025):
            with self.subTest(token=repr(token)[:30]):
                with self.assertRaises(SettingsError):
                    Settings(voice_id=token)
                original = json.dumps({'schema_version': 3, 'voice_id': token})
                self.path.write_text(original)
                with self.assertRaises(SettingsError):
                    load_settings(self.path)
                self.assertEqual(original, self.path.read_text())

    def test_uninstalled_but_well_formed_id_is_preserved_for_runtime_warning(self):
        """Configuration loading must not need SAPI or erase a removed voice."""
        save_settings(self.path, Settings(voice_id='removed-token'))
        self.assertEqual('removed-token', load_settings(self.path).voice_id)

    def test_voice_field_in_old_schema_is_rejected_not_silently_upgraded(self):
        for version in (1, 2):
            original = json.dumps({'schema_version': version, 'voice_id': 'local-token'})
            self.path.write_text(original)
            with self.assertRaises(SettingsError):
                load_settings(self.path)
            self.assertEqual(original, self.path.read_text())
