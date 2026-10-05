"""Select stable local token IDs, not duplicate names or machine-specific indices."""
import inspect
import unittest
from unittest.mock import patch

from chat_reader import app
from voice_fixtures import VoiceEngine


class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = VoiceEngine()
        self.speaker = app.WindowsSpeaker(self.engine, rate=2)

    def test_catalog_preserves_ids_and_language_even_for_duplicate_names(self):
        """Name-based lookup would conflate two different voices."""
        self.assertTrue(hasattr(self.speaker, 'voice_options'), 'No voice catalog')
        options = self.speaker.voice_options()
        self.assertEqual(['token-A', 'token-B'], [item.id for item in options])
        self.assertEqual(['zh_CN', 'en_US, en_GB'], [item.language for item in options])
        self.assertEqual([], self.engine.actions, 'Listing must be silent')

    def test_selection_and_default_reset_change_only_this_voice_not_reading_state(self):
        self.assertTrue(hasattr(self.speaker, 'set_voice'), 'No voice selection')
        self.speaker.last_text = 'Previous reply.'
        self.speaker.set_voice('TOKEN-b')
        self.assertEqual('token-B', self.engine.Voice.Id)
        self.assertEqual(2, self.engine.Rate)
        self.assertEqual('Previous reply.', self.speaker.last_text)
        self.speaker.set_voice('')
        self.assertEqual('token-A', self.engine.Voice.Id)
        self.assertEqual([], self.engine.actions)

    def test_active_or_paused_speech_refuses_switch_without_cancelling_it(self):
        self.assertTrue(hasattr(self.speaker, 'set_voice'), 'No busy voice guard')
        self.speaker.speak('Preserve current reply.')
        for paused in (False, True):
            if paused:
                self.speaker.toggle_pause()
            before = list(self.engine.actions)
            with self.assertRaisesRegex(ValueError, 'Stop'):
                self.speaker.set_voice('token-B')
            self.assertEqual('token-A', self.engine.Voice.Id)
            self.assertEqual(before, self.engine.actions)

    def test_missing_voice_is_refused_before_changing_active_voice(self):
        self.assertTrue(hasattr(self.speaker, 'set_voice'), 'No missing voice guard')
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            self.speaker.set_voice('missing')
        self.assertEqual('token-A', self.engine.Voice.Id)

    def test_saved_missing_voice_warns_and_uses_default_at_startup(self):
        self.assertIn('voice_id', inspect.signature(app.create_windows_speaker).parameters,
                      'Factory ignores saved voice')
        with patch('chat_reader.windows_audio.create_voice', return_value=self.engine):
            speaker = app.create_windows_speaker(rate=3, voice_id='missing')
        self.assertEqual('token-A', speaker.engine.Voice.Id)
        self.assertIn('unavailable', speaker.voice_warning)
        self.assertEqual('', speaker.voice_id)
        self.assertEqual([], self.engine.actions)

    def test_preview_keeps_replay_text_and_refuses_interrupting_a_reply(self):
        self.assertTrue(hasattr(self.speaker, 'preview_voice'), 'No explicit voice preview')
        self.speaker.last_text = 'Private previous reply.'
        self.speaker.preview_voice()
        self.assertEqual('Private previous reply.', self.speaker.last_text)
        self.assertNotIn('Private', self.engine.actions[0][0])
        self.assertIn('voice preview', self.engine.actions[0][0])
        with self.assertRaisesRegex(ValueError, 'Stop'):
            self.speaker.preview_voice()

    def test_missing_language_attribute_does_not_hide_an_usable_voice(self):
        self.assertTrue(hasattr(self.speaker, 'voice_options'), 'No voice catalog')
        with patch.object(self.engine.tokens[1], 'GetAttribute', side_effect=OSError('missing attribute')):
            options = self.speaker.voice_options()
        self.assertEqual(['token-A', 'token-B'], [item.id for item in options])
        self.assertEqual('', options[1].language)

    def test_missing_com_attribute_does_not_hide_voice(self):
        import comtypes
        with patch.object(self.engine.tokens[1], 'GetAttribute',
                          side_effect=comtypes.COMError(-2147200966, 'No attribute', None)):
            try:
                self.assertEqual('token-B', self.speaker.voice_options()[1].id)
            except comtypes.COMError:
                self.fail('An optional COM attribute hides a usable voice')

    def test_failed_native_voice_assignment_falls_back_with_a_warning(self):
        import comtypes
        engine = self.engine
        class RejectVoice:
            def __getattr__(self, name):
                return getattr(engine, name)
            def __setattr__(self, name, value):
                if name == 'Voice' and value.Id == 'token-B':
                    raise comtypes.COMError(-2147200966, 'Engine unavailable', None)
                setattr(engine, name, value)
        with patch('chat_reader.windows_audio.create_voice', return_value=RejectVoice()):
            try:
                speaker = app.create_windows_speaker(voice_id='token-B')
            except comtypes.COMError:
                self.fail('A failed voice assignment prevents fallback/startup')
        self.assertEqual('token-A', speaker.engine.Voice.Id)
        self.assertIn('default', speaker.voice_warning)
