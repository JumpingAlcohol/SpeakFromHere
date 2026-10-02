"""Cancelable worker jobs; native UIA never blocks the speech/control thread."""

import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from chat_reader.paragraphs import ReadingPlan


class ParagraphCapture:
    def __init__(self, *, launch=subprocess.Popen, timeout=20):
        self.launch = launch
        self.timeout = timeout
        self.current = None
        self.results = queue.Queue()
        self.threads = []
        self.lock = threading.Lock()

    def start(self, point):
        self.cancel()
        # Snapshot coordinates and command on the control thread. Launch itself
        # can take seconds on Windows and must not prevent pause/stop/exit.
        if getattr(sys, "frozen", False):
            command = [str(Path(sys.executable).parent / "reader-worker" / "SpeakFromHereWorker.exe")]
        else:
            python = Path(sys.executable)
            if python.name.lower() == "pythonw.exe":
                python = python.with_name("python.exe")
            command = [str(python), "-m", "chat_reader.paragraph_worker"]
        request = {"point": tuple(point), "process": None, "canceled": False,
                   "deadline": time.monotonic() + self.timeout}
        with self.lock:
            self.current = request
        # Non-daemon: an exit during native startup must still reap the owned
        # child once Popen returns, rather than orphan it when Python shuts down.
        thread = threading.Thread(target=self._collect, args=(request, command))
        self.threads = [item for item in self.threads if item.is_alive()]
        self.threads.append(thread)
        thread.start()

    def _collect(self, request, command):
        process = None
        point = request["point"]
        try:
            with self.lock:
                if request["canceled"]:
                    return
            if len(command) == 1 and not Path(command[0]).is_file():
                raise FileNotFoundError("Missing reader-worker. Extract the full SpeakFromHere ZIP together; use Alt + S meanwhile.")
            process = self.launch(
                command + [str(point[0]), str(point[1])],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            with self.lock:
                request["process"] = process
                canceled = request["canceled"]
            if canceled:
                self._terminate(process)
                process.communicate()
                return
            remaining = request["deadline"] - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, self.timeout)
            stdout, stderr = process.communicate(timeout=remaining)
            if process.returncode:
                result = (None, stderr.strip() or "The paragraph worker failed. Use Alt + S.")
            else:
                data = json.loads(stdout)
                text = data.get("text")
                if data.get("point") != list(point) or not isinstance(text, str) or not text.strip():
                    raise ValueError("Invalid paragraph response")
                result = (ReadingPlan.from_payload(data) if "skipped" in data else text, None)
        except subprocess.TimeoutExpired:
            self._terminate(process)
            process.communicate()
            result = (None, "Paragraph capture timed out. Try again or use Alt + S.")
        except (ValueError, TypeError, AttributeError, OSError) as error:
            if process is not None:
                self._terminate(process)
                process.communicate()
            result = (None, f"Could not start the paragraph worker: {error}" if process is None
                      else "The worker did not return a valid paragraph. Use Alt + S.")
        self.results.put((request, result))

    def poll(self):
        while True:
            try:
                request, result = self.results.get_nowait()
            except queue.Empty:
                return None
            with self.lock:
                if request is self.current:
                    self.current = None
                    return result

    def cancel(self):
        with self.lock:
            request, self.current = self.current, None
            if request is None:
                return
            request["canceled"] = True
            process = request["process"]
        if process is not None:
            self._terminate(process)

    @staticmethod
    def _terminate(process):
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                # Another collector may have already observed natural exit.
                if process.poll() is None:
                    raise

    def close(self):
        self.cancel()
        deadline = time.monotonic() + 0.5
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
