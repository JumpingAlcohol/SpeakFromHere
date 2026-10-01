"""Opt-in bundled UIA check, confined to a synthetic window owned by this test."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import uuid

import win32api
import win32con
import win32gui
import win32job


@unittest.skipUnless(os.environ.get("CHAT_READER_PORTABLE_TESTS") == "1", "Opt-in portable worker fixture")
class BundledWorkerTests(unittest.TestCase):
    def test_standalone_worker_loads_uia_and_rejects_a_nonchat_owned_window(self):
        """Missing bundled COM bindings or routing into speech breaks the worker result."""
        from chat_reader.uia_probe import WindowsUIA
        source = Path(__file__).resolve().parents[1] / "outputs/v0.2.0/AIChatReader.exe"
        self.assertTrue(source.is_file(), "Build the v0.2.0 portable preview first")
        ready, finished = threading.Event(), threading.Event()
        handles, errors = [], []
        name = "ReaderPackageTest_" + uuid.uuid4().hex

        def fixture():
            registered = False
            try:
                window_class = win32gui.WNDCLASS()
                window_class.hInstance = win32api.GetModuleHandle(None)
                window_class.lpszClassName = name
                window_class.lpfnWndProc = win32gui.DefWindowProc
                win32gui.RegisterClass(window_class)
                registered = True
                parent = win32gui.CreateWindowEx(
                    win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW | 0x08000000,
                    name, "AI Chat Reader package test", win32con.WS_POPUP | win32con.WS_VISIBLE | win32con.WS_CAPTION,
                    40, 40, 340, 100, 0, 0, window_class.hInstance, None)
                handles.append(parent)
                handles.append(win32gui.CreateWindowEx(
                    0, "Static", "Synthetic package test paragraph.",
                    win32con.WS_CHILD | win32con.WS_VISIBLE, 5, 5, 320, 60,
                    parent, 0, window_class.hInstance, None))
                ready.set()
                while not finished.wait(0.01):
                    win32gui.PumpWaitingMessages()
            except Exception as error:
                errors.append(error)
                ready.set()
            finally:
                if handles:
                    win32gui.DestroyWindow(handles[0])
                if registered:
                    win32gui.UnregisterClass(name, win32api.GetModuleHandle(None))

        thread = threading.Thread(target=fixture, daemon=True)
        thread.start()
        try:
            self.assertTrue(ready.wait(5), "The synthetic window did not start")
            if errors:
                raise errors[0]
            uia = WindowsUIA()
            parent = uia.describe(uia.automation.ElementFromHandle(handles[0]))
            self.assertEqual(50032, parent["control_type"], "Capture must stop at our owned Window")
            child = uia.describe(uia.automation.ElementFromHandle(handles[1]))
            left, top, width, height = child["bounds"]
            point = (int(left + width / 2), int(top + height / 2))
            self.assertEqual(handles[1], win32gui.WindowFromPoint(point), "Another window covers the fixture")
            with tempfile.TemporaryDirectory(prefix="reader-portable-worker-") as folder:
                executable = Path(folder) / "AIChatReader.exe"
                shutil.copy2(source, executable)
                # The job owns only this spawned process tree and kills it on cleanup.
                job = win32job.CreateJobObject(None, name + "_job")
                limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
                limits["BasicLimitInformation"]["LimitFlags"] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
                process = subprocess.Popen(
                    [str(executable), "--paragraph-worker", str(point[0]), str(point[1])], cwd=folder,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                    creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    win32job.AssignProcessToJobObject(job, process._handle)
                    deadline = time.monotonic() + 10
                    while True:
                        # UIA created on this STA thread may receive provider
                        # callbacks while another process inspects our window.
                        win32gui.PumpWaitingMessages()
                        try:
                            stdout, stderr = process.communicate(timeout=0.05)
                            break
                        except subprocess.TimeoutExpired:
                            if time.monotonic() >= deadline:
                                raise
                    self.assertEqual(1, process.returncode)
                    self.assertEqual("", stdout)
                    self.assertIn("This app/build has not been inspected", stderr)
                    self.assertNotIn("Traceback", stderr)
                finally:
                    win32job.TerminateJobObject(job, 1)
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        active = win32job.QueryInformationJobObject(job, win32job.JobObjectBasicAccountingInformation)["ActiveProcesses"]
                        if not active:
                            break
                        win32gui.PumpWaitingMessages()
                        time.sleep(0.01)
                    job.Close()
                    process.wait(timeout=5)
        finally:
            finished.set()
            thread.join(5)
            self.assertFalse(thread.is_alive(), "The synthetic package window did not close")
