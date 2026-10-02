# SpeakFromHere version plan

[English](ROADMAP.md) | [简体中文](ROADMAP.zh-CN.md)

## Product goal

A lightweight Windows companion for listening to long AI replies. The main interaction should become: point at a paragraph, press a shortcut, and listen from that paragraph to the end of that assistant reply. Users should also be able to read selected text, pause/resume, stop, and choose their reading settings.

The initial target is the user's Codex/ChatGPT desktop workflow. Support for additional apps is added only after verifying their text access and reply boundaries; universal Windows compatibility is not promised.

## Release sequence

| Version | Scope | Acceptance criteria |
| --- | --- | --- |
| **v0.1.0 — MVP preview** | Selected-text reading, pause/resume, stop/exit, portable Windows executable, English and Chinese documentation. | Consecutive selections read correctly; failed copying never reads stale text; both exit methods work; the isolated executable launches twice and releases its hotkeys; the ZIP includes both guides. |
| **v0.2.0 — Paragraph reading preview** | Identify the paragraph under the mouse and its assistant reply; read from that paragraph to the reply's end. Retain `Alt + S`; plan `Alt + E` for paragraph reading. | Starting from the first, middle and last paragraph works in the verified target app. It never crosses into another reply, a user message, the input box or reply controls. Unsupported locations report a clear message and preserve selected-text reading. |
| **v0.2.1 — Reading settings** | Persisted local SAPI rate and configurable pause/stop/exit keys; fixed Alt+S/Alt+E paths; clearer conflicts and manual fallback feedback. | Settings survive restart, old bindings are released on exit, invalid configurations are preserved with defaults/warnings, and conflicting changes are refused. |
| **v0.3.0 — Desktop interface** | Bottom-right floating player, tray, playback state, replay, rate controls, persisted English/Chinese UI and control-key settings. Login startup deferred to a separate opt-in follow-up. | Double-click without a terminal; player controls preserve target focus, hide/restore works, exit releases resources, preferences persist. Real-chat/audio check remains required. |
| **v0.4.0 — Voice options** | Voice selection, a replaceable speech backend and an optional more natural speech source. Local Windows speech remains available. | Changing voice does not break controls. Pause/stop/cancel work with each supported backend. Online speech is enabled explicitly and shows connectivity, cost and text-processing requirements; errors allow returning to local speech. |
| **v0.9.0 — Public beta** | Compatibility checks, long-reply reliability, clean-install packaging and feedback-driven fixes. | Verified Windows/app combinations are documented. Long replies, repeated use, interruptions and upgrades pass the release checklist. Downloads work without a Python install; unsupported environments fail clearly. |
| **v1.0.0 — Stable release** | A reliable, documented core workflow for the supported target environment. | Paragraph reading, selected-text fallback, playback controls, settings and the desktop interface are verified. No known blocking issue remains in the stated support scope, and a previous working release remains downloadable. |

The sequence expresses priorities, not guaranteed completion dates. A version can be split if its acceptance criteria are not yet met; unfinished work must not be presented as released functionality.

## v0.2.0 acceptance checkpoint

Source and portable acceptance passed on 2026-10-01: the user confirmed paragraph starts, same-reply endings, switching starts/replies and playback controls in the actual target app, followed by the packaged executable. The portable preview also passed startup/control/exit and bundled-worker checks. Only desktop package `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0` is accepted. Editable writing blocks, tables, user messages, other apps and unknown layouts are outside paragraph-reading scope. Keep v0.1.0 as the selected-text-only fallback.

v0.2.1 settings acceptance remains open. On 2026-10-01 the user explicitly prioritized the GUI before the reported latency/opening-audio and unsupported-block fixes. The v0.3.0 preview adds GUI/tray/language selection and bounded skipping with omission notices. Tested ordinary/table/editor/file workflows are user-confirmed after a Codex update; ISSUE-001 audio reports remain open. See the v0.3.0 release notes for verified scope. Login startup, voice/backend and volume are deferred. Native process creation can briefly delay paragraph startup; collector tests do not prove instantaneous launch.

Acceptance areas checked for this preview:

1. Check whether Windows accessibility interfaces provide reply text, paragraph order and reliable reply ownership in the target app.
2. Verify mouse-point-to-paragraph mapping, including repeated paragraph text, links/lists, wrapped lines and off-screen parts of the same reply.
3. Build and test the bounded extraction rule: current paragraph through the end of the same assistant reply.
4. Integrate extraction with existing playback controls, then verify it against the actual app and state which app/version was tested.

The preview skips code blocks and treats a list item as a starting block; selected-text reading still reads the selection. These are not capabilities of v0.1.0. Next: diagnose ISSUE-001 and verify only reproduced additional layouts for ISSUE-002. Do not expand inspected app/build scope silently. Release notes: [v0.3.0](releases/v0.3.0.md).

If the app does not expose enough structure, record the limitation and keep v0.1.0 working. A local reading panel into which the user explicitly copies one complete reply is a possible fallback, but it must be presented as a separate workflow; it is not the same as reading directly from a paragraph in Codex/ChatGPT. Do not silently change the product into a browser extension or claim desktop support without evidence.

## Development and release rules

- Work on one milestone at a time and verify its acceptance criteria before starting optional extras.
- Keep English/Chinese READMEs, roadmap and packaged quick-start guides aligned. The language policy is recorded in `AGENTS.md`.
- Run relevant automated checks and a manual end-to-end check in the actual supported app. Use synthetic text for public test fixtures and never publish captured private conversations.
- Release a version when it adds a verified user-facing capability or provides a useful tested distribution. Publish completed milestones, rather than a release for every small commit.
- Keep generated binaries in release assets, not the Git source history. Ensure the published archive matches its checksum and the tagged source.

## Deferred beyond the core release

Sentence navigation, remembering reading position across sessions, synchronized highlighting, hover-to-read buttons and additional app adapters remain candidates after the core workflow is reliable. Voice cloning, a full screen-reader replacement and automatic background reading of every chat are outside the current plan.

2026-10-02 clarification: v0.3.0 adds disclosed skipping for recognized blocks (ISSUE-002/007). This notice is not highlighting. The requested later visual feature should distinguish the planned readable paragraphs, omitted regions and current audible position; it must not claim that planned/submitted text has already been heard. Evaluate paragraph overlays without changing Codex content, plus scroll/move/DPI changes, cancellation and privacy. No original-text coloring or synchronized progress is implemented or promised for this preview.
