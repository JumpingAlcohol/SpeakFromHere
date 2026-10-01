# AI Chat Reader

Your first Windows project: select text anywhere, then press **Alt + S** to have Windows read it aloud.

This is the MVP. It deliberately reads only selected text; later versions can use Windows UI Automation to recognize one Codex or ChatGPT reply and start at the paragraph under the cursor.

## Playback controls

| Shortcut | Action |
| --- | --- |
| `Alt + S` | Read the selected text, replacing current speech |
| `Alt + P` | Pause; press again to resume from the same position |
| `Alt + X` | Stop speech, keeping the reader running |
| `Alt + Shift + Q` | Exit the reader |
| `Ctrl + C` in the terminal | Exit the reader |

When paused, reading a new selection starts the new text immediately. Stopping clears the reading position; use `Alt + S` to start another selection. Pressing `Alt + P` when nothing is being read does nothing to the voice and prints a status message.

## How it works

1. You select text in Codex, ChatGPT, a browser, or another app.
2. Press `Alt + S` and release both keys. The reader waits for key release before sending `Ctrl + C`.
3. It checks that the clipboard was updated, displays a `Reading: ...` preview, and reads the new text with Windows speech.

If copying fails, it reports `No new text copied...` instead of reading old clipboard contents. The copy replaces your clipboard contents, just like copying normally.

## Run it

Requires Windows 10/11 and Python 3.11 or later. Speech uses a locally installed Windows SAPI voice; no API key or online speech service is required.

For a fresh clone, first create the virtual environment and install dependencies from the project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

If the Python launcher `py` is unavailable, use `python -m venv .venv` instead. The local environment used during development is not included in the repository.

Open PowerShell in this folder and run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m chat_reader.app
```

Keep the PowerShell window open while the reader is running. Press `Alt + S` after selecting text, then release both keys. Another press reads the new selection and replaces any current speech.

To exit, press `Ctrl + C` in the terminal (clear any terminal text selection first), or press **Alt + Shift + Q** from any app. The reader stops speech, releases its hotkeys, and prints `AI Chat Reader stopped.`

If an older version will not exit, use the trash-can icon on that VS Code terminal to close it, then open a new terminal and run the command above. Only run one reader instance at a time.

## First manual check

1. Start the reader. Select `Hello! This is my first Python project.` in the chat, not the terminal.
2. Press `Alt + S` and release both keys. Check that the terminal preview contains the sentence, then listen.
3. Select a different sentence and press the shortcut again; repeat a third time.
4. Press `Alt + Shift + Q`. Confirm `AI Chat Reader stopped.` and the terminal prompt returns.
5. Restart the reader and check `Ctrl + C` in the terminal also exits.

For playback controls, select a longer passage and start reading. Press `Alt + P` to pause, then again to continue. Press `Alt + X` to stop; the terminal should stay running. Select another passage and press `Alt + S` to read again. Also check starting a new selection while paused.

An app must support copying its selection with `Ctrl + C`. Windows also limits simulated input into apps running as administrator; try a normal window when diagnosing a failed copy.

## Test it

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The Windows integration tests are opt-in. Close any reader instance first so its global hotkeys are available, then run in a normal desktop terminal:

```powershell
$env:CHAT_READER_WINDOWS_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:\CHAT_READER_WINDOWS_TESTS
```

The integration tests use temporary audio files or mute only the test voice. They do not play audible speech or change system volume.

## Paragraph-to-reply reading: current status

The first live accessibility inspection on 2026-10-01 returned window containers but no chat text or message boundaries in the current desktop app. Paragraph-to-reply reading is not implemented yet. A working text source and verified message boundaries are required before this can be enabled; selected-text reading and playback controls work independently.
