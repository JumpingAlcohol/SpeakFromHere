# SpeakFromHere — positioning notes / 项目定位记录

Research date / 核对日期: 2026-10-01.

## English

### Brand and core definition

**SpeakFromHere — Read AI responses aloud from exactly where you want.**

A lightweight Windows reader for choosing where to start listening inside an AI reply. In the currently inspected Codex desktop build, point at a supported paragraph and press `Alt + E`: playback starts at that paragraph's **beginning** and ends at the end of the **same completed assistant reply**. Use `Alt + S` for manually selected, copyable text elsewhere. The tagline expresses the product direction; today's positioning is paragraph-level, not arbitrary word/sentence seeking. [Current scope](../CONTEXT.md), [paragraph extraction](../src/chat_reader/paragraphs.py).

### Nearby projects: verified descriptions, not absence claims

| Project | What its publisher explicitly describes | SpeakFromHere's current emphasis |
| --- | --- | --- |
| [codex-read-aloud](https://github.com/cobibean/codex-read-aloud) | macOS, on-demand speech; a command reads the latest local Codex assistant message; system voices or optional OpenAI TTS. | A Windows desktop pointer-and-hotkey starting point within a reply. |
| [Echo](https://chromewebstore.google.com/detail/echo-read-x-chatgpt-subst/acmcamiebaibkbafoancpkdapcijoine) | Chrome extension, ChatGPT reply buttons, clickable live transcript, sentence navigation and on-device speech. | Start from the supported paragraph already under the pointer in the inspected desktop app. |
| [2lazy2read](https://2lazy2read.com/) | Windows selected-text listening with global shortcuts, plus summaries and audio history. | Reply-boundary-aware paragraph reading, with manual selection as a separate fallback. |

These are publisher descriptions, not independently tested compatibility or quality results. A feature not described in these pages is **not** proof that it is unavailable. Local speech, playback controls and flexible starting points are not exclusive to this project, as the linked descriptions illustrate.

### Defensible highlights

- **Choose a paragraph, not just the latest answer:** the core workflow is pointer → `Alt + E` → the remaining prose of that reply, without dragging a selection to its end. [Scope and implementation](../CONTEXT.md), [adapter](../src/chat_reader/codex_adapter.py).
- **Respect reply boundaries:** verify assistant ownership and completion; do not flatten the window or continue into the next reply. Unknown/unsafe structures are rejected. [Adapter](../src/chat_reader/codex_adapter.py), [extraction rules](../src/chat_reader/paragraphs.py).
- **Keep the desktop workflow:** a standalone Windows reader rather than a browser extension; manual `Alt + S` remains useful when text is copyable but paragraph reading is unavailable. [Current scope](../CONTEXT.md).
- **Local speech without a cloud voice key:** today's backend is Windows SAPI. This is a design choice, not a claim of superior naturalness or exclusive privacy. [Speech implementation](../src/chat_reader/app.py).

### Boundaries and claims to avoid

The v0.3.0 preview verifies Windows package family `OpenAI.Codex_2p2nqsd0c76g0` and its registered `app/ChatGPT.exe`, then validates the inspected reply structure rather than an exact numeric version. This does not establish support for every future Codex/ChatGPT layout, browser or Windows application; other apps need their own inspected adapters. Recognized code blocks, table/editor boundaries, inspected collapsed edited-files regions and simple post-reply activity metadata can now be skipped with a visible notice and Details. The user confirmed tested editable-block/file skipping. A real wrapped grid/table plus known standalone footer controls now passes post-fix extraction; the user now confirms ordinary/table reading after updating Codex, without establishing universal future compatibility. Unknown/protected/ambiguous structures still reject; this is not universal skipping or original-text highlighting. [Current scope](../CONTEXT.md), [compatibility](APP_COMPATIBILITY.md), [ISSUE-002](KNOWN_ISSUES.md#issue-002--one-unsupported-block-rejects-the-whole-reply--一个不兼容块导致整条回复拒读).

Startup/pause delays and missing opening audio remain open reports. The v0.3.0 preview has a floating GUI and tray, not retroactive GUI support in historical releases. Do not promise instant playback, zero latency, production reliability, natural voices, sentence-level seeking, highlighting or universal compatibility. [Known issues](KNOWN_ISSUES.md), [current milestone](../CONTEXT.md).

This is a focused comparison, not an exhaustive web search, name/trademark clearance, or evidence for “first,” “only,” “best” or “no competitors.” SpeakFromHere's distinction is its **workflow and scope combination**, not ownership of the general read-from-here idea. This independent project is not an official OpenAI product.

## 简体中文

### 品牌与核心定义

**SpeakFromHere — Read AI responses aloud from exactly where you want.**

中文表达：**从你想听的位置，开始朗读 AI 回复。**

一个轻量 Windows AI 回复阅读器。在当前已检查的 Codex 桌面版本中，将鼠标放在支持的段落上，按 `Alt + E`，从**该段开头**读到**同一条已完成 AI 回复的末尾**；其他可复制文字可手动选中后按 `Alt + S`。品牌标语表达产品方向；现阶段是段落级起读，不是精确到任意字或句子的跳播。[当前范围](../CONTEXT.md)、[段落提取](../src/chat_reader/paragraphs.py)。

### 相近项目：核实其公开描述，不据此断言它们缺少功能

| 项目 | 发布者明确描述的功能 | SpeakFromHere 当前侧重点 |
| --- | --- | --- |
| [codex-read-aloud](https://github.com/cobibean/codex-read-aloud) | macOS 按需朗读；命令读取最近一条本地 Codex 回复；系统语音或可选 OpenAI TTS。 | Windows 桌面中用鼠标位置和快捷键选择回复内起点。 |
| [Echo](https://chromewebstore.google.com/detail/echo-read-x-chatgpt-subst/acmcamiebaibkbafoancpkdapcijoine) | Chrome 扩展，为 ChatGPT 回复添加朗读按钮；支持可点击转录、句子导航、本地语音。 | 直接从已检查桌面应用中鼠标所指的支持段落开始。 |
| [2lazy2read](https://2lazy2read.com/) | Windows 选文朗读、全局快捷键，并提供摘要与音频历史。 | 识别当前回复边界的段落读取；选文朗读是另一条兜底路径。 |

以上来自发布者页面，并非独立实测兼容性或质量结论。页面没写某项功能，**不等于该项目没有该功能**。这些来源也说明，本地语音、播放控制、灵活起点本身都不是本项目独有。

### 可以准确强调的亮点

- **选定段落，而不只读最新整条回答：**鼠标定位 → `Alt + E` → 继续听这条回复的正文，不必拖选到末尾。[范围与实现](../CONTEXT.md)、[适配器](../src/chat_reader/codex_adapter.py)。
- **知道该在哪里停止：**确认 AI 回复归属及完成状态，不把整个窗口拼起来读，也不越过当前回复读下一条。未知或不安全结构仍拒读。[适配器](../src/chat_reader/codex_adapter.py)、[提取规则](../src/chat_reader/paragraphs.py)。
- **留在桌面工作流里：**独立 Windows 小工具，不是浏览器插件；不能按段落读取时，可复制文字仍可手动使用 `Alt + S`。[当前范围](../CONTEXT.md)。
- **当前语音在本机生成，无需云端声源密钥：**使用 Windows SAPI。这是设计选择，不代表音质更自然或隐私优势独有。[语音实现](../src/chat_reader/app.py)。

### 边界与不能提前宣传的能力

v0.3.0 预览版验证 Windows 包家族 `OpenAI.Codex_2p2nqsd0c76g0` 及已注册的 `app/ChatGPT.exe`，再验证已检查的回复结构，而非精确数字版本；不代表兼容所有未来 Codex／ChatGPT 布局、网页或 Windows 软件。其他应用仍须独立检查和适配。已识别的代码块、表格／编辑块边界、已检查的折叠文件区域及回复后的简单活动状态现在可跳过，并显示提示和详情。用户已确认测试过的编辑块／文件跳过成功。真实 grid／表格容器及已知独立页尾控件现通过修改后提取；用户现已确认更新 Codex 后普通段落／表格测试通过，不代表通用未来兼容。未知、受保护或归属不明结构仍拒读；这不是通用跳过，也不是原文高亮。[当前范围](../CONTEXT.md)、[兼容策略](APP_COMPATIBILITY.md)、[ISSUE-002](KNOWN_ISSUES.md#issue-002--one-unsupported-block-rejects-the-whole-reply--一个不兼容块导致整条回复拒读)。

起读／暂停延迟、首次开头丢字仍待处理。v0.3.0 预览版已有悬浮 GUI 和托盘，不代表历史发布版也有。不能宣传即时播放、零延迟、成熟稳定、自然人声、按句跳播、高亮或通用兼容。[已知问题](KNOWN_ISSUES.md)、[版本状态](../CONTEXT.md)。

这是一组聚焦比较，不是穷尽全网搜索、名称／商标审查，也不能证明“首个”“唯一”“最好”或“没有竞品”。差异在于**工作流与支持范围的组合**，不是宣称“从这里读”的概念归本项目独有。本项目独立开发，非 OpenAI 官方产品。
