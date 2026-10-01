"""Windows entry point for AI Chat Reader."""

import argparse
import ctypes
import sys
import pyperclip
import win32api
import win32con
import win32gui
import win32com.client
from pynput import keyboard

from chat_reader.core import run_reader_loop


class WindowsSpeaker:
    """Use SAPI asynchronously on the same thread that created the voice."""

    def __init__(self, engine):
        self.engine = engine
        self.paused = False

    def speak(self, text):
        if self.paused:
            self.engine.Resume()
            self.paused = False
        # 1: async, 2: cancel previous speech, 16: plain text (never XML).
        self.engine.Speak(text, 1 | 2 | 16)

    def stop(self):
        if self.paused:
            self.engine.Resume()
            self.paused = False
        self.engine.Speak("", 1 | 2)

    def toggle_pause(self):
        if self.paused:
            self.engine.Resume()
            self.paused = False
            return "resumed"
        if self.engine.WaitUntilDone(0):
            return "idle"
        self.engine.Pause()
        self.paused = True
        return "paused"


class WindowsDesktop:
    """Windows hotkeys and clipboard; no work runs on a keyboard callback thread."""

    def __init__(self, *, enable_paragraphs=False):
        self.enable_paragraphs = enable_paragraphs
        self.registered = []
        self.controller = keyboard.Controller()
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetClipboardSequenceNumber.argtypes = []
        self.user32.GetClipboardSequenceNumber.restype = ctypes.c_uint32

    def register(self):
        bindings = [
            (1, win32con.MOD_ALT | 0x4000, ord("S")),
            (2, win32con.MOD_ALT | win32con.MOD_SHIFT | 0x4000, ord("Q")),
            (3, win32con.MOD_ALT | 0x4000, ord("P")),
            (4, win32con.MOD_ALT | 0x4000, ord("X")),
        ]
        if self.enable_paragraphs:
            bindings.append((5, win32con.MOD_ALT | 0x4000, ord("E")))
        for hotkey_id, modifiers, key in bindings:
            try:
                win32gui.RegisterHotKey(None, hotkey_id, modifiers, key)
            except Exception as error:
                label = {1: "Alt + S", 2: "Alt + Shift + Q",
                         3: "Alt + P", 4: "Alt + X", 5: "Alt + E"}[hotkey_id]
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
            win32gui.UnregisterHotKey(None, hotkey_id)
        self.registered.clear()


def run(argv=None):
    parser = argparse.ArgumentParser(description="AI Chat Reader: selected text and optional experimental paragraphs.")
    parser.add_argument("--paragraphs", action="store_true", default=bool(getattr(sys, "frozen", False)),
                        help="Enable Alt + E paragraph reading (default in the portable preview)")
    parser.add_argument("--paragraph-worker", nargs=2, type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.paragraph_worker is not None:
        from chat_reader.paragraph_worker import main
        raise SystemExit(main([str(value) for value in args.paragraph_worker]))
    try:
        speaker = WindowsSpeaker(win32com.client.Dispatch("SAPI.SpVoice"))
        desktop = WindowsDesktop(enable_paragraphs=args.paragraphs)
        paragraph_reader = None
        if args.paragraphs:
            from chat_reader.paragraph_job import ParagraphCapture
            paragraph_reader = ParagraphCapture()
        run_reader_loop(desktop, speaker, paragraph_reader=paragraph_reader,
                        report=lambda message: print(message, flush=True))
    except Exception as error:
        print(f"Reader could not start: {error}", flush=True)
        raise SystemExit(1) from error


if __name__ == "__main__":
    run()
