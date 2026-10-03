"""Windows entry point for SpeakFromHere."""

import argparse
import ctypes
import sys
import pyperclip
import win32api
import win32con
import win32gui
from pynput import keyboard

from chat_reader.core import run_reader_loop
from chat_reader.settings import Settings, SettingsError, load_settings, save_settings, settings_path, parse_hotkey


class WindowsSpeaker:
    """Use SAPI asynchronously on the same thread that created the voice."""

    def __init__(self, engine, *, rate=0, audio_control=None, startup_cue=None):
        self.engine = engine
        self.engine.Rate = Settings(rate=rate).rate
        self.paused = False
        self.last_text = ""
        self.audio_control = audio_control
        self._output_paused = False
        self.startup_cue = startup_cue

    def _resume(self, *, cancel=False):
        if self._output_paused:
            if cancel:
                self.audio_control.cancel()
            else:
                self.audio_control.resume()
        else:
            self.engine.Resume()
        self._output_paused = False
        self.paused = False

    def set_rate(self, rate):
        self.engine.Rate = Settings(rate=rate).rate

    def playback_state(self):
        if self.paused:
            return "paused"
        return "idle" if self.engine.WaitUntilDone(0) else "playing"

    def play_pause(self):
        if self.playback_state() != "idle":
            return self.toggle_pause()
        if not self.last_text:
            return "idle"
        self.speak(self.last_text)
        return "replaying"

    def speak(self, text):
        if self.paused:
            self._resume(cancel=True)
        # The first text appends to the cue on the SAME voice. Purging here
        # would cancel the cue. Later reads retain ordinary replacement flags.
        try:
            cue_queued = bool(text.strip() and self.startup_cue and self.startup_cue.queue_once())
            # 1: async, 2: cancel previous speech, 16: plain text (never XML).
            self.engine.Speak(text, (1 | 16) if cue_queued else (1 | 2 | 16))
        except Exception:
            if self.startup_cue:
                try:
                    self.engine.Speak("", 1 | 2)
                except Exception:
                    pass  # Preserve the original submission error.
            raise
        self.last_text = text

    def stop(self):
        if self.paused:
            # Release the paused writer by discarding only its queued buffers,
            # immediately followed by SAPI's own utterance cancellation.
            self._resume(cancel=True)
        self.engine.Speak("", 1 | 2)

    def toggle_pause(self):
        if self.paused:
            self._resume()
            return "resumed"
        if self.engine.WaitUntilDone(0):
            return "idle"
        self._output_paused = bool(self.audio_control and self.audio_control.pause())
        if not self._output_paused:
            # Retain SAPI semantics for unopened devices/non-waveform streams.
            if self.engine.WaitUntilDone(0):
                return "idle"
            self.engine.Pause()
        self.paused = True
        return "paused"


def create_windows_speaker(*, rate=0):
    """Both runtime entries use the same owned voice and output controller."""
    from chat_reader.windows_audio import StartupCue, WaveOutputControl, create_voice
    engine = create_voice()
    return WindowsSpeaker(engine, rate=rate, audio_control=WaveOutputControl(engine),
                          startup_cue=StartupCue(engine))


class WindowsDesktop:
    """Windows hotkeys and clipboard; no work runs on a keyboard callback thread."""

    def __init__(self, *, enable_paragraphs=False, settings=None, hwnd=None):
        self.enable_paragraphs = enable_paragraphs
        self.hwnd = hwnd
        self.settings = settings or Settings()
        self.registered = []
        self.controller = keyboard.Controller()
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetClipboardSequenceNumber.argtypes = []
        self.user32.GetClipboardSequenceNumber.restype = ctypes.c_uint32

    def register(self):
        labels = {1: "Alt + S", 2: self.settings.hotkeys["exit"],
                  3: self.settings.hotkeys["pause"], 4: self.settings.hotkeys["stop"]}
        if self.enable_paragraphs:
            labels[5] = "Alt + E"
        for hotkey_id, label in labels.items():
            modifiers, key = parse_hotkey(label)
            try:
                win32gui.RegisterHotKey(self.hwnd, hotkey_id, modifiers | 0x4000, key)
            except Exception as error:
                self.close()
                raise RuntimeError(
                    f"Cannot register {label}. Close any other reader instance or app using this hotkey."
                ) from error
            self.registered.append(hotkey_id)

    def next_hotkey(self):
        found, message = win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
        if found:
            _, kind, hotkey_id, _, _, _ = message
            if kind == win32con.WM_QUIT:
                return "quit"
            if kind == win32con.WM_HOTKEY:
                events = {1: "read", 2: "quit", 3: "pause", 4: "stop"}
                if self.enable_paragraphs:
                    events[5] = "paragraph"
                return events.get(hotkey_id)
            win32gui.TranslateMessage(message)
            win32gui.DispatchMessage(message)
        return None

    def keys_down(self):
        keys = (win32con.VK_MENU, win32con.VK_CONTROL, win32con.VK_SHIFT,
                win32con.VK_LWIN, win32con.VK_RWIN, ord("S"))
        return any(win32api.GetAsyncKeyState(key) & 0x8000 for key in keys)

    def pointer_position(self):
        from chat_reader.windows_context import physical_cursor_position
        return physical_cursor_position()

    def clipboard_sequence(self):
        return self.user32.GetClipboardSequenceNumber()

    def send_copy(self):
        with self.controller.pressed(keyboard.Key.ctrl):
            self.controller.tap("c")

    def clipboard_text(self):
        return pyperclip.paste()

    def close(self):
        for hotkey_id in self.registered:
            win32gui.UnregisterHotKey(self.hwnd, hotkey_id)
        self.registered.clear()


