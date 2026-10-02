# SpeakFromHere — project handoff

Current milestone: 2026-10-02, v0.3.0 floating-player candidate, not a published Release. After updating the Codex client, the user reports the requested ordinary-paragraph/table tests work without issues and authorizes source commit/push to the existing GitHub repository. Tested editable-block/file skipping was already accepted. This is scoped user-reported compatibility, not universal future-update support; exact updated package version was not captured. Separate compaction-status capture remains pending. Verify actual Git/remote state for source publication.
简要状态：更新 Codex 后，用户确认普通段落／表格测试无问题，并授权提交及推送现有 GitHub 仓库；编辑块／文件跳过此前已通过。不是所有未来版本兼容保证，未记录新包精确版本；v0.3.0 Release 尚未发布。未知边界仍拒读，高亮未实现；原延迟／开头丢字反馈不据此关闭。

## Product and decisions

- Brand: SpeakFromHere, formerly AI Chat Reader. Tagline: "Read AI responses aloud from exactly where you want." Chinese supporting line: "AI 回复，从你想听的位置开始。" See docs/BRAND.md and docs/COMPETITIVE_POSITIONING.md; follow AGENTS.md.
- Core: a lightweight Windows AI-reply reader, not a full screen reader. Read from a supported paragraph's beginning to the same completed assistant reply's end. No arbitrary character/sentence seeking or universal compatibility.
- Preserve legacy repository URL, Python distribution ai-chat-reader, module chat_reader, environment flags and LOCALAPPDATA/AIChatReader/settings.json. New portable files use SpeakFromHere; historical releases remain unchanged.
- Alt+S reads manually selected copyable text; failed copying never speaks stale clipboard contents. Alt+E reads the hovered supported paragraph suffix. Source GUI and portable entries enable it; source console needs --paragraphs.
- Defaults: Alt+P pause/resume, Alt+X stop, Alt+Shift+Q exit; terminal Ctrl+C also exits. Only one reader instance at a time. Pause/stop/exit bindings are configurable; S/E remain fixed.
- Trust: Windows-reported OpenAI.Codex_2p2nqsd0c76g0 package family plus registered app/ChatGPT.exe, then inspected reply structure. Numeric versions alone no longer veto. No guessed path fallback, elevation or identity bypass. Other apps need separate inspected adapters. See docs/APP_COMPATIBILITY.md.
- Ordinary paragraphs/headings/recognized lists and inline links are readable. Recognized code blocks, Table (50036) boundaries, inspected table-widget grid/action wrappers, group/writing-block-surface editors, collapsed edited-files header/rows and simple post-Copy activity metadata are skipped, never starting paragraphs. Known standalone Regenerate/More leaves are ignored only after verified Copy, with label/style/protection/process guards; Chinese labels inspected, English counterparts synthetic-tested. Unknown/changed/expanded layouts, protected fields, incomplete captures and uncertain boundaries still reject. User messages remain unsupported; Alt+S is the explicit fallback.
- GUI omission notice counts kinds across the verified reply, including blocks before the start. Details gives ordered block numbers and before-start/remaining flags, not omitted text, filenames or coordinates. Notice survives pause/replay, clears for a new selection and switches English/Chinese. Diagnostics remain English; no automatic copying/saving/uploading.
- Highlighting is future work: distinguish planned readable content, omissions and actual audible progress, potentially via a non-mutating paragraph overlay. Current notice is not original-text coloring or synchronized playback tracking. Both roadmaps record the user need.
- Local Windows SAPI remains the voice backend. More natural/replaceable voices are planned for v0.4.0, not implemented. Startup/pause delays and missing first characters (ISSUE-001) remain open.
- English primary README and aligned complete Chinese README; canonical bilingual quick starts in docs/ are bundled. Maintain both GUI dictionaries; GUI language persists.
- Settings schema 2: rate -10..10, controls and language, atomically saved without chat data. Schema 1 unchanged until explicit save; v0.2.1 rejects schema 2 on downgrade. Invalid settings require explicit reset. GUI submits rate immediately without re-speaking; user reports gradual mid-playback change, timing is voice-dependent and unmeasured.
- GUI: dark draggable nonactivating topmost bottom-right player above taskbar. Settings intentionally accepts typing. Play pauses/resumes or replays last submitted text from memory; stop retains replay, exit clears it. Tray hide/restore and × exit release keys. No login-startup setting or sentence navigation.

