# SpeakFromHere

[English](README.md) | [简体中文](README.zh-CN.md)

**Read AI responses aloud from exactly where you want.**

SpeakFromHere is a lightweight, reply-aware reader for **Windows desktop AI workflows**, currently focused on an inspected Codex desktop build. Point at a supported paragraph, press **Alt + E**, and listen from that paragraph's beginning to the end of the same completed AI reply. No need to drag-select the rest of the answer. For other copyable text, select it and press **Alt + S**.

“From exactly where you want” describes the product direction: the current preview starts at **paragraph boundaries**, not arbitrary words or sentences, and does not support every Codex/ChatGPT build.

## What makes SpeakFromHere different

- **Read from here, not necessarily from the top:** choose the paragraph you want to hear in a supported reply, rather than restarting the entire answer.
- **Reply-aware, not whole-screen narration:** verify one completed assistant reply's ownership and ending boundary instead of reading the entire window or unrelated controls.
- **Stay in the desktop workflow:** a standalone Windows tool, not a browser extension or a separate AI chat site.
- **Two deliberate paths:** mouse-and-hotkey paragraph reading, plus user-selected text as an explicit fallback. Failed copying never reads stale clipboard text.
- **Local speech by default:** Windows SAPI, no cloud voice key required. This is a design choice shared with other tools, not a claim of exclusive privacy or natural voices.

