"""Floating Windows player. All Tk, hotkey and SAPI work stays on one thread."""
from collections import deque
import ctypes
import json
import tkinter as tk
from tkinter import messagebox
import win32api
import win32con
import win32gui

from chat_reader.player import TEXT, PlayerPreferences, bottom_right, play_button, skip_summary, skip_details
from chat_reader.paragraphs import ReadingPlan

BG, PANEL, BORDER, FG, MUTED, ACCENT = "#101724", "#192334", "#2b3a50", "#eff5ff", "#98a9c2", "#5ce0bb"


class TrayIcon:
    """Own a notification icon and its invisible callback window."""
    callback_message = win32con.WM_APP + 20

    def __init__(self, show):
        self.show = show
        self.added = False
        self.hwnd = None
        self.class_name = f"SpeakFromHereTray-{id(self)}"
        self.instance = win32api.GetModuleHandle(None)
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = self.instance
        window_class.lpszClassName = self.class_name
        window_class.lpfnWndProc = self._procedure
        win32gui.RegisterClass(window_class)
        try:
            self.hwnd = win32gui.CreateWindow(self.class_name, "SpeakFromHere tray", 0,
                                             0, 0, 0, 0, 0, 0, self.instance, None)
            icon = win32gui.LoadIcon(None, win32con.IDI_APPLICATION)
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD,
                (self.hwnd, 1, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                 self.callback_message, icon, "SpeakFromHere — click to show"))
            self.added = True
        except Exception:
            self.close()
            raise

    def _procedure(self, hwnd, message, wparam, lparam):
        if message == self.callback_message and lparam in (win32con.WM_LBUTTONUP, win32con.WM_RBUTTONUP):
            self.show()
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def close(self):
        if self.added:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 1))
            self.added = False
        if self.hwnd is not None:
            if win32gui.IsWindow(self.hwnd):
                win32gui.DestroyWindow(self.hwnd)
            self.hwnd = None
        win32gui.UnregisterClass(self.class_name, self.instance)


