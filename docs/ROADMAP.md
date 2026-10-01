# AI Chat Reader version plan

[English](ROADMAP.md) | [简体中文](ROADMAP.zh-CN.md)

## Product goal

A lightweight Windows companion for listening to long AI replies. The main interaction should become: point at a paragraph, press a shortcut, and listen from that paragraph to the end of that assistant reply. Users should also be able to read selected text, pause/resume, stop, and choose their reading settings.

The initial target is the user's Codex/ChatGPT desktop workflow. Support for additional apps is added only after verifying their text access and reply boundaries; universal Windows compatibility is not promised.

## Release sequence

| Version | Scope | Acceptance criteria |
| --- | --- | --- |
| **v0.1.0 — MVP preview** | Selected-text reading, pause/resume, stop/exit, portable Windows executable, English and Chinese documentation. | Consecutive selections read correctly; failed copying never reads stale text; both exit methods work; the isolated executable launches twice and releases its hotkeys; the ZIP includes both guides. |
| **v0.2.0 — Paragraph reading preview** | Identify the paragraph under the mouse and its assistant reply; read from that paragraph to the reply's end. Retain `Alt + S`; plan `Alt + E` for paragraph reading. | Starting from the first, middle and last paragraph works in the verified target app. It never crosses into another reply, a user message, the input box or reply controls. Unsupported locations report a clear message and preserve selected-text reading. |
| **v0.2.1 — Reading settings** | Configurable shortcuts, reading speed and persisted preferences; clearer feedback on shortcut conflicts and unavailable content. | Settings survive restart, hotkey changes release the old binding, and invalid or conflicting settings do not silently disable the reader. |
| **v0.3.0 — Desktop interface** | A compact control window and system tray, visible playback state, English/Chinese UI switching and an optional user-controlled startup setting. | Common controls and settings are usable without a terminal. Closing/minimizing behaviour is clear, exit frees resources, and the selected UI language persists. |
| **v0.4.0 — Voice options** | Voice selection, a replaceable speech backend and an optional more natural speech source. Local Windows speech remains available. | Changing voice does not break controls. Pause/stop/cancel work with each supported backend. Online speech is enabled explicitly and shows connectivity, cost and text-processing requirements; errors allow returning to local speech. |
| **v0.9.0 — Public beta** | Compatibility checks, long-reply reliability, clean-install packaging and feedback-driven fixes. | Verified Windows/app combinations are documented. Long replies, repeated use, interruptions and upgrades pass the release checklist. Downloads work without a Python install; unsupported environments fail clearly. |
| **v1.0.0 — Stable release** | A reliable, documented core workflow for the supported target environment. | Paragraph reading, selected-text fallback, playback controls, settings and the desktop interface are verified. No known blocking issue remains in the stated support scope, and a previous working release remains downloadable. |

The sequence expresses priorities, not guaranteed completion dates. A version can be split if its acceptance criteria are not yet met; unfinished work must not be presented as released functionality.

## v0.2.0 acceptance checkpoint

Source and portable acceptance passed on 2026-10-01: the user confirmed paragraph starts, same-reply endings, switching starts/replies and playback controls in the actual target app, followed by the packaged executable. The portable preview also passed startup/control/exit and bundled-worker checks. Only desktop package `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0` is accepted. Editable writing blocks, tables, user messages, other apps and unknown layouts are outside paragraph-reading scope. Keep v0.1.0 as the selected-text-only fallback.

Acceptance areas checked for this preview:

1. Check whether Windows accessibility interfaces provide reply text, paragraph order and reliable reply ownership in the target app.
2. Verify mouse-point-to-paragraph mapping, including repeated paragraph text, links/lists, wrapped lines and off-screen parts of the same reply.
3. Build and test the bounded extraction rule: current paragraph through the end of the same assistant reply.
4. Integrate extraction with existing playback controls, then verify it against the actual app and state which app/version was tested.

The preview skips code blocks and treats a list item as a starting block; selected-text reading continues to read exactly what the user selects. These are not capabilities of the v0.1.0 download. Next milestone: v0.2.1 reading settings, after publication and feedback. Do not quietly expand the verified app/build scope.

If the app does not expose enough structure, record the limitation and keep v0.1.0 working. A local reading panel into which the user explicitly copies one complete reply is a possible fallback, but it must be presented as a separate workflow; it is not the same as reading directly from a paragraph in Codex/ChatGPT. Do not silently change the product into a browser extension or claim desktop support without evidence.

## Development and release rules

- Work on one milestone at a time and verify its acceptance criteria before starting optional extras.
- Keep English/Chinese READMEs, roadmap and packaged quick-start guides aligned. The language policy is recorded in `AGENTS.md`.
- Run relevant automated checks and a manual end-to-end check in the actual supported app. Use synthetic text for public test fixtures and never publish captured private conversations.
- Release a version when it adds a verified user-facing capability or provides a useful tested distribution. Publish completed milestones, rather than a release for every small commit.
- Keep generated binaries in release assets, not the Git source history. Ensure the published archive matches its checksum and the tagged source.

## Deferred beyond the core release

Sentence navigation, remembering reading position across sessions, synchronized highlighting, hover-to-read buttons and additional app adapters remain candidates after the core workflow is reliable. Voice cloning, a full screen-reader replacement and automatic background reading of every chat are outside the current plan.
