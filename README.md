# AI Chat Reader

[English](README.md) | [简体中文](README.zh-CN.md)

A lightweight Windows reader for selected text, designed for listening to long AI chat replies. Select text and press **Alt + S** to read it aloud.

v0.2.0 adds paragraph-to-reply reading for the inspected desktop build. Both source and portable modes have passed the user's manual checks. This remains a preview with a deliberately limited app/build scope; v0.1.0 is retained as the selected-text-only fallback.

Documentation and download instructions are available in English and Simplified Chinese. Runtime status messages currently use English; an in-app language selector is not implemented yet.

[Download v0.2.0 preview](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.2.0) · [Previous v0.1.0](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.1.0) · [Version plan](docs/ROADMAP.md)

## Playback controls

| Shortcut | Action |
| --- | --- |
| `Alt + S` | Read the selected text, replacing current speech |
| `Alt + P` | Pause; press again to resume from the same position |
| `Alt + X` | Stop speech, keeping the reader running |
| `Alt + Shift + Q` | Exit the reader |
| `Ctrl + C` in the terminal | Exit the reader |
| `Alt + E` (v0.2.0 portable preview; source with `--paragraphs`) | Read from the paragraph under the mouse to its AI reply's end |

When paused, reading a new selection starts the new text immediately. Stopping clears the reading position; use `Alt + S` to start another selection. Pressing `Alt + P` when nothing is being read does nothing to the voice and prints a status message.

## How it works

1. You select text in Codex, ChatGPT, a browser, or another app.
2. Press `Alt + S` and release both keys. The reader waits for key release before sending `Ctrl + C`.
3. It checks that the clipboard was updated, displays a `Reading: ...` preview, and reads the new text with Windows speech.

If copying fails, it reports `No new text copied...` instead of reading old clipboard contents. The copy replaces your clipboard contents, just like copying normally.

## Run it

### Portable Windows executable

If you have a built `AIChatReader.exe`, double-click it. Python and dependencies are included. Keep its status window open or minimized and use the shortcuts above. Close any reader already running in a Python terminal before starting the executable.

The v0.2.0 preview enables `Alt + E` by default. Local builds are in `outputs/v0.2.0/`; the v0.1.0 download remains selected-text only. These versions are kept separate so the previous working files are not overwritten.

The portable ZIP includes `AIChatReader.exe`, `QuickStart.en.txt` and `QuickStart.zh-CN.txt`. Extract it before running. The binary is produced locally in `outputs/`; generated binaries are not checked into Git.

### Run from source

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

## Build the Windows executable