class PlayerWindow:
    def __init__(self, preferences, *, enable_paragraphs):
        self.preferences = preferences
        self.speaker = preferences.speaker
        self.enable_paragraphs = enable_paragraphs
        self.active_settings = preferences.value
        self.commands = deque()
        self.closed = False
        self.status_key, self.detail = "ready", ""
        self.skipped = ()
        self.last_skipped = ()
        self.dialog = None
        self.details_dialog = None
        self.tray = None
        self.old_procedure = None
        self.root = tk.Tk()
        self.root.withdraw()
        try:
            self.root.title("SpeakFromHere")
            self.root.overrideredirect(True)
            self.root.configure(bg=BG)
            self.root.protocol("WM_DELETE_WINDOW", lambda: self.commands.append("quit"))
            self.root.report_callback_exception = lambda typ, value, tb: self.error(value)
            self.buttons = {}
            card = tk.Frame(self.root, bg=BG, highlightbackground=BORDER, highlightthickness=1, padx=18, pady=16)
            card.pack(fill="both", expand=True)
            header = tk.Frame(card, bg=BG)
            header.pack(fill="x")
            title = tk.Label(header, text="SpeakFromHere", bg=BG, fg=FG, font=("Segoe UI", 13, "bold"))
            title.pack(side="left")
            for action, caption, command in (
                ("exit", "×", lambda: self.commands.append("quit")),
                ("hide", "—", self.hide), ("settings", "⚙", self.open_settings),
                ("language", "中文", self.change_language)):
                button = self._button(header, caption, command, small=True)
                button.pack(side="right", padx=(5, 0))
                self.buttons[action] = button
            self.subtitle = tk.Label(card, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
            self.subtitle.pack(fill="x", pady=(3, 15))
            status_row = tk.Frame(card, bg=BG)
            status_row.pack(fill="x")
            self.status = tk.Label(status_row, bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold"), anchor="w")
            self.status.pack(side="left", fill="x", expand=True)
            self.buttons["details"] = self._button(status_row, "Details", self.open_details, small=True)
            self.buttons["details"].pack(side="right")
            self.preview = tk.Label(card, bg=BG, fg=MUTED, font=("Segoe UI", 10), anchor="nw",
                                    justify="left", wraplength=396, height=2)
            self.preview.pack(fill="x", pady=(5, 14))
            self.skip_notice = tk.Label(card, bg=BG, fg="#ffbc7c", font=("Segoe UI", 9),
                                        anchor="nw", justify="left", wraplength=396, height=2)
            self.skip_notice.pack(fill="x", pady=(0, 8))
            controls = tk.Frame(card, bg=BG)
            controls.pack(fill="x")
            self.buttons["play"] = self._button(controls, "▶ Play", lambda: self.commands.append("play"), accent=True)
            self.buttons["play"].pack(side="left", ipadx=12, ipady=8)
            self.buttons["stop"] = self._button(controls, "■ Stop", lambda: self.commands.append("stop"))
            self.buttons["stop"].pack(side="left", padx=(8, 0), ipadx=5, ipady=8)
            speed = tk.Frame(controls, bg=PANEL, padx=5, pady=6)
            speed.pack(side="right")
            self.buttons["slower"] = self._button(speed, "−", lambda: self.change_rate(-1), small=True)
            self.buttons["slower"].pack(side="left")
            self.rate_label = tk.Label(speed, bg=PANEL, fg=FG, width=10, font=("Segoe UI", 9))
            self.rate_label.pack(side="left", padx=3)
            self.buttons["faster"] = self._button(speed, "+", lambda: self.change_rate(1), small=True)
            self.buttons["faster"].pack(side="left")
            self.rate_hint = tk.Label(card, bg=BG, fg=MUTED, font=("Segoe UI", 8), anchor="w")
            self.rate_hint.pack(fill="x", pady=(9, 0))
            self.guide = tk.Label(card, bg=BG, fg=MUTED, font=("Segoe UI", 9), anchor="w")
            self.guide.pack(fill="x", pady=(9, 0))
            self.refresh()
            self.root.update_idletasks()
            width = max(448, card.winfo_reqwidth())
            height = card.winfo_reqheight()
            self.root.geometry(f"{width}x{height}")
            self.root.update_idletasks()
            self.hwnd = win32gui.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            styles = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE,
                (styles | 0x08000000 | win32con.WS_EX_TOOLWINDOW) & ~win32con.WS_EX_APPWINDOW)
            self.old_procedure = win32gui.SetWindowLong(self.hwnd, win32con.GWL_WNDPROC, self._procedure)
            monitor = win32api.MonitorFromPoint(win32api.GetCursorPos(), win32con.MONITOR_DEFAULTTONEAREST)
            self.work_area = win32api.GetMonitorInfo(monitor)["Work"]
            x, y = bottom_right(self.work_area, width, height)
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, x, y, width, height, win32con.SWP_NOACTIVATE)
            # Rounded corners are an optional Windows 11 decoration.
            try:
                preference = ctypes.c_int(2)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(self.hwnd), 33,
                    ctypes.byref(preference), ctypes.sizeof(preference))
            except (AttributeError, OSError):
                pass
            title.bind("<ButtonPress-1>", self._begin_drag)
            title.bind("<B1-Motion>", self._drag)
            header.bind("<ButtonPress-1>", self._begin_drag)
            header.bind("<B1-Motion>", self._drag)
            try:
                self.tray = TrayIcon(self.show)
            except Exception as error:
                self.buttons["hide"].configure(state="disabled")
                self.error(error)
        except Exception:
            self.close()
            raise

    def _button(self, parent, text, command, *, small=False, accent=False):
        return tk.Button(parent, text=text, command=command, takefocus=False,
                         bg=ACCENT if accent else PANEL, fg="#09261e" if accent else FG,
                         activebackground="#85efd2" if accent else BORDER,
                         activeforeground="#09261e" if accent else FG, relief="flat", bd=0,
                         disabledforeground=MUTED, cursor="hand2", padx=8, pady=3,
                         font=("Segoe UI", 10 if small else 11, "normal" if small else "bold"))

    def _procedure(self, hwnd, message, wparam, lparam):
        if message == win32con.WM_MOUSEACTIVATE:
            return 3  # MA_NOACTIVATE: clicks work without moving app focus.
        if message == win32con.WM_HOTKEY:
            events = {1: "read", 2: "quit", 3: "pause", 4: "stop"}
            if self.enable_paragraphs:
                events[5] = "paragraph"
            event = events.get(wparam)
            if event:
                self.commands.append(event)
            return 0
        return win32gui.CallWindowProc(self.old_procedure, hwnd, message, wparam, lparam)

    def _begin_drag(self, event):
        x, y = win32api.GetCursorPos()
        left, top, _, _ = win32gui.GetWindowRect(self.hwnd)
        self.drag_offset = x - left, y - top

    def _drag(self, event):
        x, y = win32api.GetCursorPos()
        dx, dy = self.drag_offset
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, x - dx, y - dy, 0, 0,
                             win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    def show(self):
        if not self.closed:
            self.root.deiconify()
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)

    def hide(self):
        if self.tray and self.tray.added:
            self.root.withdraw()

    def change_rate(self, delta):
        try:
            self.preferences.update(rate=max(-10, min(10, self.preferences.value.rate + delta)))
            self.refresh()
        except Exception as error:
            self.error(error)

    def change_language(self):
        try:
            language = "zh-CN" if self.preferences.value.language == "en" else "en"
            self.preferences.update(language=language)
            if self.dialog:
                self.dialog.close()
            self.refresh()
        except Exception as error:
            self.error(error)

    def error(self, error):
        self.status_key, self.detail = "error", str(error)
        self.refresh()

    def report(self, message):
        if message.startswith(("Reading:", "Reading paragraph:")):
            self.skipped = ()
            self.last_skipped = ()
            if self.details_dialog:
                self.details_dialog.close()
            self.status_key, self.detail = "playing", message.split(":", 1)[1].strip()
        elif message.startswith("Skipped content: "):
            try:
                self.skipped = ReadingPlan.from_payload({"text": "metadata", "skipped": json.loads(
                    message[len("Skipped content: "):])}).skipped
                self.last_skipped = self.skipped
            except (ValueError, TypeError):
                self.error("Skipped-content details are invalid. Do not assume all content was read.")
                return
        elif message.startswith("Checking paragraph"):
            self.skipped = ()
            if self.details_dialog:
                self.details_dialog.close()
            self.status_key, self.detail = "checking", ""
        elif message.startswith("Could not") or "No new text copied" in message or "not enabled" in message:
            self.status_key, self.detail = "error", message
        elif message.startswith("Settings warning:"):
            self.status_key, self.detail = "warning", message
        elif message.startswith("Speech paused"):
            self.skipped = self.last_skipped
            self.status_key = "paused"
        elif message.startswith(("Speech resumed", "Replaying")):
            self.skipped = self.last_skipped
            self.status_key = "playing"
        elif message.startswith(("Speech stopped", "Nothing is currently")):
            self.status_key = "ready"
        self.refresh()

    def refresh(self):
        if self.closed:
            return
        language = self.preferences.value.language
        text = TEXT[language]
        state = self.speaker.playback_state()
        if self.status_key in ("ready", "playing", "paused"):
            self.status_key = {"playing": "playing", "paused": "paused", "idle": "ready"}[state]
        label, enabled = play_button(self.speaker, language)
        self.buttons["play"].configure(text=("Ⅱ " if state == "playing" else "▶ ") + label,
                                      state="normal" if enabled else "disabled")
        self.buttons["stop"].configure(text="■ " + text["stop"])
        self.buttons["language"].configure(text="中文" if language == "en" else "EN")
        self.subtitle.configure(text=text["subtitle"])
        self.status.configure(text="●  " + text[self.status_key], fg="#ffbc7c" if self.status_key in ("error", "warning") else ACCENT)
        self.preview.configure(text=self.detail or text["empty"])
        self.skip_notice.configure(text=skip_summary(self.skipped, language))
        self.buttons["details"].configure(text=text["diagnostic"],
            state="normal" if self.skipped or (self.status_key in ("error", "warning") and self.detail) else "disabled")
        rate = self.preferences.value.rate
        description = text["slow"] if rate < 0 else text["fast"] if rate > 0 else text["normal"]
        self.rate_label.configure(text=f"{description} {rate:+d}")
        self.buttons["slower"].configure(state="normal" if rate > -10 else "disabled")
        self.buttons["faster"].configure(state="normal" if rate < 10 else "disabled")
        self.rate_hint.configure(text=text["next"])
        self.guide.configure(text=text["guide"] if self.enable_paragraphs else "Alt + S  " + text["empty"])

    def open_settings(self):
        if self.dialog:
            self.dialog.root.lift()
        else:
            self.dialog = SettingsDialog(self)
        return self.dialog

    def open_details(self):
        if self.details_dialog:
            self.details_dialog.root.lift()
        else:
            message = self.detail if self.status_key in ("error", "warning") else ""
            skipped = skip_details(self.skipped)
            self.details_dialog = DetailsDialog(self, "\n\n".join(item for item in (message, skipped) if item))
        return self.details_dialog

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.dialog:
                self.dialog.close()
            if self.details_dialog:
                self.details_dialog.close()
            if self.tray:
                self.tray.close()
        finally:
            try:
                if self.old_procedure and win32gui.IsWindow(self.hwnd):
                    # pywin32's WNDPROC setter accepts callbacks, not the saved
                    # native pointer. Restore it with the pointer-sized API.
                    restore = ctypes.windll.user32.SetWindowLongPtrW
                    restore.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t)
                    restore.restype = ctypes.c_ssize_t
                    restore(self.hwnd, win32con.GWL_WNDPROC, self.old_procedure)
            finally:
                self.root.destroy()


