# SpeakFromHere — brand and product definition / 品牌与产品定义

Decided 2026-10-01 / 确定于 2026-10-01.

## English

**Name:** SpeakFromHere

**Tagline:** Read AI responses aloud from exactly where you want.

**Core definition:** A lightweight, reply-aware Windows desktop reader. Choose a supported paragraph in a completed AI response, then listen from its beginning to the end of that same reply without selecting the entire remainder. Keep manually selected-text reading as an explicit fallback.

**Main promise:** choose where to start listening and keep the reply boundary—not a new general-purpose screen reader, a browser extension, or a replacement AI chat app.

**Current truth:** paragraph-level starting points only, limited to the inspected Codex desktop package recorded in CONTEXT.md. “Exactly where you want” is the product direction, not arbitrary word/sentence seeking. Other copyable selections can use Alt+S. The v0.3.0 preview skips recognized code blocks, table/editor boundaries, inspected collapsed edited-files regions and simple post-reply activity metadata, with an omission notice and Details. The user confirmed tested editable-block/file skipping. A real wrapped grid/table and known standalone footer controls now pass post-fix extraction; the user now confirms ordinary/table reading after updating Codex. This does not prove compatibility with all future layouts. Unknown or unsafe boundaries still reject. Playback/pause latency and missing opening audio remain reported issues.

The v0.3.0 preview uses Windows package identity plus the inspected reply structure, not an exact numeric version. An unchanged number or a similar interface is not proof of compatibility; other applications still need separate inspected adapters. [Compatibility policy](APP_COMPATIBILITY.md).

**Highlights:** pointer-to-paragraph + hotkey; completed assistant-reply ownership and ending boundary; native Windows desktop workflow; explicit selected-text fallback with fresh-clipboard validation; local Windows speech. These form a positioning combination, not proof of exclusive features or superior audio quality. [Primary-source comparison](COMPETITIVE_POSITIONING.md).

**Continuity:** formerly AI Chat Reader. Public documentation, runtime labels and new portable filenames use SpeakFromHere. For now keep `ai-chat-reader` distribution/repository slug, `chat_reader` module, existing environment flags and LOCALAPPDATA/AIChatReader/settings.json. Existing published downloads and historical notes retain their original names. Rebranding does not require resetting settings, renaming the checkout, or changing remote Git URLs. Remote rename/publication needs separate authorization.

Do not claim “first,” “only,” “best,” universal app support, instant/zero-delay playback, natural voices, precise sentence/word seeking, highlighting, or universal unreadable-block skipping. Distinguish unpublished candidate behavior from shipped releases and synthetic checks from live acceptance. This independent project is not affiliated with OpenAI. The name is the user's choice; this work is not a trademark/domain/name-availability clearance.

## 简体中文

**名称：**SpeakFromHere

**英文标语：**Read AI responses aloud from exactly where you want.

**中文辅句：**AI 回复，从你想听的位置开始。

**核心定义：**一个理解回复边界的轻量 Windows 桌面朗读工具。在已完成 AI 回复中选定支持的段落，从该段开头读到同一条回复末尾，不必选中剩余全文；保留用户主动选文朗读作为独立兜底。

**核心价值：**决定从哪里开始听，并知道该在哪里停止。不是重新做一个通用屏幕阅读器、浏览器插件或 AI 聊天客户端。

**当前真实能力：**仅段落级起读，只支持 CONTEXT.md 中记录的已检查 Codex 桌面应用包。“从你想听的位置开始”表达产品方向，不是任意字／句精确跳播。其他可复制选择可用 Alt+S。v0.3.0 预览版会跳过已识别的代码块、表格／编辑块边界、已检查的折叠文件区域及回复后的简单活动状态，并显示跳过提示与详情。用户已确认测试过的编辑块／文件跳过成功。真实 grid／表格容器和已知独立页尾控件现通过修改后提取；用户现已确认更新 Codex 后普通段落／表格测试通过，不代表所有未来布局兼容。未知或不安全边界仍拒读。播放／暂停延迟和首次开头丢字仍是待处理反馈。

v0.3.0 预览版使用 Windows 包身份及已检查的回复结构，不再绑定精确数字版本。相同版本号或相似界面不代表兼容；其他应用仍须单独检查和适配。[兼容策略](APP_COMPATIBILITY.md)。

**差异化亮点：**鼠标定位段落＋快捷键；识别已完成 AI 回复的归属与末尾；原生 Windows 桌面工作流；验证新剪贴板的主动选文兜底；本地 Windows 语音。这是定位组合，不证明功能独有或音质领先。详见[一手来源对比](COMPETITIVE_POSITIONING.md)。

**兼容性：**原名 AI Chat Reader。对外文档、运行提示和新的便携文件改用 SpeakFromHere。暂时保留 `ai-chat-reader` 分发名／仓库路径、`chat_reader` 模块、环境变量和 LOCALAPPDATA/AIChatReader/settings.json。已发布下载和历史说明保留旧名。改品牌不要求重置设置、改本地文件夹或远端 Git 地址；远端改名／发布需另行授权。

不能宣传“首个”“唯一”“最好”、通用兼容、即时／零延迟、自然人声、字句级跳播、高亮或任意不可读块都能跳过。区分未发布候选版与已发布版本、合成测试与实机验收。本项目独立开发，与 OpenAI 无隶属关系。名字由用户指定，本次不是商标／域名／名称可用性审查。
