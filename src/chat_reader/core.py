import time


def read_selected_text(copy_selection, get_clipboard_text, speaker):
    """Copy the current selection and read it aloud when it contains text."""
    if copy_selection() is False:
        return False
    text = get_clipboard_text().strip()
    if not text:
        return False

    speaker.speak(text)
    return True


def make_hotkey_handler(copy_selection, get_clipboard_text, speaker, report_status):
    """Create the action that runs whenever the reader hotkey is pressed."""
    def handle_hotkey():
        was_read = read_selected_text(copy_selection, get_clipboard_text, speaker)
        if was_read:
            report_status("Reading selected text...")
        else:
            report_status("No text is selected.")

    return handle_hotkey


def capture_selection(desktop, *, clock=time.monotonic, sleep=time.sleep):
    """Wait for released keys, then accept text only after a fresh clipboard update."""
    deadline = clock() + 2.0
    while desktop.keys_down():
        if clock() >= deadline:
            return ""
        sleep(0.01)

    before = desktop.clipboard_sequence()
    desktop.send_copy()
    deadline = clock() + 1.0
    while clock() < deadline:
        if desktop.clipboard_sequence() != before:
            return desktop.clipboard_text().strip()
        sleep(0.01)
    return ""


def run_reader_loop(desktop, speaker, *, report=print,
                    clock=time.monotonic, sleep=time.sleep):
    """Keep capture and speech on the main thread and always clean up on exit."""
    try:
        desktop.register()
        report("AI Chat Reader is running. Select text, press Alt + S, then release both keys.")
        report("Playback: Alt + P to pause/resume, Alt + X to stop speech.")
        report("Exit: Ctrl + C in this terminal, or Alt + Shift + Q anywhere.")
        while True:
            event = desktop.next_hotkey()
            if event == "quit":
                break
            if event in {"read", "pause", "stop"}:
                try:
                    if event == "pause":
                        state = speaker.toggle_pause()
                        report({
                            "paused": "Speech paused. Alt + P to resume.",
                            "resumed": "Speech resumed.",
                            "idle": "Nothing is currently being read. Select text and press Alt + S.",
                        }[state])
                        continue
                    if event == "stop":
                        speaker.stop()
                        report("Speech stopped. Select text and press Alt + S to read again.")
                        continue
                    text = capture_selection(desktop, clock=clock, sleep=sleep)
                    if not text:
                        report("No new text copied. Select text in the active app and try again.")
                        continue
                    preview = " ".join(text.split())[:100]
                    report(f"Reading: {preview}")
                    speaker.speak(text)
                except Exception as error:
                    report(f"Could not {'read this selection' if event == 'read' else 'control playback'}: {error}")
            sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            speaker.stop()
        finally:
            desktop.close()
        report("AI Chat Reader stopped.")
