"""Real windowed bundle, isolated settings and only test-owned process trees."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid
import zipfile

import win32con
import win32gui
import win32job
import win32process


@unittest.skipUnless(os.environ.get("CHAT_READER_PORTABLE_TESTS") == "1", "Opt-in windowed portable check")
class PortableGuiTests(unittest.TestCase):
    def test_zip_contains_gui_console_and_both_canonical_guides(self):
        root = Path(__file__).resolve().parents[1]
        with zipfile.ZipFile(root / "outputs/v0.3.0/SpeakFromHere/SpeakFromHere-Windows-x64.zip") as archive:
            files = {name for name in archive.namelist() if not name.endswith("/")}
            top = {"SpeakFromHere.exe", "SpeakFromHereConsole.exe", "QuickStart.en.txt", "QuickStart.zh-CN.txt"}
            self.assertEqual(top, {name for name in files if "/" not in name})
            self.assertIn("reader-worker/SpeakFromHereWorker.exe", files)
            self.assertIn("reader-worker/_internal/python312.dll", files)
            self.assertTrue(all(name in top or name.startswith("reader-worker/") for name in files))
            helper = root / "outputs/v0.3.0/SpeakFromHere/reader-worker"
            expected = {"reader-worker/" + path.relative_to(helper).as_posix()
                        for path in helper.rglob("*") if path.is_file()}
            self.assertEqual(expected, files - top, "ZIP must include every helper runtime file")
            for name in ("QuickStart.en.txt", "QuickStart.zh-CN.txt"):
                self.assertEqual((root / "docs" / name).read_bytes(), archive.read(name))

    def test_double_click_entry_shows_nonactivating_player_and_releases_actual_hotkeys_twice(self):
        source = Path(__file__).resolve().parents[1] / "outputs/v0.3.0/SpeakFromHere/SpeakFromHere.exe"
        self.assertTrue(source.is_file(), "Build the GUI candidate first")
        with tempfile.TemporaryDirectory(prefix="reader-gui-bundle-") as folder:
            executable = Path(folder) / "SpeakFromHere.exe"
            shutil.copy2(source, executable)
            for attempt in range(2):
                job = win32job.CreateJobObject(None, "ReaderGuiTest_" + uuid.uuid4().hex)
                limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
                limits["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
                process = subprocess.Popen([str(executable), "--settings-file", str(Path(folder) / "settings.json")],
                                           cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    win32job.AssignProcessToJobObject(job, process._handle)
                    deadline = time.monotonic() + 20
                    player = None
                    while time.monotonic() < deadline:
                        pids = win32job.QueryInformationJobObject(job, win32job.JobObjectBasicProcessIdList)
                        windows = []
                        def collect(hwnd, unused):
                            if win32process.GetWindowThreadProcessId(hwnd)[1] in pids:
                                windows.append(hwnd)
                        win32gui.EnumWindows(collect, None)
                        self.assertFalse(any(win32gui.GetClassName(hwnd) == "ConsoleWindowClass" for hwnd in windows))
                        found = [hwnd for hwnd in windows if win32gui.GetWindowText(hwnd) == "SpeakFromHere" and win32gui.IsWindowVisible(hwnd)]
                        if found:
                            player = found[0]
                            break
                        self.assertIsNone(process.poll(), "The bundle exited before showing its player")
                        time.sleep(0.05)
                    self.assertIsNotNone(player, "Floating player did not appear")
                    style = win32gui.GetWindowLong(player, win32con.GWL_EXSTYLE)
                    details = []
                    win32gui.EnumChildWindows(player, lambda hwnd, _: details.append(win32gui.GetWindowText(hwnd)), None)
                    self.assertTrue(style & 0x08000000, f"Unexpected window {win32gui.GetClassName(player)}: {details}")
                    self.assertTrue(style & win32con.WS_EX_TOPMOST)
                    for modifiers, letter in ((1, "S"), (1, "E"), (1, "P"), (1, "X"), (5, "Q")):
                        with self.assertRaises(Exception) as conflict:
                            win32gui.RegisterHotKey(None, 208, modifiers | 0x4000, ord(letter))
                        self.assertEqual(1409, conflict.exception.winerror, "Expected OS hotkey ownership, not another error")
                    # Do not inject keyboard input/copy text from other applications.
                    for event in (3, 4, 2):
                        win32gui.PostMessage(player, win32con.WM_HOTKEY, event, 0)
                    stdout, stderr = process.communicate(timeout=10)
                    self.assertEqual(0, process.returncode)
                    self.assertEqual((b"", b""), (stdout, stderr))
                    self.assertFalse(win32gui.IsWindow(player))
                    for modifiers, letter in ((1, "S"), (1, "E"), (1, "P"), (1, "X"), (5, "Q")):
                        win32gui.RegisterHotKey(None, 208, modifiers | 0x4000, ord(letter))
                        win32gui.UnregisterHotKey(None, 208)
                    self.assertFalse((Path(folder) / "settings.json").exists(), "Startup must not write preferences/chat text")
                finally:
                    win32job.TerminateJobObject(job, 1)
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        if not win32job.QueryInformationJobObject(job, win32job.JobObjectBasicAccountingInformation)["ActiveProcesses"]:
                            break
                        time.sleep(0.01)
                    process.wait(timeout=5)
                    job.Close()
                    if process.stdout:
                        process.stdout.close()
                    if process.stderr:
                        process.stderr.close()
