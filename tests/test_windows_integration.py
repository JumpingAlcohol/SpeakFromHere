"""Opt-in Windows checks: real SAPI renders to temporary WAV files, never speakers."""

import _thread
import os
from pathlib import Path
import tempfile
import threading
import unittest
import wave

import win32api
import win32con
import win32gui
import time
import win32com.client

from chat_reader.app import WindowsDesktop, WindowsSpeaker
from chat_reader.core import run_reader_loop
from chat_reader.settings import Settings, save_settings, load_settings


@unittest.skipUnless(os.environ.get("CHAT_READER_WINDOWS_TESTS") == "1",
                     "Opt-in desktop integration checks")
class WindowsIntegrationTests(unittest.TestCase):
    def test_actual_alt_control_collision_is_rejected_and_registration_is_rolled_back(self):
        desktop = WindowsDesktop(settings=Settings(hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
        win32gui.RegisterHotKey(None, 91, win32con.MOD_ALT | 0x4000, ord("J"))
        try:
            with self.assertRaisesRegex(RuntimeError, "Alt \\+ J"):
                desktop.register()
            self.assertEqual([], desktop.registered)
        finally:
            desktop.close()
            win32gui.UnregisterHotKey(None, 91)

    def test_saved_custom_controls_release_old_bindings_and_can_register_again(self):
        with tempfile.TemporaryDirectory(prefix="reader-settings-") as folder:
            path = Path(folder) / "settings.json"
            save_settings(path, Settings(rate=3, hotkeys={"pause": "Alt+J", "stop": "Alt+K", "exit": "Alt+Shift+L"}))
            for _ in range(2):
                value = load_settings(path)
                desktop = WindowsDesktop(settings=value)
                test_registered = False
                voice = win32com.client.Dispatch("SAPI.SpVoice")
                voice.Volume = 0
                speaker = WindowsSpeaker(voice, rate=value.rate)
                try:
                    desktop.register()
                    self.assertEqual(3, voice.Rate)
                    win32gui.RegisterHotKey(None, 90, win32con.MOD_ALT | 0x4000, ord("P"))
                    test_registered = True
                    win32api.PostThreadMessage(win32api.GetCurrentThreadId(), win32con.WM_HOTKEY, 3, 0)
                    deadline = time.monotonic() + 1
                    event = None
                    while event is None and time.monotonic() < deadline:
                        event = desktop.next_hotkey()
                    self.assertEqual("pause", event)
                finally:
                    speaker.stop()
                    desktop.close()
                    if test_registered:
                        win32gui.UnregisterHotKey(None, 90)

    def test_real_voice_pauses_resumes_and_stops_without_playing_audible_audio(self):
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        voice.Volume = 0  # Mute only this test voice, not the system or the user's reader.
        speaker = WindowsSpeaker(voice)
        try:
            self.assertEqual("idle", speaker.toggle_pause())
            speaker.speak("This sentence gives us enough time to test pausing and resuming. " * 5)
            self.assertEqual("paused", speaker.toggle_pause())
            self.assertFalse(voice.WaitUntilDone(25), "A paused utterance should not finish")
            self.assertEqual("resumed", speaker.toggle_pause())
            speaker.stop()
            self.assertTrue(voice.WaitUntilDone(1000), "Stopping should clear pending speech")
            self.assertEqual("idle", speaker.toggle_pause())
        finally:
            speaker.stop()

    def test_real_voice_reads_new_selection_after_pause_and_after_stop(self):
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        voice.Volume = 0
        speaker = WindowsSpeaker(voice)
        try:
            speaker.speak("Original selection for a pause and replacement test. " * 5)
            self.assertEqual("paused", speaker.toggle_pause())
            speaker.speak("Replacement selection.")
            self.assertTrue(voice.WaitUntilDone(5000), "Replacement was left paused")
            speaker.speak("Another selection to pause and then stop. " * 5)
            self.assertEqual("paused", speaker.toggle_pause())
            speaker.stop()
            speaker.speak("After stopping, I can still read.")
            self.assertTrue(voice.WaitUntilDone(5000), "Stop left the next selection paused")
        finally:
            speaker.stop()

    def test_same_voice_renders_two_successive_requests(self):
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        speaker = WindowsSpeaker(voice)
        original_output = voice.AudioOutputStream
        try:
            with tempfile.TemporaryDirectory(prefix="chat-reader-test-") as folder:
                for index, text in enumerate(("First selection.", "Second selection.")):
                    stream = win32com.client.Dispatch("SAPI.SpFileStream")
                    path = Path(folder) / f"speech-{index}.wav"
                    stream.Open(str(path), 3)  # SSFMCreateForWrite
                    try:
                        voice.AudioOutputStream = stream
                        speaker.speak(text)
                        self.assertTrue(voice.WaitUntilDone(5000), "Speech did not finish")
                    finally:
                        speaker.stop()
                        voice.WaitUntilDone(1000)
                        voice.AudioOutputStream = original_output
                        stream.Close()
                    with wave.open(str(path), "rb") as audio:
                        self.assertGreater(audio.getnframes(), 1000)
        finally:
            speaker.stop()

    def test_real_windows_message_queue_handles_global_exit(self):
        desktop = WindowsDesktop()
        voice = WindowsSpeaker(win32com.client.Dispatch("SAPI.SpVoice"))
        messages = []
        # Deliver the same message Windows sends for the registered exit hotkey.
        original_register = desktop.register
        def register():
            original_register()
            win32api.PostThreadMessage(win32api.GetCurrentThreadId(), win32con.WM_HOTKEY, 2, 0)
        desktop.register = register
        run_reader_loop(desktop, voice, report=messages.append)
        self.assertEqual([], desktop.registered)
        self.assertEqual("SpeakFromHere stopped.", messages[-1])

    def test_keyboard_interrupt_exits_real_idle_windows_loop(self):
        desktop = WindowsDesktop()
        voice = WindowsSpeaker(win32com.client.Dispatch("SAPI.SpVoice"))
        messages = []
        timer = threading.Timer(0.15, _thread.interrupt_main)
        original_register = desktop.register
        def register():
            original_register()
            timer.start()
        desktop.register = register
        try:
            run_reader_loop(desktop, voice, report=messages.append)
        finally:
            timer.cancel()
            if timer.ident is not None:
                timer.join()
        self.assertEqual([], desktop.registered)
        self.assertEqual("SpeakFromHere stopped.", messages[-1])
