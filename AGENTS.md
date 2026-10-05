# SpeakFromHere project rules

## Brand and positioning

- Public product name: `SpeakFromHere` (exact capitalization). Tagline: `Read AI responses aloud from exactly where you want.` Chinese supporting line: `AI 回复，从你想听的位置开始。`
- Lead with reply-aware, paragraph-start listening in an inspected Windows Codex desktop build, not generic TTS. Always clarify paragraph granularity; no arbitrary-character/sentence-seeking or universal compatibility claim.
- Read `docs/BRAND.md` and `docs/COMPETITIVE_POSITIONING.md` for copy. Do not claim first/only/best or name/trademark clearance. Open latency/audio-loss and unsupported-block issues remain open; no safe-skipping or natural-voice claims before verification.
- The owner renamed the GitHub repository to `JumpingAlcohol/SpeakFromHere` on 2026-10-04; current links/origin use that verified URL. Keep legacy Python distribution/module, environment variables and local settings path compatible unless a separate migration is requested. Preserve historical release files/notes. New local bundles use `SpeakFromHere` filenames.

## Language policy

- `README.md` is the primary English README. `README.zh-CN.md` is the complete Simplified Chinese version. Both start with reciprocal `English | 简体中文` links.
- Keep both READMEs aligned whenever features, shortcuts, requirements, setup, tests, packaging, or limitations change. Do not update just one language.
- Portable downloads include `QuickStart.en.txt` and `QuickStart.zh-CN.txt`. Their canonical sources are in `docs/`; the build copies them into the output and includes both in the ZIP.
- The GUI has a persisted English/Chinese selector. Console status and detailed diagnostics stay in English; maintain both GUI label dictionaries when changing controls. Historical releases do not acquire GUI support retroactively.
- Keep code identifiers, commands, filenames and shortcut bindings consistent across languages. Chinese promotional materials can link directly to `README.zh-CN.md`; the GitHub landing page defaults to English.

## Generated files

- Do not commit virtual environments, caches, local credentials, scratch files or generated binaries. Build outputs belong in ignored `outputs/` and intermediate files in ignored `work/`.
- Verify the portable ZIP contains the executable and both quick-start files after changing packaging or documentation.

## Project continuity

- Read `CONTEXT.md` at the start of a new chat before exploring the repository. It is a short handoff of verified milestones, boundaries, commands and the next priority.
- Keep it concise and update it when a milestone or workflow changes. Do not copy old chat transcripts into it.
- Treat recorded release/build results as historical evidence; verify Git state, artifacts and remote status before publishing again.
- Never put credentials, captured private chat text or personal absolute paths into the public handoff.
