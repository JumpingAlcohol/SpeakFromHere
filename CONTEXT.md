# SpeakFromHere — project handoff

## Current milestone / 当前状态

2026-10-04: user explicitly authorized committing/publishing v0.4.0 local SAPI voice selection, then developing reading-position visualization. Alternative/open-source/online backends are deferred. Final release checks pass 225 opt-in tests (no skips), actual embedded GUI/console 125 each, helper 66, ZIP/canonical guides and two portable startup/control/exit runs. Publication is prepared, not yet confirmed. GUI stable-ID dropdown/save-and-preview; stopped speech switches. Preview cancels pending capture, uses controls, retains reply replay/omissions. No language auto-switch, installation, registry workaround or online speech. User confirms tested English listening/restart retention and reports candidate works normally; no broader voice/app guarantee.

当前阶段：用户已授权先提交并发布 v0.4.0 本机声源选择，再开发阅读位置可视化；发布准备中，不提前宣称成功。其他声源后端暂缓，不代表声音自然化。设置升级 schema 3，旧 schema 1／2 读取不改写；保存／降级前备份，v0.3.1 不认识 schema 3。验收使用独立配置，不修改用户默认偏好。

Listening feedback 2026-10-04: user confirms English-voice English reading and, when asked directly, retention of the selected voice after exit/reopen. English-voice Chinese reading is unsupported in their observed test, not paragraph extraction failure or multilingual support. These checks do not separately confirm current Alt+E/all controls. Language-matched preview remains proposed, not implemented; the candidate still uses a fixed bilingual sample. No commit/push/release requested by these confirmations.
听感记录：用户确认英文声源读英文正常，并明确确认退出重开后仍记住所选声源，随后反馈候选流程“正常”。英文声源不能读中文属于观察到的语言限制；不代表所有声源／应用支持。按声源语言生成试听样句仍为建议，当前是固定双语样句；本次确认不包含提交／发布授权。

Historical publication 2026-10-02: v0.3.1 preview: https://github.com/JumpingAlcohol/SpeakFromHere/releases/tag/v0.3.1 . Release ID 402300877, tag/source commit ffdd309c88a787c80e8e032543259905815d662b. Four assets publicly hash-verified and old releases unchanged at publication; not a current remote re-audit. Historical tags/downloads are not modified by repository-link or local-candidate changes.

用户验收后明确授权，v0.3.1 预览版现已公开发布。四个附件重新下载校验一致，旧版标签／说明／附件未改。最终源码和便携检查通过；后续交接文档提交不移动发布标签。首读提示音是暂时方案，不是所有设备／长时间闲置吞字的全面修复。

## Product and invariants

- Brand: SpeakFromHere. Read docs/BRAND.md and docs/COMPETITIVE_POSITIONING.md; follow AGENTS.md. Paragraph-start listening to the same completed assistant reply's end, not arbitrary-character seeking or universal compatibility.
- Repository renamed by owner to SpeakFromHere; preserve distribution ai-chat-reader, module chat_reader, environment flags and LOCALAPPDATA/AIChatReader/settings.json. No credentials/private chat/binaries in Git; work/ and outputs/ are ignored.
- Alt+S: selected copyable text, never stale clipboard. Alt+E: hovered supported paragraph; no automatic clipboard fallback. GUI/portable enable paragraphs; source console requires --paragraphs.
- Defaults: Alt+P pause/resume, Alt+X stop, Alt+Shift+Q exit; terminal Ctrl+C exits. S/E fixed; other controls configurable. One reader instance at a time.
- Trust Windows-reported OpenAI.Codex_2p2nqsd0c76g0 family and registered app/ChatGPT.exe, then inspected reply structure. Numeric version alone does not veto. No guessed path, identity bypass or elevation. Other apps require separately inspected adapters; see docs/APP_COMPATIBILITY.md.
- Ordinary paragraphs/headings/recognized lists/inline links readable. Recognized code/table/editor/collapsed edited-files/status regions skipped with omission disclosure. Unknown/protected/expanded/ambiguous layouts, incomplete captures, user messages and current generating reply reject. Earlier completed replies need verified ownership/footer/later assistant marker.
- GUI omission notice counts kinds across the reply; Details lists ordered blocks and before-start/remaining flags, not omitted text/files/coordinates. Notice survives pause/replay, clears for selection. No automatic capture/upload. This is not synchronized highlighting.
- English primary README and aligned Chinese; canonical bilingual QuickStarts in ZIP. GUI language persists; console/diagnostics English. Candidate schema 3: rate -10..10, controls, language, voice_id (empty = default); atomic save without chat data. Schema 1/2 migrate only on save. v0.3.1 and earlier reject schema 3 downgrade. Corruption needs explicit reset.
- Dark draggable, nonactivating, topmost player above taskbar; settings may focus. Play toggles/replays in-memory last text; stop retains replay; exit clears it. Tray/× release keys. No login-startup/sentence navigation.