On Windows, after creating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\scripts\build.ps1
```

The outputs are `outputs/v0.2.0/AIChatReader.exe` and `outputs/v0.2.0/AIChatReader-Windows-x64.zip`, with a ZIP checksum in `SHA256SUMS.txt`. The ZIP includes the executable and both quick-start guides, copied from `docs/`. The build bundles one executable with Windows speech, UI Automation bindings and global shortcuts. Its internal capture worker runs without starting another reader or registering hotkeys. Temporary build files stay in `work/`.

The build uses [PyInstaller's single-file packaging](https://pyinstaller.org/en/stable/usage.html).

To check the built executable in isolation, close any running reader and run:

```powershell
.\scripts\test-executable.ps1
```

This copies only the executable into a fresh test directory, starts it twice with hidden windows, checks idle pause, stop and graceful exit through its Windows message queue, and confirms hotkeys can be registered again after exit. It does not replace the manual selected-text-and-audio check.

## Paragraph-to-reply reading: current status

On 2026-10-01, the user confirmed source-mode checks: first/middle/last paragraph starts, stopping at the same reply's end, changing reply/paragraph, repeated reading, pause/resume, stop, exit and selected-text fallback all worked in the inspected desktop app. The user then confirmed the portable executable also worked. Tables, editable writing blocks, user messages and other apps remain outside paragraph-reading scope, as expected. Automated tests and offline structure replay also pass. Broader app, machine and language compatibility has not been established.

The local package passed two isolated startup/control/exit runs, standalone bundled-UIA verification, and the full 88-test suite with Windows integration checks enabled. Both ZIP guides match their canonical sources and the archive checksum was verified. No captured private chats are included.

### Run the paragraph preview from source

Close the existing reader first. From the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

Keep the target window visible and point at ordinary text in a completed assistant reply, without selecting or clicking. Press `Alt + E` and keep the mouse still until capture finishes. It should start at the beginning of that paragraph and stop at the end of the same reply. Moving the mouse alone does not trigger speech. Try the first, middle and last paragraph, then another reply, and confirm repeated reads, pause/resume, stop, exit and `Alt + S` still work.

Scope and safeguards:

- The prototype accepts only the inspected desktop package `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0` (`app/ChatGPT.exe`). An app update, a browser or another build is rejected until inspected. This is not general ChatGPT/browser support. Chinese interface structure was captured locally; English markers are covered only by synthetic tests.
- Ordinary paragraphs, headings, inline text/links and recognized list items are handled. A list item is a starting block; code blocks are skipped. Hovering code, user messages, buttons or input fields is rejected.
- Replies containing editable writing blocks, tables or unknown structures are currently rejected rather than partly read. Use `Alt + S` for them. Generating replies, ambiguous hit locations and incomplete captures also report a reason without falling back to stale clipboard text.
- Capture uses physical screen coordinates and a separate process with a 20-second timeout. A new read replaces a pending capture; pause, stop and exit cancel it so a late result cannot restart speech. The existing voice continues while a new capture is pending, unless you stop or pause it.
- Paragraph capture does not click, copy, save a chat file or upload text. Text is held locally in memory and read with Windows SAPI. Only the separate inspection command below saves a private diagnostic JSON. The terminal preview is limited to 100 characters; the extracted suffix is spoken in full.

Source mode without `--paragraphs` keeps the normal MVP behaviour and does not register `Alt + E`. The local v0.2.0 executable enables paragraph reading by default; the older v0.1.0 download does not support it.

### Inspect a real paragraph

From the project folder, install the optional inspection dependency, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.inspect_paragraph
```

Within five seconds, move the mouse onto an ordinary paragraph in a completed AI reply. Do not click or select text. Keep that application visible, with no other window covering the paragraph. The command samples the mouse position, reads accessibility structure and saves `work/paragraph-probe.json`. It does not change the clipboard, click, speak, register hotkeys or upload data.

The local JSON contains app text: keep it private, do not upload it, and never commit it. `work/` is ignored. The terminal prints only capture status, not the captured chat. Ordinary noneditable containers can use UIA's default password status when the provider omits that property. Password fields and controls with unknown password status are redacted, their children are skipped and the capture is marked incomplete; pointing directly at them is rejected. A subtree size/depth/time limit also marks or rejects incomplete captures; native inspection runs in a separate process with a 20-second timeout. `verified reply: False` is expected: diagnostic data is not proof of supported paragraph reading.

The probe always reports `verified reply: False`: it is a generic diagnostic, not a playback verdict. Use `--paragraphs` for the separate experimental playback adapter; the probe itself never enables hotkeys.

To check native UIA against a test-owned hidden window, without inspecting other applications:

```powershell
$env:CHAT_READER_UIA_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_uia_windows.py -v
Remove-Item Env:\CHAT_READER_UIA_TESTS
```

Implementation references: [Microsoft UIA point lookup](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomation-elementfrompoint), [UIA screen coordinates](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-screenscaling), [UIA element properties](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids) and [comtypes client documentation](https://comtypes.readthedocs.io/en/stable/client.html).

After building, check the bundled worker in a normal desktop terminal:

```powershell
$env:CHAT_READER_PORTABLE_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_portable_worker.py -v
Remove-Item Env:\CHAT_READER_PORTABLE_TESTS
```

This copies only the executable to a temporary folder, briefly shows a synthetic test-owned window without activating it, and verifies that the bundled UIA worker rejects this unsupported app without starting speech or another reader. It never inspects private chat or other applications. Restricted sandboxes can block cross-process UIA; run this check in the normal desktop environment. It does not replace the portable app's real-chat/audio check.
