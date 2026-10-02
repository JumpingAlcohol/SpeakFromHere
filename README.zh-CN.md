# SpeakFromHere

[English](README.md) | [简体中文](README.zh-CN.md)

**Read AI responses aloud from exactly where you want.**

**AI 回复，从你想听的位置开始。**

SpeakFromHere 是面向 **Windows 桌面 AI 工作流**、理解回复边界的轻量朗读工具，目前聚焦已检查的 Codex 桌面版本。把鼠标放在支持的段落上，按 **Alt + E**，从该段开头读到同一条已完成 AI 回复的末尾，不必拖选到回答最后。其他可复制文字可选中后按 **Alt + S**。

“从你想听的位置开始”表达产品方向：当前预览版按**段落开头**起读，不是任意字词或句子精确跳播，也不支持所有 Codex／ChatGPT 版本。

## SpeakFromHere 的差异化亮点

- **从这里读，不必从头重听：**在支持的回复中选定想听的段落，而不是重播整条回答。
- **理解回复边界，不是朗读整个界面：**确认一条已完成 AI 回复的归属与结束位置，不把整个窗口和无关控件拼起来读。
- **保留桌面工作流：**独立 Windows 小工具，不是浏览器插件，也不要求换到另一个 AI 聊天网站。
- **两条明确路径：**鼠标定位＋快捷键读段落；用户主动选文作为另一条兜底路径。复制失败不读旧剪贴板。
- **默认本机语音：**使用 Windows SAPI，无需云端声源密钥。这是与其他工具共享的设计选择，不宣称隐私优势独有或声音已自然化。