class DetailsDialog:
    """Complete read-only error text, only in memory; no automatic clipboard write."""
    def __init__(self, window, message):
        self.window = window
        self.root = tk.Toplevel(window.root)
        self.root.title("SpeakFromHere — " + TEXT[window.preferences.value.language]["diagnostic"])
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.content = tk.Text(self.root, width=64, height=10, wrap="word",
                               bg=PANEL, fg=FG, font=("Segoe UI", 10), padx=12, pady=12)
        self.content.pack(fill="both", expand=True)
        self.content.insert("1.0", message)
        self.content.configure(state="disabled")

    def close(self):
        self.window.details_dialog = None
        self.root.destroy()


class SettingsDialog:
    def __init__(self, window):
        self.window = window
        self.root = tk.Toplevel(window.root)
        self.root.configure(bg=BG, padx=18, pady=18)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        text = TEXT[window.preferences.value.language]
        self.root.title(text["settings"])
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.variables = {}
        for row, action in enumerate(("pause", "stop", "exit")):
            tk.Label(self.root, text=text[action], bg=BG, fg=FG, font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=6)
            variable = tk.StringVar(value=window.preferences.value.hotkeys[action])
            self.variables[action] = variable
            tk.Entry(self.root, textvariable=variable, bg=PANEL, fg=FG, insertbackground=FG,
                     relief="flat", font=("Segoe UI", 11), width=23).grid(row=row, column=1, padx=(18, 0), pady=6)
        tk.Label(self.root, text=text["restart"] + "\nAlt + S / Alt + E: fixed", bg=BG,
                 fg=MUTED, justify="left", font=("Segoe UI", 9)).grid(row=3, column=0, columnspan=2, pady=12)
        self.error_label = tk.Label(self.root, bg=BG, fg="#ffbc7c", wraplength=330, justify="left")
        self.error_label.grid(row=4, column=0, columnspan=2)
        window._button(self.root, text["reset"], self.reset).grid(row=5, column=0, pady=(12, 0), sticky="w")
        window._button(self.root, text["save"], self.save, accent=True).grid(row=5, column=1, pady=(12, 0), sticky="e")

    def save(self):
        try:
            self.window.preferences.update(hotkeys={action: value.get() for action, value in self.variables.items()})
            self.window.status_key, self.window.detail = "ready", TEXT[self.window.preferences.value.language]["restart"]
            self.window.refresh()
            self.close()
        except Exception as error:
            self.error_label.configure(text=str(error))

    def reset(self):
        text = TEXT[self.window.preferences.value.language]
        if messagebox.askyesno(text["reset"], text["reset_confirm"], parent=self.root):
            try:
                self.window.preferences.reset()
                self.window.status_key, self.window.detail = "ready", TEXT["en"]["restart"]
                self.window.refresh()
                self.close()
            except Exception as error:
                self.error_label.configure(text=str(error))

    def close(self):
        self.window.dialog = None
        self.root.destroy()


