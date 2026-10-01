# AI Chat Reader

[English](README.md) | [简体中文](README.zh-CN.md)

一个轻量的 Windows 选文朗读工具，方便收听较长的 AI 聊天回复。选中文字，按 **Alt + S** 即可开始朗读。

当前是 MVP 版本，只朗读选中的文字。后续计划通过 Windows UI Automation 识别 Codex 或 ChatGPT 的单条回复，并从鼠标所在段落开始朗读。

项目文档和下载包说明均提供英文、简体中文两版。目前程序的状态提示使用英文，尚未实现程序内的语言切换。

[下载 v0.1.0 预览版](https://github.com/JumpingAlcohol/ai-chat-reader/releases/tag/v0.1.0) · [版本计划](docs/ROADMAP.zh-CN.md)

## 播放控制

| 快捷键 | 功能 |
| --- | --- |
| `Alt + S` | 朗读选中文字，替换当前朗读 |
| `Alt + P` | 暂停；再按一次从暂停处继续 |
| `Alt + X` | 停止朗读，程序保持运行 |
| `Alt + Shift + Q` | 退出程序 |
| 在终端中按 `Ctrl + C` | 退出程序 |

暂停时选择新文字并开始朗读，会立即播放新的内容。停止会清除本次朗读位置；使用 `Alt + S` 开始朗读其他文字。没有正在朗读的内容时，按 `Alt + P` 不会改变语音状态，只会显示提示。

## 工作方式

1. 在 Codex、ChatGPT、浏览器或其他应用中选中文字。
2. 按 `Alt + S`，然后松开两个按键。程序会等待按键松开，再发送 `Ctrl + C`。
3. 程序确认剪贴板更新后，显示 `Reading: ...` 预览，并使用 Windows 语音朗读新文字。

复制失败时，程序会显示 `No new text copied...`，不会朗读旧剪贴板内容。复制操作会替换剪贴板内容，与普通复制相同。

## 运行程序

### Windows 便携版

如果已有打包好的 `AIChatReader.exe`，双击即可启动。程序已经包含 Python 和依赖。保持状态窗口打开或最小化，然后使用上面的快捷键。启动前，先退出已经在 Python 终端中运行的朗读器。

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
.\.venv\Scripts\python.exe -m pip install -e ".[build]"
.\scripts\build.ps1
```

输出文件为 `outputs/AIChatReader.exe` 和 `outputs/AIChatReader-Windows-x64.zip`。ZIP 包包含可执行文件和从 `docs/` 复制的两份使用说明。打包配置生成单个可执行文件，保留控制台状态窗口、本地 Windows 语音和全局快捷键。中间构建文件位于 `work/`。

构建采用 [PyInstaller 单文件打包](https://pyinstaller.org/en/stable/usage.html)。

独立检查打包后的程序前，先退出正在运行的朗读器，然后运行：

```powershell
.\scripts\test-executable.ps1
```

此检查仅将可执行文件复制到新的测试目录，以隐藏窗口连续启动两次，通过 Windows 消息队列检查空闲时暂停、停止和正常退出，并确认退出后可以再次注册快捷键。它不能替代手动选文和声音检查。

## 从段落读到回复末尾：当前状态

2026-10-01 的首次实际无障碍界面检查只返回了窗口容器，没有取得当前桌面应用中的聊天正文或回复边界。因此，段落到回复末尾的朗读功能尚未实现。需要先取得可靠的正文来源并确认回复边界，才能启用此功能；选文朗读和播放控制可以独立使用。