亮点在于这套工作流的组合，不是“首个”“唯一”“最好”。[codex-read-aloud](https://github.com/cobibean/codex-read-aloud) 描述 macOS／最近一条回复朗读；[Echo](https://chromewebstore.google.com/detail/echo-read-x-chatgpt-subst/acmcamiebaibkbafoancpkdapcijoine) 描述浏览器回复控制与可点击转录；[2lazy2read](https://2lazy2read.com/) 描述 Windows 选文朗读。功能有重叠。详见[带来源的对比](docs/COMPETITIVE_POSITIONING.md)和[品牌定义](docs/BRAND.md)。

本项目独立开发，非 OpenAI 官方产品。当前延迟、开头丢字及布局限制已列入[问题记录](docs/KNOWN_ISSUES.md)。本地候选版现可跳过已识别的不可读块，并明确提示；不是无条件忽略所有未知结构。

## 预览版状态

v0.2.0 新增针对已检查桌面应用版本的段落到回复末尾朗读，源码和便携程序均已通过用户手动验收。这仍是支持范围明确受限的预览版；保留只支持选文朗读的 v0.1.0 作为旧版兜底。

项目文档和下载包说明均提供英文、简体中文两版。新悬浮播放器支持保存中英文界面选择；终端输出及详细诊断仍使用英文。

当前工作区推进基于 v0.2.1 设置的 **v0.3.0 悬浮播放器候选版**。后续解析修改新增有边界的跳过及省略提示；播放延迟／开头吞字仍待处理。这是本地候选版，未发布下载。`Alt + S` 和 `Alt + E` 保持固定，不开放其他应用。

[下载 v0.2.0 预览版](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.2.0) · [旧版 v0.1.0](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.1.0) · [版本计划](docs/ROADMAP.zh-CN.md)

原名 **AI Chat Reader**。保留仓库地址、Python 分发名 `ai-chat-reader`、模块 `chat_reader`、测试环境变量及 `%LOCALAPPDATA%\AIChatReader\settings.json`。已发布的 v0.1.0／v0.2.0 下载名称与文件不改。当前本地 GUI 候选包位于 `outputs/v0.3.0/SpeakFromHere/`，旧候选包分开保留。没有重命名远端仓库或发布新版本。

## 悬浮播放器（v0.3.0 候选版）

**完整解压 ZIP**，让 `reader-worker/` 与两个主程序留在同一目录，再双击 `SpeakFromHere.exe`：小播放器置顶显示在当前显示器工作区右下角，避开任务栏，无需终端。拖动标题可移动窗口。请先退出其他朗读器。不要只移动 exe，段落读取需要旁边的辅助程序文件夹。

- 用 `Alt + S` 读取新选文，或指向支持的段落按 `Alt + E`。点击播放器不会猜测新的选文或起点。
- 主按钮在朗读时暂停／继续；空闲时从头重播最近一次成功提交的文字，首次朗读前禁用。停止会取消朗读，但保留内存中的文字供重播；退出后清空，不保存朗读历史。
- `−`／`+` 调整 SAPI 语速（-10..10），显示慢／标准／快，不标精确倍数。改动立即提交，不重新开始朗读。用户报告当前声源会在播放中逐渐变速；响应取决于声源／缓冲，尚未独立测量。不能断言所有声源都立即生效，或都必须等到下次朗读。
- `中文`／`EN` 切换并保存界面语言。`⚙` 修改暂停／停止／退出键，需重启生效；重置必须确认，会替换已保存偏好。
- `—` 隐藏到通知区域，点击托盘图标恢复；`×` 退出、停止语音并释放快捷键。普通播放器按钮不抢原应用焦点；设置窗口为了输入会接受焦点。
- 错误／警告时点**详细信息**，可展开并选中完整英文提示，不再受两行预览限制。不会自动复制、保存或上传。身份查询错误包含失败的 Windows API 和数字错误码，排查拒读时只需提供这段错误。

橙色**已跳过…**提示说明省略的类型／数量，包括起读段落之前的省略项；**详细信息**列出回复块序号，以及位于起点前还是剩余回复中。不把文件名或被跳过的文字放进提示，只保存在内存。暂停／重播保留，新读取替换。块序号不是屏幕位置；这不是原文高亮或同步进度跟踪。

本候选版不增加开机启动、新声源、按句跳播或原文高亮。用户已确认可编辑块和已编辑文件区域跳过成功。真实表格示例的拒读已定位到 grid／工具栏容器及独立页尾按钮；严格限定的修改已有合成回归测试，用户在更新 Codex 后确认普通段落／表格测试通过。详见[候选版说明](docs/releases/v0.3.0.md)。

## 播放控制

| 快捷键 | 功能 |
| --- | --- |
| `Alt + S` | 朗读选中文字，替换当前朗读 |
| `Alt + P` | 暂停；再按一次从暂停处继续 |
| `Alt + X` | 停止朗读，程序保持运行 |
| `Alt + Shift + Q` | 退出程序 |
| 在终端模式中按 `Ctrl + C` | 退出程序 |
| `Alt + E`（便携版／源码 `--gui` 或 `--paragraphs`） | 从鼠标所在段落读到所属 AI 回复末尾 |

暂停时新读取会替换暂停的内容。停止会清除位置；GUI 播放按钮可从头重播上次文字。空闲时 `Alt + P` 不会重播。

## 工作方式

1. 在 Codex、ChatGPT、浏览器或其他应用中选中文字。
2. 按 `Alt + S`，然后松开两个按键。程序会等待按键松开，再发送 `Ctrl + C`。
3. 程序确认剪贴板更新后，显示 `Reading: ...` 预览，并使用 Windows 语音朗读新文字。

复制失败时，程序会显示 `No new text copied...`，不会朗读旧剪贴板内容。复制操作会替换剪贴板内容，与普通复制相同。

## 运行程序

### Windows 便携版

双击新的 `SpeakFromHere.exe` 启动悬浮界面，已包含 Python、Tk 和依赖。`SpeakFromHereConsole.exe` 是高级终端入口，用于诊断及设置命令；不要同时运行两者。

两个新便携入口均默认启用 `Alt + E`。当前构建位于 `outputs/v0.3.0/SpeakFromHere/`，旧文件分开保留。v0.1.0 下载仍只支持选文朗读。

ZIP 包含 `SpeakFromHere.exe`、`SpeakFromHereConsole.exe`、`QuickStart.en.txt` 和 `QuickStart.zh-CN.txt`。请先解压再运行。二进制文件只放在被忽略的 `outputs/`，不提交到 Git。

### 从源码运行

需要 Windows 10/11 和 Python 3.11 或更高版本。程序使用本地安装的 Windows SAPI 语音，无需 API 密钥或在线语音服务。

GUI 还需 Python 可选的 Tkinter 组件（通常包含在 Windows Python 安装包中）及 paragraph 扩展。完成下方环境配置后运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\pythonw.exe -m chat_reader.app --gui
```

`pythonw.exe` 不打开终端。开发时可用 `python.exe` 加 `--gui`，或使用下方原有终端命令。

首次克隆后，在项目文件夹中创建虚拟环境并安装依赖：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

如果没有 Python 启动器 `py`，可改用 `python -m venv .venv`。开发时使用的本地虚拟环境不包含在仓库中。

在项目文件夹中打开 PowerShell，运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m chat_reader.app
```

运行期间保持 PowerShell 窗口打开。选中文字后按 `Alt + S`，再松开两个按键。再次触发会朗读新的选择，并替换正在播放的内容。

退出时，在终端中按 `Ctrl + C`（先取消终端文字选择），或在任意应用中按 **Alt + Shift + Q**。程序会停止语音、释放快捷键，并显示 `SpeakFromHere stopped.`。

如果旧版程序无法退出，点击对应 VS Code 终端的垃圾桶图标关闭它，再打开新终端运行上面的命令。一次只运行一个朗读器实例。

## 首次手动检查

GUI 先用 `Alt + S` 连续读三段不同选文，点击暂停／继续、停止／播放，改语速后启动新文字，切换语言并重启，隐藏到托盘再恢复，最后点 `×` 退出。在已检查应用中重测 `Alt + E` 首段／中段／末段。留意开头字和已知延迟；静音自动测试不能代替听感验收。下面是终端模式检查。

1. 启动朗读器。在聊天窗口中选中 `Hello! This is my first Python project.`，不要在终端中选择。
2. 按 `Alt + S` 并松开两个按键，确认终端预览包含这句话，再听声音是否正确。
3. 换一句话，再触发快捷键；重复第三次。
4. 按 `Alt + Shift + Q`，确认显示 `SpeakFromHere stopped.`，并回到终端提示符。
5. 重新启动，检查在终端中按 `Ctrl + C` 也能退出。

测试播放控制时，选中一段较长的文字并开始朗读。按 `Alt + P` 暂停，再按一次继续。按 `Alt + X` 停止，终端应保持运行。换一段文字，按 `Alt + S` 再次朗读；也请测试暂停时选择新文字并开始朗读。

目标应用必须支持通过 `Ctrl + C` 复制选中文字。Windows 也会限制向以管理员权限运行的应用模拟输入；排查复制失败时，可先在普通权限窗口中测试。

## 自动测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Windows 集成测试需要手动启用。先关闭正在运行的朗读器，确保全局快捷键可用，再在普通桌面终端中运行：

```powershell
$env:CHAT_READER_WINDOWS_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:\CHAT_READER_WINDOWS_TESTS
```

集成测试使用临时音频文件，或仅将测试语音实例静音；不会播放可听见的语音，也不会改变系统音量。

`CHAT_READER_GUI_TESTS=1` 启用原生播放器／托盘测试；`CHAT_READER_UIA_TESTS=1` 和 `CHAT_READER_PORTABLE_TESTS=1` 启用隔离 UIA／打包检查。先退出朗读器，启用所需标志，运行测试后清除。GUI 测试只创建自己的窗口和临时配置，不抓取私人应用。

## 构建 Windows 可执行文件

在 Windows 上创建虚拟环境后，运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\scripts\build.ps1
```

输出在 `outputs/v0.3.0/SpeakFromHere/`：无终端的 `SpeakFromHere.exe`、高级 `SpeakFromHereConsole.exe`、`reader-worker/`、`SpeakFromHere-Windows-x64.zip` 和 `SHA256SUMS.txt`。无需另装 Python。ZIP 包含两个入口、完整读取辅助程序及来自 `docs/` 的两份规范说明。两入口启动同一个轻量读取程序，不打开终端或另一个播放器，避免每次解包／载入完整朗读器。须完整解压并保留目录结构，中间文件位于 `work/`。

构建采用 [PyInstaller](https://pyinstaller.org/en/stable/usage.html)：主入口为单文件，读取辅助程序为单目录。

请在 Tcl/Tk 可用的正常 Windows 桌面环境中构建。检测不到 Tk 时 spec 会拒绝继续，避免交付缺少 GUI 的包。受限环境／失败构建后，可用 `scripts/build.ps1 -Clean` 刷新缓存。

独立检查打包后的程序前，先退出正在运行的朗读器，然后运行：

```powershell
.\scripts\test-executable.ps1
```

此脚本连续两次检查终端入口，使用隔离设置并确认系统实际快捷键占用。启用后，`tests/test_portable_gui.py` 单独启动 GUI 两次，检查可见、不抢焦点且无终端的窗口，只向测试窗口发送控制，检查退出／释放快捷键及 ZIP 内容。`tests/test_portable_worker.py` 检查独立无终端读取进程的 UIA 和重定向管道。均不改个人偏好，不能替代真实聊天／声音验收。

## 阅读设置（v0.2.1，v0.3.0 扩展）

GUI 可调整语速／语言并打开设置窗口；高级使用仍可用命令。

先退出正在运行的朗读器。在项目文件夹中运行：

```powershell
.\.venv\Scripts\python.exe -m chat_reader.app --show-settings
.\.venv\Scripts\python.exe -m chat_reader.app --set-rate 2 --set-hotkey 'pause=Alt+J'
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

或者在便携包解压目录中打开 PowerShell：

```powershell
.\SpeakFromHereConsole.exe --show-settings
.\SpeakFromHereConsole.exe --set-rate 2 --set-hotkey 'pause=Alt+J'
.\SpeakFromHere.exe
```

设置命令只保存／显示后退出，不启动语音、读取或快捷键。改动需重启，不影响正在运行的实例。语速是 -10（慢）到 10（快）的整数，默认 0，不是速度倍数，实际听感取决于声音。参考 [微软 SAPI Rate](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ms723606(v=vs.85))。

只允许修改 `pause`、`stop`、`exit`，格式为 `Alt+字母` 或 `Alt+Shift+字母`（A-Z）。重复 `--set-hotkey` 可一起修改多个控制。重复／不支持的键、与固定 `Alt+S`／`Alt+E` 的冲突会在保存前被拒绝。不做运行中重新绑定。启动显示实际控制键，测试时使用它们代替前文默认值。其他应用仍可能占用格式有效的键：启动明确指出冲突，释放已取得的键并退出，不会悄悄禁用控制。

源码和便携版共用 `%LOCALAPPDATA%\AIChatReader\settings.json`。schema 2 在语速／控制绑定之外新增 `language`，不保存聊天或凭据。schema 1 可直接读取，只有主动保存才升级。**切换版本前请备份设置：**v0.2.1 不认识 schema 2，会警告并退回默认值。保存采用原子替换。文件不存在时使用默认值，不自动创建；无效／不可读文件保留并警告／使用默认值，拒绝直接更新。备份后可明确确认 GUI 重置或用 `--reset-settings` 替换。`--settings-file PATH` 可指定隔离配置，不改变段落支持范围。

手动验收尚待完成：保存语速 2 和暂停键 `Alt+J`，重启，核对启动显示与听感，用新键暂停／继续，重复选文及首段／中段／末段朗读，然后停止、退出并重新启动。不支持的内容仍须提示 “Use Alt + S”，不能自动复制／发声。需要时可用 `--reset-settings` 恢复默认值。

段落进程启动及结果收集现均不占用控制线程，坐标在处理命令时采样。暂停／停止／新读取能取消尚在启动的任务，迟到进程仍会回收，旧结果不会触发朗读。20 秒期限包含启动时间。退出先释放控制，但程序关闭可能短暂等待系统启动返回，以回收它的子进程；不据此宣称修复 SAPI 或选文起读／暂停延迟。

待处理用户反馈：Alt+S 也可能起读延迟，暂停频繁延迟，首次朗读可能吞掉开头的一两个字；原因尚未确认。本地候选版现可跳过已识别的不可读区域并明确提示；未知、受保护或边界不明结构仍可能整条拒读。详见[问题记录与验收要求](docs/KNOWN_ISSUES.md)。候选版手动验收仍未完成。

本地 v0.3.0 候选版现已修正 GUI／读取进程之间的显示缩放坐标不一致，原问题会定位到其他应用并报身份错误。鼠标取点、UIA 点定位及段落边界使用一致的物理像素坐标，不改变 Windows 缩放设置、不放宽身份检查。原生回归测试覆盖开发机器的缩放桌面；仍需重测真实聊天。此修正不代表上面的播放及不支持内容问题已解决。

## 从段落读到回复末尾：当前状态

2026-10-01，用户确认源码和便携模式的首／中／末段起读、同一回复末尾、切换起点／回复及控制均正常。那个历史预览版拒绝表格／编辑块；新本地候选版的省略规则见下方，须独立验收。更广泛的应用、电脑和语言兼容性尚未确认。

本地包已通过两次独立启动／控制／退出检查、独立打包 UIA 验证，以及启用 Windows 集成检查的全部 88 项测试。ZIP 内两份说明与原始文档一致，压缩包校验值已验证，没有包含捕获的私人聊天。

### 从源码运行段落预览版

先退出原来的朗读器，在项目文件夹中运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

保持目标窗口可见，把鼠标放在已完成的 AI 回复的普通正文上，不用选择或点击。按 `Alt + E`，读取期间保持鼠标不动。应当从该段开头读到同一条回复末尾；仅移动鼠标不会自动朗读。分别测试首段、中间段、末段，再换另一条回复，确认连续朗读、暂停／继续、停止、退出和 `Alt + S` 仍能正常使用。

范围和保护措施：

- 当前本地 v0.3.0 候选版验证 Windows 返回的包家族 `OpenAI.Codex_2p2nqsd0c76g0`，以及捕获进程是否是该已注册包的 `app/ChatGPT.exe`。数字版本变化不再直接拒读，但已检查的回复结构仍须通过完整性、归属、段落起点和完成状态检查。其他应用、无包身份／仿冒名称程序、改变或不安全的布局仍不支持；这不是通用 Codex／ChatGPT／浏览器兼容。旧下载仍保留原来的精确版本限制。详见[应用兼容策略](docs/APP_COMPATIBILITY.md)。中文结构已有本地检查；英文标记仅有合成测试覆盖。
- 支持普通段落、标题、行内文字／链接和已识别的列表项。列表项作为起点；跳过代码块及已确认的非文本叶节点分隔线。鼠标指向代码、分隔线、用户消息、按钮或输入框时会拒绝读取。
- 已识别的 Table（50036）表格、已检查的 `group/app-widget` 表格容器（包含正确类型的 grid 与限定工具栏）、已知 `group/writing-block-surface` 编辑块容器、已检查的折叠文件摘要及连续文件行、简单“复制”页尾后活动状态容器，会省略而不读取其内容。代码块省略也会提示。测试过的编辑块／文件跳过已由用户确认；用户在更新 Codex 后确认普通段落／表格测试通过。展开／改变的区域仍可能拒读。鼠标指向被跳过块，不会自动跳到下一段；可复制内容请手动用 `Alt + S`。
- 已知独立“重新生成回复／更多操作”页尾按钮，仅在同一回复“复制”已确认后，且为无保护、正确样式的叶节点时忽略，不能证明回复完成。中文标签已实机检查，英文对应标签仅有合成覆盖。未知按钮或隐藏子节点仍拒读。
- 未知／受保护结构、回复归属不明、正在生成或检查不完整仍拒读；Alt+E 失败不会自动复制。可跳过类型不能证明回复完成、隐藏内部回复标记或跨到下一条回复。
- 同一回复的“复制”页尾已确认后，纯 24 小时时间及 `星期四23:43`／`Thursday 23:43` 这类星期时间可识别为元数据，不朗读、也不能作为起点。只接受无保护的文本叶节点；未知块仍拒读。中文标签已在本地检查，完整英文星期名称只有合成测试覆盖。缩写、AM/PM 及其他未检查日期格式不假定兼容。
- 若旧回复自身的完成页脚及同一对话结构内后续 AI 回复标记均可确认，新回复正在生成不会挡住这条旧回复。当前正在生成的回复仍不可读；这不代表已实现通用的不可读模块跳过。
- 使用物理屏幕坐标，读取在独立进程中运行，20 秒超时。新读取会替换待完成的检查；暂停、停止和退出会取消检查，避免迟到的结果重新启动朗读。等待新检查期间，原有语音继续播放，除非主动停止或暂停。
- 段落读取不点击、不复制、不保存聊天文件、不上传文字。文字仅保存在本机内存中，并交给 Windows SAPI。只有下面独立的检查命令会保存私人诊断 JSON。终端预览最多 100 个字符，朗读使用完整的提取内容。

源码模式不加 `--paragraphs` 时保持正常 MVP 行为，不注册 `Alt + E`。本地 v0.2.0 可执行文件默认启用段落读取；旧版 v0.1.0 下载包没有此功能。

### 检查实际段落

在项目文件夹中安装可选检查依赖，然后运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.inspect_paragraph
```

在五秒内，把鼠标移到一条已完成的 AI 回复的普通段落上，无需点击或选中文字。保持目标应用可见，不要让其他窗口遮住该段落。命令会读取鼠标位置和无障碍结构，保存到 `work/paragraph-probe.json`，不会改剪贴板、点击、发声、注册快捷键或上传数据。

本地 JSON 包含应用文字，请保密，不要上传，更不能提交到仓库。`work/` 已被忽略。终端只显示检查状态，不输出捕获到的聊天。普通不可编辑容器未提供密码状态属性时，可以使用 UIA 的默认状态；密码控件及状态不明的控件会被遮蔽，跳过其子节点，并标记检查不完整；鼠标直接指向这类控件时会拒绝检查。达到节点数、深度或时间限制时，也会标记或拒绝不完整检查；原生读取在独立进程中运行，超过 20 秒会超时退出。出现 `verified reply: False` 是正常的：诊断数据不等于已经支持段落朗读。

检查工具始终显示 `verified reply: False`：它只是通用诊断，不是播放判定。`--paragraphs` 启用的是独立的实验性播放适配；检查工具本身永远不会启用快捷键。

只检查测试程序自己创建的隐藏窗口、不读取其他应用的 Windows UIA 测试：

```powershell
$env:CHAT_READER_UIA_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_uia_windows.py -v
Remove-Item Env:\CHAT_READER_UIA_TESTS
```

实现参考：[微软 UIA 鼠标点定位](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomation-elementfrompoint)、[UIA 屏幕坐标](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-screenscaling)、[UIA 元素属性](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-automation-element-propids)及 [comtypes 客户端文档](https://comtypes.readthedocs.io/en/stable/client.html)。

构建完成后，在普通桌面终端中检查打包的读取进程：

```powershell
$env:CHAT_READER_PORTABLE_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_portable_worker.py -v
Remove-Item Env:\CHAT_READER_PORTABLE_TESTS
```

此检查在隔离临时目录中测试旧的内部无终端读取入口及新的完整辅助程序，短暂显示不抢焦点的合成自有窗口，确认不支持应用被拒绝，且不启动朗读或另一个播放器。不会检查私人聊天或其他应用。受限沙箱可能阻挡跨进程 UIA，请在正常桌面环境中运行；不能代替便携程序的真实聊天／声音检查。
