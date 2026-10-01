# AI Chat Reader

[English](README.md) | [简体中文](README.zh-CN.md)

一个轻量的 Windows 选文朗读工具，方便收听较长的 AI 聊天回复。选中文字，按 **Alt + S** 即可开始朗读。

v0.2.0 新增针对已检查桌面应用版本的段落到回复末尾朗读，源码和便携程序均已通过用户手动验收。这仍是支持范围明确受限的预览版；保留只支持选文朗读的 v0.1.0 作为旧版兜底。

项目文档和下载包说明均提供英文、简体中文两版。目前程序的状态提示使用英文，尚未实现程序内的语言切换。

[下载 v0.2.0 预览版](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.2.0) · [旧版 v0.1.0](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.1.0) · [版本计划](docs/ROADMAP.zh-CN.md)

## 播放控制

| 快捷键 | 功能 |
| --- | --- |
| `Alt + S` | 朗读选中文字，替换当前朗读 |
| `Alt + P` | 暂停；再按一次从暂停处继续 |
| `Alt + X` | 停止朗读，程序保持运行 |
| `Alt + Shift + Q` | 退出程序 |
| 在终端中按 `Ctrl + C` | 退出程序 |
| `Alt + E`（v0.2.0 便携预览版；源码加 `--paragraphs`） | 从鼠标所在段落读到所属 AI 回复末尾 |

暂停时选择新文字并开始朗读，会立即播放新的内容。停止会清除本次朗读位置；使用 `Alt + S` 开始朗读其他文字。没有正在朗读的内容时，按 `Alt + P` 不会改变语音状态，只会显示提示。

## 工作方式

1. 在 Codex、ChatGPT、浏览器或其他应用中选中文字。
2. 按 `Alt + S`，然后松开两个按键。程序会等待按键松开，再发送 `Ctrl + C`。
3. 程序确认剪贴板更新后，显示 `Reading: ...` 预览，并使用 Windows 语音朗读新文字。

复制失败时，程序会显示 `No new text copied...`，不会朗读旧剪贴板内容。复制操作会替换剪贴板内容，与普通复制相同。

## 运行程序

### Windows 便携版

如果已有打包好的 `AIChatReader.exe`，双击即可启动。程序已经包含 Python 和依赖。保持状态窗口打开或最小化，然后使用上面的快捷键。启动前，先退出已经在 Python 终端中运行的朗读器。

v0.2.0 预览版默认启用 `Alt + E`，本地构建位于 `outputs/v0.2.0/`。v0.1.0 下载包仍只支持选文朗读；新旧版本分开放置，避免覆盖之前的可用文件。

便携 ZIP 包包含 `AIChatReader.exe`、`QuickStart.en.txt` 和 `QuickStart.zh-CN.txt`。请先解压，再启动程序。可执行文件在本地生成到 `outputs/`；生成的二进制文件不提交到 Git。

### 从源码运行

需要 Windows 10/11 和 Python 3.11 或更高版本。程序使用本地安装的 Windows SAPI 语音，无需 API 密钥或在线语音服务。

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

退出时，在终端中按 `Ctrl + C`（先取消终端文字选择），或在任意应用中按 **Alt + Shift + Q**。程序会停止语音、释放快捷键，并显示 `AI Chat Reader stopped.`。

如果旧版程序无法退出，点击对应 VS Code 终端的垃圾桶图标关闭它，再打开新终端运行上面的命令。一次只运行一个朗读器实例。

## 首次手动检查

1. 启动朗读器。在聊天窗口中选中 `Hello! This is my first Python project.`，不要在终端中选择。
2. 按 `Alt + S` 并松开两个按键，确认终端预览包含这句话，再听声音是否正确。
3. 换一句话，再触发快捷键；重复第三次。
4. 按 `Alt + Shift + Q`，确认显示 `AI Chat Reader stopped.`，并回到终端提示符。
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

## 构建 Windows 可执行文件

在 Windows 上创建虚拟环境后，运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[build,paragraph]"
.\scripts\build.ps1
```

输出文件为 `outputs/v0.2.0/AIChatReader.exe` 和 `outputs/v0.2.0/AIChatReader-Windows-x64.zip`，ZIP 校验值保存在 `SHA256SUMS.txt`。ZIP 包含可执行文件和从 `docs/` 复制的两份说明。单个可执行文件包含 Windows 语音、UI Automation 绑定和全局快捷键；内部读取进程不会启动另一个朗读器或注册快捷键。中间构建文件位于 `work/`。

构建采用 [PyInstaller 单文件打包](https://pyinstaller.org/en/stable/usage.html)。

独立检查打包后的程序前，先退出正在运行的朗读器，然后运行：

```powershell
.\scripts\test-executable.ps1
```

此检查仅将可执行文件复制到新的测试目录，以隐藏窗口连续启动两次，通过 Windows 消息队列检查空闲时暂停、停止和正常退出，并确认退出后可以再次注册快捷键。它不能替代手动选文和声音检查。

## 从段落读到回复末尾：当前状态

2026-10-01，用户确认源码模式的首段／中间段／末段起读、停在同一条回复末尾、换回复／换段落、连续朗读、暂停／继续、停止、退出及选文兜底，在已检查的桌面应用中均正常；随后也确认了便携程序可用。表格、可编辑写作块、用户消息和其他应用仍不支持段落朗读，与预期范围一致。自动测试和结构离线回放也通过；更广泛的应用、电脑和语言兼容性尚未确认。

本地包已通过两次独立启动／控制／退出检查、独立打包 UIA 验证，以及启用 Windows 集成检查的全部 88 项测试。ZIP 内两份说明与原始文档一致，压缩包校验值已验证，没有包含捕获的私人聊天。

### 从源码运行段落预览版

先退出原来的朗读器，在项目文件夹中运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[paragraph]"
.\.venv\Scripts\python.exe -m chat_reader.app --paragraphs
```

保持目标窗口可见，把鼠标放在已完成的 AI 回复的普通正文上，不用选择或点击。按 `Alt + E`，读取期间保持鼠标不动。应当从该段开头读到同一条回复末尾；仅移动鼠标不会自动朗读。分别测试首段、中间段、末段，再换另一条回复，确认连续朗读、暂停／继续、停止、退出和 `Alt + S` 仍能正常使用。

范围和保护措施：

- 原型只接受已检查的桌面应用包 `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0`（`app/ChatGPT.exe`）。应用更新、浏览器或其他版本会被拒绝，直到重新检查。这不代表通用 ChatGPT／浏览器支持。中文界面结构已在本地捕获；英文标记仅经过合成测试。
- 支持普通段落、标题、行内文字／链接和已识别的列表项。列表项作为起点；跳过代码块。鼠标指向代码、用户消息、按钮或输入框时会拒绝读取。
- 回复中含可编辑写作块、表格或未知结构时，目前会整条拒绝，不会只读一部分；请改用 `Alt + S`。正在生成、起点不明确和检查不完整时也会提示原因，不会改读旧剪贴板。
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

此测试仅将可执行文件复制到临时目录，短暂显示一个由测试自己创建、不抢焦点的合成窗口，确认打包的 UIA 读取进程拒绝这个不支持的应用，不启动语音或另一个朗读器。不检查私人聊天或其他应用。受限沙箱可能阻止跨进程 UIA，请在正常桌面环境中运行；它不能替代便携程序的真实聊天与声音检查。
