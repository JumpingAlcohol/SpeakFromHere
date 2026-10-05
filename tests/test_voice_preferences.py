import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from chat_reader import app
from chat_reader.core import run_reader_loop
from chat_reader.player import PlayerPreferences
from chat_reader.settings import Settings, load_settings, save_settings
from test_runtime import Clock, Desktop
from test_paragraph_runtime import Capture
from voice_fixtures import VoiceEngine


class VoicePreferenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'settings.json'
        self.speaker = app.WindowsSpeaker(VoiceEngine())
        self.model = PlayerPreferences(self.path, Settings(), self.speaker)

    def test_gui_voice_save_reaches_runtime_and_merges_existing_keys(self):
        save_settings(self.path, Settings(rate=2, language='zh-CN'))
        self.model.update(voice_id='token-B')
        self.assertEqual('token-B', self.speaker.engine.Voice.Id, 'GUI saves but does not apply voice')
        value = load_settings(self.path)
        self.assertEqual(('token-B', 2, 'zh-CN'), (value.voice_id, value.rate, value.language))

    def test_failed_disk_save_restores_both_voice_and_rate(self):
        save_settings(self.path, Settings(rate=2))
        self.speaker.set_rate(2)
        before = self.path.read_bytes()
        def disk_failure(*_args):
            self.assertEqual('token-B', self.speaker.engine.Voice.Id,
                             'The transaction did not apply the chosen voice')
            raise OSError('disk unavailable')
        with patch('chat_reader.player.save_settings', side_effect=disk_failure):
            with self.assertRaises(OSError):
                self.model.update(voice_id='token-B', rate=4)
        self.assertEqual(('token-A', 2, ''),
                         (self.speaker.engine.Voice.Id, self.speaker.engine.Rate, self.speaker.voice_id))
        self.assertEqual(before, self.path.read_bytes())

    def test_busy_voice_change_cannot_write_new_preference(self):
        self.speaker.speak('Previous.')
        with self.assertRaisesRegex(ValueError, 'Stop'):
            self.model.update(voice_id='token-B')
        self.assertFalse(self.path.exists())
        self.assertEqual('token-A', self.speaker.engine.Voice.Id)

    def test_rate_command_preserves_voice_without_starting_sapi(self):
        save_settings(self.path, Settings(voice_id='token-B'))
        with patch('sys.stdout', new=io.StringIO()), patch.object(app, 'create_windows_speaker', side_effect=AssertionError('Speech started')):
            app.run(['--settings-file', str(self.path), '--set-rate', '3'])
        self.assertEqual('token-B', load_settings(self.path).voice_id)

    def test_busy_rejection_never_reassigns_even_the_previous_voice(self):
        class RejectActiveAssignment(VoiceEngine):
            def __setattr__(self, name, value):
                if name == 'Voice' and hasattr(self, 'Voice') and self.Status.RunningState == 2:
                    raise AssertionError('A refused switch still reassigns a live SAPI voice')
                super().__setattr__(name, value)
        self.speaker.engine = RejectActiveAssignment()
        self.speaker.engine.Rate = 0
        self.speaker.speak('Current synthetic reply.')
        with self.assertRaisesRegex(ValueError, 'Stop'):
            self.model.update(voice_id='token-B')

    def test_preview_event_cancels_pending_capture_and_keeps_reply_for_replay(self):
        clock, capture = Clock(), Capture()
        desktop = Desktop(clock)
        desktop.events = iter(['preview', 'quit'])
        self.speaker.last_text = 'Previous reply.'
        messages = []
        run_reader_loop(desktop, self.speaker, paragraph_reader=capture, report=messages.append,
                        clock=clock.monotonic, sleep=clock.sleep)
        self.assertTrue(any('Voice preview:' in message for message in messages), 'Preview event ignored')
        self.assertEqual('Previous reply.', self.speaker.last_text)
        self.assertEqual(7, desktop.sequence, 'Preview must not copy')
        self.assertGreaterEqual(capture.cancellations, 1)

    def test_cli_voice_list_and_selection_never_speak_or_register_hotkeys(self):
        engine = self.speaker.engine
        with patch('chat_reader.windows_audio.create_voice', return_value=engine), \
                patch.object(app, 'WindowsDesktop', side_effect=AssertionError('Desktop started')), \
                patch('sys.stdout', new=io.StringIO()) as output:
            try:
                app.run(['--settings-file', str(self.path), '--list-voices'])
            except SystemExit as error:
                self.fail(f'Voice-list command unavailable: exit {error.code}')
            self.assertFalse(self.path.exists())
            self.assertIn('token-B', output.getvalue())
            app.run(['--settings-file', str(self.path), '--set-voice', 'token-B'])
            self.assertEqual('token-B', load_settings(self.path).voice_id)
        self.assertEqual([], engine.actions)
