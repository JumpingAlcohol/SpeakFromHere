import time
import json
from chat_reader.settings import Settings
from chat_reader.paragraphs import ReadingPlan


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


def run_reader_loop(desktop, speaker, *, report=print, paragraph_reader=None,
                    clock=time.monotonic, sleep=time.sleep, settings=None):
    """Keep capture and speech on the main thread and always clean up on exit."""
    settings = settings or Settings()
    pause, stop, exit_key = (settings.hotkeys[action] for action in ("pause", "stop", "exit"))
    try:
        desktop.register()
        report("SpeakFromHere is running. Select text, press Alt + S, then release both keys.")
        report(f"Rate: {settings.rate} (local Windows voice).")
        report(f"Playback: {pause} to pause/resume, {stop} to stop speech.")
        report(f"Exit: Ctrl + C in this terminal, or {exit_key} anywhere.")
        if paragraph_reader is not None:
            report("Experimental paragraphs: point at ordinary completed reply text and press Alt + E.")
        while True:
            event = desktop.next_hotkey()
            if event == "quit":
                break
            if event in {"read", "pause", "play", "stop", "paragraph", "preview"}:
                try:
                    if paragraph_reader is not None:
                        paragraph_reader.cancel()
                    if event == "paragraph":
                        if paragraph_reader is None:
                            report("Paragraph reading is not enabled. Use Alt + S.")
                        else:
                            paragraph_reader.start(desktop.pointer_position())
                            report("Checking paragraph... Playback controls remain available.")
                    elif event == "preview":
                        speaker.preview_voice()
                        report("Voice preview: local synthetic sample; previous reply retained for replay.")
                        continue
                    elif event in {"pause", "play"}:
                        state = speaker.play_pause() if event == "play" else speaker.toggle_pause()
                        report({
                            "paused": f"Speech paused. {pause} to resume.",
                            "resumed": "Speech resumed.",
                            "replaying": "Replaying last text.",
                            "idle": "Nothing is currently being read. Select text and press Alt + S.",
                        }[state])
                        continue
                    elif event == "stop":
                        speaker.stop()
                        report("Speech stopped. Select text and press Alt + S to read again.")
                        continue
                    else:
                        text = capture_selection(desktop, clock=clock, sleep=sleep)
                        if not text:
                            report("No new text copied. Select text in the active app and try again.")
                            continue
                        preview = " ".join(text.split())[:100]
                        report(f"Reading: {preview}")
                        speaker.speak(text)
                except Exception as error:
                    action = {"read": "read this selection", "paragraph": "read this paragraph"}.get(event, "control playback")
                    fallback = " Use Alt + S for selected text." if event == "paragraph" else ""
                    report(f"Could not {action}: {error}{fallback}")
            if paragraph_reader is not None:
                try:
                    result = paragraph_reader.poll()
                    if result is not None:
                        text, error = result
                        if error:
                            report(f"Could not read this paragraph: {error} Use Alt + S for selected text.")
                        else:
                            plan = text if isinstance(text, ReadingPlan) else None
                            if plan is not None:
                                text = plan.text
                            preview = " ".join(text.split())[:100]
                            report(f"Reading paragraph: {preview}")
                            if plan is not None:
                                report("Skipped content: " + json.dumps(plan.to_payload()["skipped"]))
                            speaker.speak(text)
                except Exception as error:
                    report(f"Could not read this paragraph: {error} Use Alt + S for selected text.")
            sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if paragraph_reader is not None:
                paragraph_reader.close()
        finally:
            try:
                speaker.stop()
            finally:
                desktop.close()
        report("SpeakFromHere stopped.")