def run(argv=None):
    parser = argparse.ArgumentParser(description="SpeakFromHere: selected text and optional experimental paragraphs.")
    parser.add_argument("--gui", action="store_true", help="Open the floating player (includes bounded Alt + E reading)")
    parser.add_argument("--paragraphs", action="store_true", default=bool(getattr(sys, "frozen", False)),
                        help="Enable Alt + E paragraph reading (default in the portable preview)")
    parser.add_argument("--paragraph-worker", nargs=2, type=int, help=argparse.SUPPRESS)
    parser.add_argument("--settings-file", help="Override the local settings path (for isolated profiles/testing)")
    parser.add_argument("--show-settings", action="store_true", help="Show settings without starting the reader")
    parser.add_argument("--set-rate", type=int, metavar="N", help="Save speaking rate -10 to 10; restart reader to apply")
    parser.add_argument("--set-hotkey", action="append", default=[], metavar="ACTION=CHORD",
                        help="Save pause, stop or exit binding, e.g. pause=Alt+J; restart to apply")
    parser.add_argument("--reset-settings", action="store_true", help="Explicitly replace settings with defaults")
    args = parser.parse_args(argv)
    if args.paragraph_worker is not None:
        from chat_reader.paragraph_worker import main
        raise SystemExit(main([str(value) for value in args.paragraph_worker]))
    try:
        if args.reset_settings and (args.set_rate is not None or args.set_hotkey):
            raise SettingsError("Use --reset-settings separately from other changes.")
        path = args.settings_file or settings_path()
        changed = args.set_rate is not None or bool(args.set_hotkey) or args.reset_settings
        warning = None
        try:
            value = Settings() if args.reset_settings else load_settings(path)
        except (SettingsError, OSError, UnicodeError) as error:
            if changed:
                raise SettingsError(f"Cannot modify settings: {error} Use --reset-settings explicitly to replace the file.") from error
            warning = f"{error} Using defaults; file left unchanged."
            if not args.gui:
                print("Settings warning: " + warning, flush=True)
            value = Settings()
        if changed:
            hotkeys = dict(value.hotkeys)
            seen = set()
            for assignment in args.set_hotkey:
                action, separator, chord = assignment.partition("=")
                if not separator or action not in hotkeys or action in seen:
                    raise SettingsError("Use each action once: pause=CHORD, stop=CHORD or exit=CHORD. Alt + S / Alt + E are fixed.")
                seen.add(action)
                hotkeys[action] = chord
            value = Settings(rate=value.rate if args.set_rate is None else args.set_rate, hotkeys=hotkeys,
                             language=value.language)
            save_settings(path, value)
            print("Settings saved. Restart the reader to apply changes; running instances are unchanged.", flush=True)
        if changed or args.show_settings:
            print(f"Settings file: {path}\nRate: {value.rate}\nRead selection: Alt + S (fixed)\nParagraph: Alt + E (fixed; only when enabled)", flush=True)
            for action, chord in value.hotkeys.items():
                print(f"{action}: {chord}", flush=True)
            return
        if args.gui:
            from chat_reader.gui import run_gui
            return run_gui(path, value, enable_paragraphs=True, warning=warning)
        print(f"Settings file: {path}", flush=True)
        speaker = create_windows_speaker(rate=value.rate)
        desktop = WindowsDesktop(enable_paragraphs=args.paragraphs, settings=value)
        paragraph_reader = None
        if args.paragraphs:
            from chat_reader.paragraph_job import ParagraphCapture
            paragraph_reader = ParagraphCapture()
        run_reader_loop(desktop, speaker, paragraph_reader=paragraph_reader, settings=value,
                        report=lambda message: print(message, flush=True))
    except Exception as error:
        if args.gui:
            ctypes.windll.user32.MessageBoxW(None, f"Reader could not start: {error}", "SpeakFromHere", 0x10)
        else:
            print(f"Reader could not start: {error}", flush=True)
        raise SystemExit(1) from error


if __name__ == "__main__":
    run()