## Architecture

- app.py: Windows hotkeys, main-thread SAPI, settings commands without playback. Hidden --paragraph-worker x y routes only to capture.
- gui.py + player.py: Tk/tray/labels/settings/omission notice and Details, sharing core and same-thread SAPI. HWND-bound shortcuts survive Tk dispatch; WS_EX_NOACTIVATE preserves focus. gui_entry.py preserves internal-worker UTF-8 routing.
- core.py: selected capture and controls; read/play/pause/stop/exit cancels pending paragraph results. ReadingPlan reports whitelist-only omissions before speaking prose. Clipboard waits and SAPI remain here; this does not fix ISSUE-001.
- windows_context.py: physical pointer and same-handle executable/package checks. physical_coordinate_context temporarily sets thread PER_MONITOR_AWARE_V2 for cursor sampling and UIA hit/cache calls, then restores it. No guessed ratio or Tk/process scaling change.
- uia_probe.py: bounded read-only UIA capture with password redaction. inspect_paragraph.py is diagnostic only; verified_reply: False there is not a playback verdict. Historical private snapshots remain ignored in work/.
- codex_adapter.py: hidden speaker headings, paragraph identity/geometry and Copy footer delimit one completed reply. Typed separators, valid Chinese/full-English weekday clocks and simple activity shapes are metadata, never completion evidence. Earlier completed replies may be read during later generation only with verified ownership/footer/later assistant marker; current generating replies reject.
- paragraphs.py: immutable ReadingPlan(text, skipped) and whitelist-only SkippedBlock(kind, ordinal, before_start); suffix extraction and strict payload validation. Legacy text-only wrappers remain compatible.
- paragraph_worker.py + paragraph_job.py: fresh isolated capture, startup-inclusive 20s deadline, pipe draining/cancellation. Launch/collection off control thread. Portable GUI/console share neighboring reader-worker/SpeakFromHereWorker.exe plus full runtime; missing helper asks for full ZIP extraction, never relaunches reader. Source pythonw uses neighboring python.exe. Non-daemon cleanup can briefly delay exit after controls release while native startup returns.

## Verification and remaining acceptance

