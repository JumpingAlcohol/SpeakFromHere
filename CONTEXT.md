# SpeakFromHere — project handoff

## Current milestone / 当前状态

2026-10-02: v0.3.1 preview published with explicit user authorization: https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.3.1 . Release ID 402300877, tag/source commit ffdd309c88a787c80e8e032543259905815d662b. All four public assets re-downloaded and hash-verified; notes match tagged source. Historical v0.1.0/v0.2.0/v0.3.0 IDs, notes, assets and tag refs verified unchanged. Final source/portable checks pass; runtime unchanged from user-accepted candidate. Later handoff-only commits do not move the release tag.

用户验收后明确授权，v0.3.1 预览版现已公开发布。四个附件重新下载校验一致，旧版标签／说明／附件未改。最终源码和便携检查通过；后续交接文档提交不移动发布标签。首读提示音是暂时方案，不是所有设备／长时间闲置吞字的全面修复。

## Product and invariants

- Brand: SpeakFromHere. Read docs/BRAND.md and docs/COMPETITIVE_POSITIONING.md; follow AGENTS.md. Paragraph-start listening to the same completed assistant reply's end, not arbitrary-character seeking or universal compatibility.
- Preserve legacy repository/distribution ai-chat-reader, module chat_reader, environment flags and LOCALAPPDATA/AIChatReader/settings.json. No credentials/private chat/binaries in Git; work/ and outputs/ are ignored.
- Alt+S: selected copyable text, never stale clipboard. Alt+E: hovered supported paragraph; no automatic clipboard fallback. GUI/portable enable paragraphs; source console requires --paragraphs.
- Defaults: Alt+P pause/resume, Alt+X stop, Alt+Shift+Q exit; terminal Ctrl+C exits. S/E fixed; other controls configurable. One reader instance at a time.
- Trust Windows-reported OpenAI.Codex_2p2nqsd0c76g0 family and registered app/ChatGPT.exe, then inspected reply structure. Numeric version alone does not veto. No guessed path, identity bypass or elevation. Other apps require separately inspected adapters; see docs/APP_COMPATIBILITY.md.
- Ordinary paragraphs/headings/recognized lists/inline links readable. Recognized code/table/editor/collapsed edited-files/status regions skipped with omission disclosure. Unknown/protected/expanded/ambiguous layouts, incomplete captures, user messages and current generating reply reject. Earlier completed replies need verified ownership/footer/later assistant marker.
- GUI omission notice counts kinds across the reply; Details lists ordered blocks and before-start/remaining flags, not omitted text/files/coordinates. Notice survives pause/replay, clears for selection. No automatic capture/upload. This is not synchronized highlighting.
- English primary README and complete aligned Chinese README; canonical bilingual QuickStarts copied into ZIP. GUI language persists; console/diagnostics English. Settings schema 2: rate -10..10, controls, language; atomic local save without chat data. Schema 1 migrates only on save; v0.2.1 rejects schema 2 downgrade. Corruption needs explicit reset.
- Dark draggable, nonactivating, topmost player above taskbar; settings may focus. Play toggles/replays in-memory last text; stop retains replay; exit clears it. Tray/× release keys. No login-startup/sentence navigation.

## Architecture and audio change

- app.py and gui.py share create_windows_speaker; main-thread dynamic comtypes SAPI. windows_audio.py retrieves native ISpMMSysAudio GetMMHandle with pointer-sized handles. Waveform pause/restart retains queued audio/position; paused cancellation resets owned buffers before SAPI purge. Non-waveform/unopened output falls back to SAPI. Never close borrowed handles, change SpAudio state or system volume/default device.
- StartupCue lazily queues one soft faded 400 ms/660 Hz PCM stream before first nonempty read per launch. SpeakStream flags 3, first plain text flags 17 (no cue purge), later flags 19. Retain stream lifetime; explicitly scale voice.Volume because SpeakStream bypasses it. Launch/settings/empty/failed captures silent; resume/replay/later reads do not repeat. Text errors cancel queued cue without replacing successful replay text.
- core.py controls/selected capture/ReadingPlan; read/play/pause/stop/exit cancels pending paragraph results. paragraphs.py validates immutable text/skipped payloads; old text-only wrappers remain.
- windows_context.py uses same-handle package/executable verification and temporary thread PER_MONITOR_AWARE_V2 for physical pointer/UIA, restoring afterward. No guessed scaling or process/Tk scaling changes.
- uia_probe.py is bounded/password-redacted; inspect_paragraph.py is diagnostic only. verified_reply: False there is not a playback verdict. codex_adapter.py validates assistant markers, geometry, completion Copy footer and bounded skip shapes.
- paragraph_job.py/worker: fresh capture, off-control-thread startup/collection, startup-inclusive 20s deadline, pipe draining/cancellation. Portable GUI/console share full neighboring reader-worker/ runtime; source pythonw uses neighboring python.exe. Missing helper asks for full extraction, never relaunches reader. Non-daemon cleanup can briefly delay exit after controls release.
- GUI HWND-bound hotkeys and WS_EX_NOACTIVATE preserve focus; shared controls and bilingual dictionaries. No new settings schema/UI in v0.3.1.