## Architecture and audio change

- app.py and gui.py share create_windows_speaker; main-thread dynamic comtypes SAPI. windows_audio.py retrieves native ISpMMSysAudio GetMMHandle with pointer-sized handles. Waveform pause/restart retains queued audio/position; paused cancellation resets owned buffers before SAPI purge. Non-waveform/unopened output falls back to SAPI. Never close borrowed handles, change SpAudio state or system volume/default device.
- StartupCue lazily queues one soft faded 400 ms/660 Hz PCM stream before first nonempty read per launch. SpeakStream flags 3, first plain text flags 17 (no cue purge), later flags 19. Retain stream lifetime; explicitly scale voice.Volume because SpeakStream bypasses it. Launch/settings/empty/failed captures silent; resume/replay/later reads do not repeat. Text errors cancel queued cue without replacing successful replay text.
- core.py controls/selected capture/ReadingPlan; read/play/pause/stop/exit cancels pending paragraph results. paragraphs.py validates immutable text/skipped payloads; old text-only wrappers remain.
- windows_context.py uses same-handle package/executable verification and temporary thread PER_MONITOR_AWARE_V2 for physical pointer/UIA, restoring afterward. No guessed scaling or process/Tk scaling changes.
- uia_probe.py is bounded/password-redacted; inspect_paragraph.py is diagnostic only. verified_reply: False there is not a playback verdict. codex_adapter.py validates assistant markers, geometry, completion Copy footer and bounded skip shapes.
- paragraph_job.py/worker: fresh capture, off-control-thread startup/collection, startup-inclusive 20s deadline, pipe draining/cancellation. Portable GUI/console share full neighboring reader-worker/ runtime; source pythonw uses neighboring python.exe. Missing helper asks for full extraction, never relaunches reader. Non-daemon cleanup can briefly delay exit after controls release.
- GUI HWND-bound hotkeys and WS_EX_NOACTIVATE preserve focus; shared controls and bilingual dictionaries. No new settings schema/UI in v0.3.1.
- Candidate voices.py enumerates SAPI IDs/descriptions/optional LCID metadata; no registry writes. WindowsSpeaker.set_voice changes only its own token while idle; factory warns/defaults on missing/failed saved token without file mutation. PlayerPreferences applies selection before atomic save; failed save restores voice/rate, rejected busy selection never reassigns the old live token. CLI --list-voices/--set-voice are silent/no hotkeys; --show-settings and rate/key-only commands need no speech object and preserve voice_id.

## Verification and open limits

- Local voice candidate: 225 full opt-in tests pass, no skips (default: 225 with 36 skips). Actual embedded GUI/console 125 each, helper 66, all pass; ZIP/helper/canonical guides checked. Two portable startup/control/exit/hotkey-release runs, silent portable list/select/reload, pip/compileall/diff checks pass. Both installed voices Huihui (zh_CN) and Zira (en_US) render owned WAV previews and hold/resume muted output during rate/replacement controls. Initial Zira rate check reproducibly finished a Chinese-only passage too early; changing only synthetic text to a long bilingual passage resolves it, no pause-code change. Temporary diagnostic fields removed. All new behavioral branches first failed then passed; controls remain scoped to available tested voices.
- Final v0.4.0 ZIP SHA256: ce18ce909f2795d73c09db14af142c07aecb0d4a62665122e83febae99509eed. Historical candidate hash: 9ee3dab7e8e4ce094a6c5027ce5d1290bbd0c2a40881d914de2cb3e601f84052. Published v0.3.1 local ZIP still matches 32beeff511fe873e294e828f2d2e3f2fe466e28a765f5c5ceb0987d1b9fde629. Manual candidate uses work/voice-acceptance-2026-10-04/settings.json (initial schema 2, Chinese UI), not the user's default profile. Generated isolated-test shortcut lives outside the ZIP; restart through it to use the same test profile. No chat/credentials captured.
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
- Current release output: outputs/v0.4.0/SpeakFromHere/, separate from all previous outputs. GUI/console exe + complete reader-worker/ + both guides + ZIP/SHA256SUMS. Extract entire ZIP. Build requires working Tcl/Tk; no GUI-less output.
- Public repository: https://github.com/JumpingAlcohol/SpeakFromHere . v0.4.0 publication now explicitly authorized. Verify Git/remote/tag/assets; historical evidence remains ignored in work/.

## Next priority

User order: commit/publish v0.4.0 local SAPI selection first, then develop paragraph-level reading-position visualization. Keep new visualization work after the release commit/tag. Do not equate queued text with audible progress; validate playback position, pause/cancel/replay, scrolling/DPI and privacy before claiming synchronized original-window highlighting. Other voice backends are deferred. Language-matched preview remains proposed, not implemented. No chat history/cloud upload or application-scope expansion. Historical releases/tags remain untouched.