- Historical milestones: v0.2.0 reading/portable accepted by user; v0.2.1 settings/rebrand had 108 desktop tests. Initial v0.3.0 GUI had 133; parser/identity/helper/DPI/weekday increments reached 139/147/156/160/169. Details remain in release notes and docs/KNOWN_ISSUES.md, not proof of current remote state.
- Latest candidate: all **190 tests passed** with WINDOWS/GUI/UIA/PORTABLE opt-ins, no skips. Two successive console portable settings/startup/control/exit smoke runs passed, with real shortcut ownership/release. Covers SAPI/shortcuts, owned-window GUI omission/language/details/replay, UIA/DPI, worker protocol and table/widget/footer regressions. Isolated settings and synthetic/owned windows only.
- Clean portable rebuild on approved normal desktop. Actual embedded GUI/console modules passed **90 checks each**; helper passed **66**, no skips in the final embedded run. ZIP main entries, all helper files, byte-matching canonical guides and absence of temporary identity tracing checked. pip check, compileall and diff check passed. Initial build was blocked by running old GUI; retried successfully after user exited, without killing processes or changing permissions.
- Current ZIP SHA256 after acceptance-guide-only refresh: 27fc4194cb826b188d8a9cfa0f82d959f0835f8c3e24c5359a23d26c56b186d1. Executables unchanged; ZIP entries/helper/canonical guides verified again. Pre-commit default suite: 190 tests, 22 desktop opt-in skips. Embedded normal-desktop rerun: 90/90/66 checks, no skips; restricted cursor/UIA failures did not reproduce there. Verify actual artifact again before any Release publication.
- ISSUE-002: user confirms tested editable-block/file skips and now reports the requested ordinary/table workflows work after a Codex update. Earlier 1050-node edited-files checks passed. Table diagnosis: twice-reproduced 546-node capture identified group/app-widget _TableContainer_* with typed grid/Table (50036)/two-action overlay and standalone post-Copy Regenerate/More leaves. Removing only these three nodes in memory restored prose; the narrow fix passes six new regressions covering hash variation, suffix/disclosure, no cell starts and unsafe boundaries. Fresh real extraction reports one table omission, ordinal 2. No body/cell text saved/output; this does not establish all layouts or table narration.
- ISSUE-007: complete 960-node inspection confirmed 已优化对话 in the narrow post-Copy activity container before the next turn. In-memory removal restored the suffix; new synthetic skip regression passes. Post-fix real capture/manual playback remain pending.
- ISSUE-004: metadata-only trace/native owned-window reproduction proved mismatched physical coordinates selected another process, explaining identity error 5/package rejection. Scoped DPI correction passed embedded modules; user confirmed GUI Alt+E restored. Temporary trace removed; original helper backup stays ignored.
- ISSUE-006: weekday-prefixed post-Copy leaf timestamps ignored; user confirms Chinese fix. Full English weekday labels have synthetic coverage, not live English inspection. Abbreviations, AM/PM and uninspected relative dates remain unsupported.
- ISSUE-003: three interleaved owned-window helper measurements ~1.07–1.14s versus old GUI internal worker ~2.11–3.05s. Small-capture startup evidence, not real-chat speed or audio latency acceptance.
- Restricted COM/UIA/native checks can yield false negatives. Use approved normal-desktop execution, not admin/UAC; never weaken guards. Run native GUI suites serially to avoid foreground interference.
- Public fixtures are handwritten/synthetic. Never commit work/, caches, environments, credentials, private chat text or binaries. Verification is development-machine Windows 11 x64, not general platform/app support.

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

- Opt-ins: CHAT_READER_WINDOWS_TESTS=1, CHAT_READER_GUI_TESTS=1, CHAT_READER_UIA_TESTS=1, CHAT_READER_PORTABLE_TESTS=1; clear after testing. Speech checks mute their own voice or render temporary WAV.
- Artifacts: outputs/v0.3.0/SpeakFromHere/: SpeakFromHere.exe (GUI), SpeakFromHereConsole.exe, reader-worker/ (required), both quick starts, SpeakFromHere-Windows-x64.zip, SHA256SUMS.txt. Extract full ZIP; never copy only main exe. Build requires usable Tcl/Tk on normal desktop; spec refuses GUI-less builds.
- Repository: https://github.com/JumpingAlcohol/ai-chat-reader . Last recorded published checkpoint: v0.2.0, not a current remote check. Inspect actual remote/tag/assets and require publication authorization. Older output directories remain separate.

## Next priority

1. Preserve user acceptance of tested ordinary/table/editor/file workflows after client update; exact updated package version was not recorded. Source commit/push is authorized, not a Release publication request. Compaction-status dedicated post-fix capture remains pending.
2. Fix only reproduced further layouts. Unknown content must not silently cross turn/app/protection boundaries. ISSUE-002 remains partially verified, not universally complete.
3. Continue accepted roadmap after manual checks. Highlighting needs separate design/verification (audible position, scrolling/DPI, cancellation, privacy); skip metadata is groundwork, not highlighting.
4. ISSUE-001 playback/pause delays and opening loss remain independently open. No natural-voice/universal claims or remote action without explicit request.