## Verification and open limits

- Final v0.3.1: 199 Windows/GUI/UIA/portable opt-in tests pass, no skips; default 199 with 31 opt-in skips. Actual embedded GUI/console 99 each, helper 66, all pass. Two portable startup/idle-control/stop/exit runs verify actual shortcut ownership/release. Full ZIP/helper/canonical guides, pip check, compileall and diff check pass.
- Final ZIP SHA256: 32beeff511fe873e294e828f2d2e3f2fe466e28a765f5c5ceb0987d1b9fde629. v0.3.0 local ZIP unchanged: fd432b3b8feb96aec02c3e526a9f23c3f90d6458f4a37168e0a85728313548d0. Candidate/historical evidence remains ignored locally or in release notes/KNOWN_ISSUES.md.
- Pause reproduction: SAPI API returned 0.01–0.29ms while muted native output kept advancing ~648–1798ms. Waveform calls ~1–9ms held position; four native regressions first failed then passed. Paused reset-before-purge avoids writer deadlock/old replay. No zero-delay/all-device guarantee.
- First-read evidence: fresh A/B/B/A all lost opening syllable, including 350ms silence; same WAV first lost it, repeat complete; no-initial-purge also failed. 400/800ms same-output audible cue trials preserve it; user approved 400ms and accepted candidate workflow. Missing-cue, text-error cancellation and muted-volume regressions failed then passed. No hardware cause, recording or long-idle remedy established.
- ISSUE-002: user accepts inspected ordinary/table/editor/file skipping after Codex update; precise new package version not recorded. Tables are omitted, not narrated. Boundary safety is unchanged, not unconditional unknown-node skipping.
- ISSUE-004: owned-window reproduction proved physical-coordinate mismatch caused GUI-only identity error; scoped DPI fix accepted by user, temporary tracing removed.
- ISSUE-003: shared helper ~1.07–1.14s vs old GUI internal capture ~2.11–3.05s on small owned windows, not a real-chat speed/audio guarantee.
- ISSUE-006: Chinese weekday footer accepted; full English weekday labels synthetic-tested only. Abbreviations/AM-PM/uninspected relative dates unsupported.
- ISSUE-007: real 960-node inspection/in-memory differential confirms compaction-status shape; narrow skip implemented/tested. Dedicated post-fix real capture remains pending.
- Development-machine Windows 11 x64 evidence, not broad platform/client support. Normal desktop approval, not admin/UAC, for COM/UIA; restricted execution may give false negatives. Native GUI suites serially, own test processes/settings/voices only. No user-reader kills, audio recording, private fixtures or system device/volume changes.

## Commands and artifacts

~~~powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --show-settings
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
.\.venv\Scripts\pythonw.exe -m chat_reader.app --gui
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\build.ps1 -Clean
.\scripts\test-executable.ps1
~~~

- Opt-ins: CHAT_READER_WINDOWS_TESTS, CHAT_READER_GUI_TESTS, CHAT_READER_UIA_TESTS, CHAT_READER_PORTABLE_TESTS = 1; clear afterward. Speech tests mute own voice or render temporary WAV.
- Current output: outputs/v0.3.1/SpeakFromHere/, separate from older outputs. GUI/console exe + complete reader-worker/ + both guides + ZIP/SHA256SUMS. Extract entire ZIP. Build requires working Tcl/Tk; no GUI-less output.
- Public repository: https://github.com/JumpingAlcohol/ai-chat-reader . Reverify Git/remote/tag/assets before publishing; user explicitly authorized this v0.3.1 release. Four assets: ZIP, SHA256SUMS, both QuickStarts. Frozen public historical metadata remains ignored in work/.

## Next priority

v0.3.1 publication/verification complete; do not republish or move its tag. Next: v0.4.0 local Windows voice selection first, optional alternative backend later. Cloud provider/text transmission/cost requires explicit choice; no auto-upload/API-key requirement. Highlighting follows separate audible-position/scrolling/DPI/cancellation/privacy design. More natural voices and synchronized original-text coloring are not implemented. Fix further layouts only when reproduced and safely bounded.
