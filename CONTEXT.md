# AI Chat Reader — project handoff

Last milestone: 2026-10-01, v0.2.0 paragraph-reading preview accepted for publication.
简要状态：源码和便携版均已验收；下一步是 v0.2.1 阅读设置，不扩展当前应用范围。

## Product and decisions

- A lightweight Windows AI-reply reader, not a full screen reader or browser extension.
- `Alt + S` reads selected text in apps that support copying it; never read stale clipboard contents after a failed copy.
- `Alt + E` reads from the hovered paragraph's beginning to the end of that assistant reply. Portable v0.2.0 enables it by default; Python source needs `--paragraphs`.
- `Alt + P` pauses/resumes, `Alt + X` stops, `Alt + Shift + Q` or terminal `Ctrl + C` exits. Only one reader instance at a time.
- Paragraph scope: inspected package `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0`, executable `app/ChatGPT.exe`. Other builds/apps are rejected until inspected.
- Ordinary paragraphs/headings/recognized lists and inline links are handled; code blocks are skipped. Tables, editable writing blocks, user messages, controls and incomplete/unknown structures are unsupported. `Alt + S` is the fallback.
- Windows SAPI is local. More natural/replaceable voices are planned for v0.4.0, not implemented.
- English README + complete Simplified Chinese README, matching bilingual quick-start guides, English runtime status. Follow `AGENTS.md`.

## Architecture

- `app.py`: Windows hotkeys, main-thread SAPI; hidden `--paragraph-worker x y` routes only to capture, never to reader startup.
- `core.py`: interruptible controls and selected-text capture; pending paragraph results are canceled by read/pause/stop/exit.
- `windows_context.py`: physical pointer coordinates and executable identity query.
- `uia_probe.py`: bounded read-only UIA capture, password redaction, no upload or clipboard changes.
- `codex_adapter.py`: hidden speaker headings + paragraph identity/geometry + copy footer delimit one completed assistant reply; never flatten a whole window into speech.
- `paragraphs.py`: platform-independent suffix extraction with ownership/completeness validation.
- `paragraph_worker.py` + `paragraph_job.py`: isolated capture with a 20-second timeout, pipe draining and stale-result cancellation. Frozen jobs reuse the bundled executable, not Python `-m` arguments.
- `inspect_paragraph.py`: separate diagnostic only. Its `verified_reply: False` is expected, not a playback verdict. Private snapshots stay in ignored `work/`.

## Verified milestone

- User confirmed first/middle/last starts, same-reply ending, switching replies/paragraphs, repeat reads and existing controls in source mode; then confirmed the portable executable.
- All 88 tests passed with Windows SAPI/UIA/portable checks enabled. Two isolated executable startup/control/exit runs passed; standalone bundled UIA was verified against a test-owned synthetic window.
- Native cross-process UIA and credential access may fail inside the restricted sandbox; use approved normal-desktop execution for those checks. Do not weaken reader safety checks to work around sandbox restrictions.
- Public fixtures are synthetic. Never commit `work/paragraph-probe.json`, virtual environments, credentials or generated binaries.
- This is development-machine Windows 11 x64 verification, not general Windows/app/language compatibility. English interface markers have synthetic coverage only.

## Commands and artifacts

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\build.ps1
.\scripts\test-executable.ps1
```

- Opt-in environments: `CHAT_READER_WINDOWS_TESTS=1`, `CHAT_READER_UIA_TESTS=1`, `CHAT_READER_PORTABLE_TESTS=1`; clear them after testing. Speech tests mute only their own voice or render temporary WAV files.
- Build outputs: `outputs/v0.2.0/AIChatReader.exe`, `AIChatReader-Windows-x64.zip`, `SHA256SUMS.txt`. ZIP contains the executable and both canonical quick-start guides. Previous v0.1.0 files remain separate.
- Repository: https://github.com/JumpingAlcohol/ai-chat-reader
- Release checkpoint: tag `v0.2.0`, bilingual notes in `docs/releases/v0.2.0.md`. Check the actual remote to confirm publication, tag commit and asset hashes; this file is not proof of remote state.

## Next priority

After v0.2.0 publication/feedback, plan v0.2.1: configurable shortcuts, reading speed and persisted settings. GUI/tray/language switch are v0.3.0. Natural voice backends are v0.4.0. See both roadmaps; do not start optional table/editor or universal-app support without a new scope decision.