class GuiDesktop:
    """Keep Tk dispatch from swallowing thread hotkeys by binding them to our HWND."""
    def __init__(self, window, desktop):
        self.window, self.desktop = window, desktop
        self.closed = False

    def __getattr__(self, name):
        return getattr(self.desktop, name)

    def register(self):
        self.desktop.register()
        self.window.show()

    def next_hotkey(self):
        self.window.root.update()
        self.window.refresh()
        return self.window.commands.popleft() if self.window.commands else None

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                self.desktop.close()
            finally:
                self.window.close()


def run_gui(path, value, *, enable_paragraphs=True, warning=None):
    from chat_reader.app import WindowsDesktop, WindowsSpeaker
    from chat_reader.core import run_reader_loop
    from chat_reader.paragraph_job import ParagraphCapture
    import win32com.client
    # Set DPI awareness before creating any Tk widgets, never change another app.
    ctypes.windll.user32.SetProcessDPIAware()
    speaker = WindowsSpeaker(win32com.client.Dispatch("SAPI.SpVoice"), rate=value.rate)
    window = PlayerWindow(PlayerPreferences(path, value, speaker), enable_paragraphs=enable_paragraphs)
    desktop = GuiDesktop(window, WindowsDesktop(settings=value, enable_paragraphs=enable_paragraphs, hwnd=window.hwnd))
    try:
        if warning:
            window.report("Settings warning: " + warning)
        run_reader_loop(desktop, speaker, report=window.report, settings=value,
                        paragraph_reader=ParagraphCapture() if enable_paragraphs else None)
    finally:
        desktop.close()
