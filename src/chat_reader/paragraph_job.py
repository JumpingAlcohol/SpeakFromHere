"""Cancelable worker jobs; native UIA never blocks the speech/control thread."""

import json
import queue
import subprocess
import sys
import threading
import time


class ParagraphCapture:
    def __init__(self, *, launch=subprocess.Popen, timeout=20):
        self.launch = launch
        self.timeout = timeout
        self.current = None
        self.results = queue.Queue()
        self.threads = []

    def start(self, point):
        self.cancel()
        command = ([sys.executable, "--paragraph-worker"] if getattr(sys, "frozen", False)
                   else [sys.executable, "-m", "chat_reader.paragraph_worker"])
        process = self.launch(
            command + [str(point[0]), str(point[1])],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.current = process
        thread = threading.Thread(target=self._collect, args=(process, tuple(point)), daemon=True)
        self.threads = [item for item in self.threads if item.is_alive()]
        self.threads.append(thread)
        thread.start()

    def _collect(self, process, point):
        try:
            stdout, stderr = process.communicate(timeout=self.timeout)
            if process.returncode:
                result = (None, stderr.strip() or "The paragraph worker failed. Use Alt + S.")
            else:
                data = json.loads(stdout)
                text = data.get("text")
                if data.get("point") != list(point) or not isinstance(text, str) or not text.strip():
                    raise ValueError("Invalid paragraph response")
                result = (text, None)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            result = (None, "Paragraph capture timed out. Try again or use Alt + S.")
        except (ValueError, TypeError, AttributeError, OSError):
            if process.poll() is None:
                process.kill()
            process.communicate()
            result = (None, "The worker did not return a valid paragraph. Use Alt + S.")
        self.results.put((process, result))

    def poll(self):
        while True:
            try:
                process, result = self.results.get_nowait()
            except queue.Empty:
                return None
            if process is self.current:
                self.current = None
                return result

    def cancel(self):
        process, self.current = self.current, None
        if process is not None and process.poll() is None:
            process.kill()

    def close(self):
        self.cancel()
        deadline = time.monotonic() + 0.5
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