These highlights describe a focused workflow combination, not “first,” “only” or “best.” [codex-read-aloud](https://github.com/cobibean/codex-read-aloud) documents macOS/latest-message reading; [Echo](https://chromewebstore.google.com/detail/echo-read-x-chatgpt-subst/acmcamiebaibkbafoancpkdapcijoine) documents browser reply controls and clickable transcripts; [2lazy2read](https://2lazy2read.com/) documents Windows selected-text listening. Features overlap. See the [source-backed comparison](docs/COMPETITIVE_POSITIONING.md) and [brand definition](docs/BRAND.md).

This is an independent project, not an official OpenAI product. Delays, opening-audio loss and layout limitations are tracked in [known issues](docs/KNOWN_ISSUES.md). The v0.3.0 preview omits recognized nonreadable blocks with a visible notice; it does not blindly ignore every unknown structure.

## Preview status

v0.2.0 adds paragraph-to-reply reading for the inspected desktop build. Both source and portable modes have passed the user's manual checks. This remains a preview with a deliberately limited app/build scope; v0.1.0 is retained as the selected-text-only fallback.

Documentation and download instructions are available in English and Simplified Chinese. The new floating player has a persisted English/Chinese selector; console output and detailed diagnostics remain English.

**v0.3.0 — Floating Player & Bounded Skipping Preview** adds a terminal-free player, persisted bilingual settings and visible omission notices for recognized nonreadable blocks. Playback-delay/opening-audio reports remain open. `Alt + S` and `Alt + E` remain fixed; no other paragraph-reading apps are enabled.

[Download v0.3.0 preview](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.3.0) · [Previous v0.2.0](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.2.0) · [Previous v0.1.0](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.1.0) · [Version plan](docs/ROADMAP.md)

Formerly **AI Chat Reader**. The existing repository URL, Python distribution `ai-chat-reader`, module `chat_reader`, environment flags and `%LOCALAPPDATA%\AIChatReader\settings.json` are retained. Historical v0.1.0/v0.2.0 downloads keep their original names and files. New portable builds use `outputs/v0.3.0/SpeakFromHere/`; the repository has not been renamed.

## Floating player (v0.3.0 preview)

Extract the **entire ZIP**, keeping `reader-worker/` next to the two main executables, and double-click `SpeakFromHere.exe`: a compact, always-on-top player opens at the bottom right of the current monitor's work area, above the taskbar. No terminal is required. Drag its title to move it. Close any other reader first. Do not move only the exe: paragraph reading requires the helper folder.

- Start new text with `Alt + S`, or point at a supported paragraph and press `Alt + E`. The player does not guess a new selection when clicked.
- The main button pauses/resumes current speech. When idle, it replays the last successfully submitted text from the beginning; before the first read it is disabled. Stop cancels speech but leaves that text in memory for replay. Closing the app clears it; no reading history is saved.
- `−` / `+` adjust SAPI rate (-10..10), displayed as slow/normal/fast, not exact multipliers. Changes are submitted immediately without restarting speech. The user reports gradual mid-playback changes with the current voice; audible timing depends on voice/buffering and is not independently measured. Do not promise instant universal changes or next-playback-only behavior.
- `中文` / `EN` switches and saves interface language. `⚙` edits pause/stop/exit keys; restart to activate new bindings. Reset requires confirmation and replaces saved preferences.
- `—` hides to the notification area; click the tray icon to restore. `×` exits, stops speech and releases shortcuts. Normal player buttons do not activate the window; the settings dialog intentionally accepts focus for typing.
- On an error/warning, **Details** opens the complete, selectable English message instead of the two-line preview. It does not automatically copy, save or upload anything. Identity-query errors include the failing Windows API and numeric error code; share only that error when diagnosing refusal.

An amber **Skipped …** notice discloses omitted types/counts, including omissions before your starting paragraph. **Details** lists ordered reply-block numbers and whether each is before the start or in the remaining reply. No skipped text or file names enter the notice; it is memory-only. Pause/replay preserve it and a new read replaces it. Block numbers are not screen coordinates. This is not original-text highlighting or synchronized progress tracking.

This preview does not add login startup, new voices, sentence seeking or original-text highlighting. The user confirmed editable-block and edited-files skipping. A real table-widget refusal was traced to its grid/overlay container and standalone footer controls; narrow fixes have regression coverage, and the user reports ordinary/table reading works after updating Codex. See [release notes](docs/releases/v0.3.0.md).

## Playback controls

| Shortcut | Action |
| --- | --- |
| `Alt + S` | Read the selected text, replacing current speech |
| `Alt + P` | Pause; press again to resume from the same position |
| `Alt + X` | Stop speech, keeping the reader running |
| `Alt + Shift + Q` | Exit the reader |
| `Ctrl + C` in console mode | Exit the reader |
| `Alt + E` (portable / source `--gui` or `--paragraphs`) | Read from the paragraph under the mouse to its AI reply's end |

When paused, a new read replaces the paused utterance. Stopping clears the position; the GUI Play button can replay the last text from the beginning. `Alt + P` while idle does not replay it.

## How it works

1. You select text in Codex, ChatGPT, a browser, or another app.
2. Press `Alt + S` and release both keys. The reader waits for key release before sending `Ctrl + C`.
3. It checks that the clipboard was updated, displays a `Reading: ...` preview, and reads the new text with Windows speech.

If copying fails, it reports `No new text copied...` instead of reading old clipboard contents. The copy replaces your clipboard contents, just like copying normally.

## Run it

### Portable Windows executable

Double-click the new `SpeakFromHere.exe` for the floating GUI. Python, Tk and dependencies are included. `SpeakFromHereConsole.exe` is a separate advanced console entry for diagnostics/settings commands; do not run both at once.

Both new portable entries enable `Alt + E` by default. Current builds are in `outputs/v0.3.0/SpeakFromHere/`; previous artifacts remain separate. The v0.1.0 download remains selected-text only.

The ZIP includes `SpeakFromHere.exe`, `SpeakFromHereConsole.exe`, `QuickStart.en.txt` and `QuickStart.zh-CN.txt`. Extract before running. Generated binaries stay in ignored `outputs/`, not Git.

### Run from source

Requires Windows 10/11 and Python 3.11 or later. Speech uses a locally installed Windows SAPI voice; no API key or online speech service is required.

The GUI also requires Python's optional Tkinter component (included in typical Windows Python installers) and the paragraph extra. After setup, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\pythonw.exe -m chat_reader.app --gui
```

`pythonw.exe` starts the GUI without a console. Use `python.exe` with `--gui` for development, or the existing console commands below.

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

To exit, press `Ctrl + C` in the terminal (clear any terminal text selection first), or press **Alt + Shift + Q** from any app. The reader stops speech, releases its hotkeys, and prints `SpeakFromHere stopped.`

If an older version will not exit, use the trash-can icon on that VS Code terminal to close it, then open a new terminal and run the command above. Only run one reader instance at a time.

## First manual check

For the GUI, first read three different selections with `Alt + S`, click Pause/Resume and Stop/Play, change rate then start new text, toggle language and restart, hide/restore from the tray, and exit with `×`. Recheck first/middle/last paragraph starts with `Alt + E` in the inspected app. Listen for opening characters and note existing delays; automated silent tests cannot validate these. Console checks follow.

1. Start the reader. Select `Hello! This is my first Python project.` in the chat, not the terminal.
2. Press `Alt + S` and release both keys. Check that the terminal preview contains the sentence, then listen.
3. Select a different sentence and press the shortcut again; repeat a third time.
4. Press `Alt + Shift + Q`. Confirm `SpeakFromHere stopped.` and the terminal prompt returns.
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

`CHAT_READER_GUI_TESTS=1` enables native player/tray tests. `CHAT_READER_UIA_TESTS=1` and `CHAT_READER_PORTABLE_TESTS=1` enable isolated UIA/bundle checks. Close the reader, enable the desired flags, run the suite, then clear them. GUI tests create only their own windows and temporary profiles, not private app captures.

## Build the Windows executable

On Windows, after creating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\scripts\build.ps1
```

Outputs are in `outputs/v0.3.0/SpeakFromHere/`: windowed `SpeakFromHere.exe`, advanced `SpeakFromHereConsole.exe`, `reader-worker/`, `SpeakFromHere-Windows-x64.zip` and `SHA256SUMS.txt`. No separate Python installation is needed. The ZIP includes both entries, the complete capture-helper runtime and canonical guides from `docs/`. Both entries launch the same lightweight helper without a terminal or another player, avoiding repeated unpacking/loading of the full reader. Extract and keep the whole folder together. Intermediate files stay in `work/`.

The build uses [PyInstaller](https://pyinstaller.org/en/stable/usage.html): single-file main entries, a one-directory capture helper.

Build in a normal Windows desktop environment with usable Tcl/Tk. The spec refuses to proceed if Tk cannot be detected, rather than shipping a missing-GUI bundle. After a restricted/failed build, use `scripts/build.ps1 -Clean` to refresh caches.

To check the built executable in isolation, close any running reader and run:

```powershell
.\scripts\test-executable.ps1
```

This checks the console entry twice with isolated settings and actual OS hotkey ownership. Opt-in `tests/test_portable_gui.py` separately starts the standalone GUI twice, verifies its visible nonactivating window and no console, sends controls only to that owned window, and verifies exit/key release and ZIP contents. `tests/test_portable_worker.py` checks the standalone windowed worker's UIA and redirected pipes. None replace real-chat/audio acceptance or change personal preferences.

## Reading settings (v0.2.1, extended in v0.3.0)

The GUI controls rate/language and provides a settings dialog; commands remain available for advanced use.

Close the running reader first. From the project folder:

```powershell
.\.venv\Scripts\python.exe -m chat_reader.app --show-settings
.\.venv\Scripts\python.exe -m chat_reader.app --set-rate 2 --set-hotkey 'pause=Alt+J'
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

Or open PowerShell in the extracted portable folder:

```powershell
.\SpeakFromHereConsole.exe --show-settings
.\SpeakFromHereConsole.exe --set-rate 2 --set-hotkey 'pause=Alt+J'
.\SpeakFromHere.exe
```

Settings commands save/show and exit without starting speech, capture or hotkeys. Changes apply on restart, not to running instances. The integer rate is -10 (slow) to 10 (fast), default 0, not a speed multiplier; actual differences depend on the voice. See [Microsoft SAPI Rate](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723606(v=vs.85)).

Only `pause`, `stop` and `exit` bindings can change, using `Alt+LETTER` or `Alt+Shift+LETTER` (A-Z). Repeat `--set-hotkey` to update multiple controls together. Duplicate/unsupported keys and conflicts with fixed `Alt+S` / `Alt+E` are rejected before saving. No live rebinding. Startup displays the effective controls: use those instead of the default keys in the checks above. Another app may occupy a valid binding; startup names that conflict, releases acquired keys and exits rather than silently disabling a control.

Source and portable versions share `%LOCALAPPDATA%\AIChatReader\settings.json`. Schema 2 adds `language` to rate and control bindings; no chat text or credentials are saved. Existing schema-1 files load unchanged and upgrade only on explicit save. **Back up settings before switching versions:** v0.2.1 does not understand schema 2 and falls back to defaults with a warning. Saves are atomic. Missing files use defaults without creating a file. Invalid/unreadable files are preserved with warning/default startup; direct updates are refused. After backing up, explicitly confirm GUI Reset or use `--reset-settings` to replace them. `--settings-file PATH` selects an isolated profile, without changing paragraph scope.

To check customized settings: save rate 2 and pause `Alt+J`, restart, verify startup feedback and audible rate, use the new pause/resume key, repeat selection and first/middle/last paragraph reads, then stop/exit and restart. Unsupported content must still report “Use Alt + S” without copying/speaking automatically. Restore defaults with `--reset-settings` if desired.

Paragraph startup and collection now run off the control thread, with coordinates sampled when the command is handled. Pause/stop/new reads cancel even a pending process launch; late children are reaped and stale results are ignored. The 20-second deadline includes launch time. Exit releases controls first but process shutdown may wait briefly for a pending native launch to return so its child can be cleaned up. This does not establish a fix for SAPI or selected-text pause/start delays.

Open user feedback: Alt+S playback can also start late, pauses are frequently delayed, and first playback may omit opening characters; causes are unconfirmed. The v0.3.0 preview skips recognized nonreadable regions with an omission notice. Unknown/protected/boundary-ambiguous structures can still reject the reply. See [known issues and acceptance requirements](docs/KNOWN_ISSUES.md). The user confirmed tested ordinary/table/editor/file workflows after a Codex update; separate audio reports and uninspected layouts remain open.

The v0.3.0 preview corrects a GUI/worker display-scaling coordinate mismatch that could target a different application and report an identity error. Cursor sampling, UIA point lookup and paragraph bounds use the same physical-pixel coordinate space without changing Windows scaling or relaxing identity checks. Native regression coverage includes the development machine's scaled desktop; the user confirmed GUI paragraph reading was restored. Playback reports and uninspected-layout limitations remain open.

## Paragraph-to-reply reading: current status

On 2026-10-01, the user confirmed first/middle/last paragraph starts, same-reply ending, switching starts/replies and controls in source and portable modes. That historical preview rejected tables/editors. On 2026-10-02, the user confirmed tested ordinary/table/editor/file workflows after a Codex update; the exact updated package version was not captured. Broader app, machine and language compatibility has not been established.

The v0.3.0 package passed isolated startup/control/exit runs and bundled-UIA verification. All 190 tests passed with the Windows/GUI/UIA/portable opt-ins enabled; embedded GUI/console checks passed 90 each and helper checks passed 66. Both ZIP guides match their canonical sources and the archive checksum was verified. No captured private chats are included. These checks do not establish broader machine or audio compatibility.

### Run the paragraph preview from source

Close the existing reader first. From the project folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

Keep the target window visible and point at ordinary text in a completed assistant reply, without selecting or clicking. Press `Alt + E` and keep the mouse still until capture finishes. It should start at the beginning of that paragraph and stop at the end of the same reply. Moving the mouse alone does not trigger speech. Try the first, middle and last paragraph, then another reply, and confirm repeated reads, pause/resume, stop, exit and `Alt + S` still work.

Scope and safeguards:

- The v0.3.0 preview verifies Windows-reported package family `OpenAI.Codex_2p2nqsd0c76g0` and that the captured process is the registered package's `app/ChatGPT.exe`. Numeric version alone no longer rejects an update; the inspected reply structure must still pass every capture, ownership, paragraph and completion check. Different apps, unpackaged/lookalike executables and changed/unsafe layouts remain unsupported. This is not universal Codex/ChatGPT/browser compatibility. Older downloads retain their original exact-version gate. See [application compatibility](docs/APP_COMPATIBILITY.md). Chinese interface structure has local captures; English markers have synthetic coverage only.
- Ordinary paragraphs, headings, inline text/links and recognized list items are handled. A list item is a starting block; code blocks and verified non-text leaf separators are skipped. Hovering code, separators, user messages, buttons or input fields is rejected.
- Recognized Table (50036) blocks, the inspected `group/app-widget` table container with a typed grid and bounded action overlay, the known `group/writing-block-surface` editor wrapper, inspected collapsed edited-files summaries with contiguous rows, and simple post-Copy activity status containers are omitted without reading their contents. Code omissions are also disclosed. The tested editor/file skips are user-confirmed; ordinary/table reading is also user-confirmed after a Codex client update. Expanded/changed regions may still reject. Pointing at any skipped block does not advance to another paragraph; use `Alt + S` on a copyable selection.
- Known standalone Regenerate/More footer buttons are ignored only as unprotected, correctly styled leaves after the same reply's verified Copy footer; they do not prove completion. Their Chinese labels were inspected locally; English counterparts have synthetic coverage only. Unknown buttons or hidden descendants still reject.
- Unknown/protected structures, ambiguous ownership, generating replies and incomplete captures still reject; Alt+E never automatically copies. Skip types cannot prove completion, hide nested reply markers or cross into the next reply.
- A newer reply generating does not veto an earlier reply when its own completion footer and a later assistant marker in the same transcript are verified. The current generating reply remains unavailable; this is not general unsupported-block skipping.
- After a verified same-reply Copy footer, plain 24-hour clocks and weekday-prefixed clocks such as `星期四23:43` / `Thursday 23:43` are recognized as metadata, not speech or starting paragraphs. Only unprotected text leaves qualify; unknown blocks still reject. Chinese labels were inspected locally; full English weekday names have synthetic tests only. Abbreviations, AM/PM and other uninspected date formats are not assumed compatible.
- Capture uses physical screen coordinates and a separate process with a 20-second timeout. A new read replaces a pending capture; pause, stop and exit cancel it so a late result cannot restart speech. The existing voice continues while a new capture is pending, unless you stop or pause it.
- Paragraph capture does not click, copy, save a chat file or upload text. Text is held locally in memory and read with Windows SAPI. Only the separate inspection command below saves a private diagnostic JSON. The terminal preview is limited to 100 characters; the extracted suffix is spoken in full.

Source mode without `--paragraphs` keeps the normal MVP behaviour and does not register `Alt + E`. The v0.3.0 portable entries enable paragraph reading by default; the older v0.1.0 download does not support it.

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

This tests the legacy internal windowed worker and the new complete helper runtime from isolated temporary folders, briefly shows a synthetic test-owned window without activating it, and verifies unsupported-app rejection without starting speech or another reader. It never inspects private chat or other applications. Restricted sandboxes can block cross-process UIA; run this check in the normal desktop environment. It does not replace the portable app's real-chat/audio check.
