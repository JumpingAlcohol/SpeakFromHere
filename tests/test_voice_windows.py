"""Current-machine SAPI selection acceptance: owned WAVs/muted native output."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave


@unittest.skipUnless(os.environ.get('CHAT_READER_WINDOWS_TESTS') == '1', 'Opt-in real local voice checks')
class NativeVoiceTests(unittest.TestCase):
    def test_each_installed_voice_is_selected_and_renders_preview_without_overwriting_replay(self):
        from test_windows_audio import load_runtime
        import comtypes.client
        app = load_runtime()
        catalog = app.create_windows_speaker().voice_options()
        self.assertTrue(catalog, 'No installed SAPI voices to verify')
        with tempfile.TemporaryDirectory(prefix='reader-voice-wav-') as folder:
            for index, option in enumerate(catalog):
                with self.subTest(voice=option.name):
                    speaker = app.create_windows_speaker(rate=2, voice_id=option.id)
                    self.assertEqual(option.id.casefold(), speaker.engine.Voice.Id.casefold())
                    self.assertEqual('', speaker.voice_warning)
                    self.assertEqual(2, int(speaker.engine.Rate))
                    speaker.last_text = 'Previous synthetic reply.'
                    stream = comtypes.client.CreateObject('SAPI.SpFileStream', dynamic=True)
                    path = Path(folder) / f'{index}.wav'
                    stream.Format.Type = 22
                    stream.Open(str(path), 3)
                    speaker.engine.AllowAudioOutputFormatChangesOnNextSet = False
                    speaker.engine.AudioOutputStream = stream
                    try:
                        speaker.preview_voice()
                        self.assertTrue(speaker.engine.WaitUntilDone(10000))
                        self.assertEqual('Previous synthetic reply.', speaker.last_text)
                        speaker.set_voice('')
                        self.assertEqual('', speaker.voice_id)
                    finally:
                        speaker.stop()
                        speaker.engine.WaitUntilDone(1000)
                        stream.Close()
                    with wave.open(str(path)) as audio:
                        self.assertGreater(audio.getnframes(), 8820, 'Preview rendered no speech after cue')

    def test_each_installed_voice_keeps_native_pause_replacement_and_rate_controls(self):
        from test_windows_audio import load_runtime
        catalog = load_runtime().create_windows_speaker().voice_options()
        self.assertTrue(catalog)
        for option in catalog:
            for scenario in ('replace', 'rate'):
                with self.subTest(voice=option.name, scenario=scenario):
                    run = subprocess.run([sys.executable, str(Path(__file__).with_name('test_windows_audio.py')),
                                          '--native-case', scenario], capture_output=True, text=True,
                        encoding='utf-8', timeout=20,
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8', 'CHAT_READER_TEST_VOICE_ID': option.id})
                    self.assertEqual(0, run.returncode, run.stdout + run.stderr)
                    value = json.loads(next(line.removeprefix('AUDIO_RESULT=')
                        for line in run.stdout.splitlines() if line.startswith('AUDIO_RESULT=')))
                    self.assertEqual(option.id.casefold(), value['voice_id'].casefold(),
                                     'Saved selection did not reach the console runtime')
                    for cycle in value['cycles']:
                        self.assertTrue(cycle['held'], cycle)
                        self.assertTrue(cycle['advanced'], cycle)
                    self.assertTrue(value['exit_completed'])
                    if scenario == 'replace':
                        self.assertTrue(value['replacement_completed'])
                    else:
                        self.assertTrue(value['rate_held'])
                        self.assertTrue(value['rate_resumed'])
