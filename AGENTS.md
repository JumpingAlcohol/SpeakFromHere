# AI Chat Reader project rules

## Language policy

- `README.md` is the primary English README. `README.zh-CN.md` is the complete Simplified Chinese version. Both start with reciprocal `English | 简体中文` links.
- Keep both READMEs aligned whenever features, shortcuts, requirements, setup, tests, packaging, or limitations change. Do not update just one language.
- Portable downloads include `QuickStart.en.txt` and `QuickStart.zh-CN.txt`. Their canonical sources are in `docs/`; the build copies them into the output and includes both in the ZIP.
- Runtime status messages currently stay in English. Add an English/Chinese language selector when a dedicated GUI is implemented; do not claim this selector exists yet.
- Keep code identifiers, commands, filenames and shortcut bindings consistent across languages. Chinese promotional materials can link directly to `README.zh-CN.md`; the GitHub landing page defaults to English.

## Generated files

- Do not commit virtual environments, caches, local credentials, scratch files or generated binaries. Build outputs belong in ignored `outputs/` and intermediate files in ignored `work/`.
- Verify the portable ZIP contains the executable and both quick-start files after changing packaging or documentation.

## Project continuity

- Read `CONTEXT.md` at the start of a new chat before exploring the repository. It is a short handoff of verified milestones, boundaries, commands and the next priority.
- Keep it concise and update it when a milestone or workflow changes. Do not copy old chat transcripts into it.
- Treat recorded release/build results as historical evidence; verify Git state, artifacts and remote status before publishing again.
- Never put credentials, captured private chat text or personal absolute paths into the public handoff.
