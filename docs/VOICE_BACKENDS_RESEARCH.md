# 可选神经语音后端调研

核对日期：2026-10-04。只查阅一手资料；未安装、下载或运行模型，未向演示站或服务上传聊天正文。以下是候选方案，不是 SpeakFromHere 已实现的能力；自然度、Windows 启动时间和长文稳定性均未实测。

## 结论

可行，但这些通常是“模型＋合成引擎”，不是可以直接放进当前 Windows SAPI 声源下拉框的安装包。推荐先单独试听官方公开样例，再为合适的模型增加一个可选本地后端，保留 SAPI。优先评估 Kokoro 是基于体量、语言和接口的部署适配推断，不是音质排名。

## 候选比较

| 候选 | 官方能力及许可证 | 接入与 Windows 注意事项 |
| --- | --- | --- |
| Kokoro | 82M 参数；基础版本有中英文等声源，另有专门的 `Kokoro-82M-v1.1-zh` 中英模型。代码、这两个官方模型页均标注 Apache-2.0；发布时仍须保留所选模型及依赖的许可材料。[代码](https://github.com/hexgrad/kokoro)、[基础模型](https://huggingface.co/hexgrad/Kokoro-82M)、[中英模型](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh) | Python `KPipeline` 生成音频；官方源码有 CPU/CUDA 选择。Windows 的 eSpeak-ng 安装另有说明，中文需相应 `misaki[zh]` 前端。不能只下载声源 `.pt` 就脱离模型使用；模型文件不等于 SAPI token。[源码](https://github.com/hexgrad/kokoro/blob/main/kokoro/pipeline.py)、[安装说明](https://github.com/hexgrad/kokoro)、[中文用法](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh#usage) |
| Piper（OHF-Voice 当前维护分支） | 本地神经 TTS，提供英语、简体中文等独立声源。当前引擎是 GPL-3.0；声源许可另查每个 `MODEL_CARD`，不能把整个声源目录视为统一许可。[引擎](https://github.com/OHF-Voice/piper1-gpl)、[声源说明](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md) | 每个声源需 `.onnx` 与 `.onnx.json`。Python API 可输出 WAV 或音频块，CUDA 为可选；PyPI 有 Windows x64 wheel。许可核对是公开分发前置事项，不在此判断最终法律兼容性。[Python API](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/API_PYTHON.md)、[官方 PyPI](https://pypi.org/project/piper-tts/) |
| Qwen3-TTS | 0.6B/1.7B 系列，支持中、英等 10 种语言；CustomVoice 有预设声线，其他型号用于声音设计或克隆。代码与核对的 0.6B CustomVoice 模型分别标注 Apache-2.0。[代码](https://github.com/QwenLM/Qwen3-TTS)、[模型](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice) | Python `qwen-tts` 生成音频；官方样例主要使用 CUDA/BF16/FlashAttention。FlashAttention 官方仍提示 Windows 编译需要更多测试。较大模型与 GPU 优化依赖使它更适合作为后续评估项；这不代表不能在 Windows 或 CPU 上运行，也不是本机性能结论。[官方用法](https://github.com/QwenLM/Qwen3-TTS#quickstart)、[FlashAttention](https://github.com/Dao-AILab/flash-attention#installation-and-features) |

特别注意：Piper 中文 `huayan` 的模型卡把训练数据许可证记为 **Unknown**，不应未经进一步核实就随公共便携包分发；其他声源也需逐个核对。[具体模型卡](https://huggingface.co/rhasspy/piper-voices/blob/main/zh/zh_CN/huayan/medium/MODEL_CARD)

中文／英文支持不等于任何声线、任意混合句都可靠。Kokoro 的中英版本还明确说明并非对前版的全面升级；它减少了部分旧声线。Qwen 建议优先使用声线的母语。数字、英文缩写、代码、长回复和首句需专门验收。[Kokoro 中英模型说明](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)、[Qwen 预设声线说明](https://github.com/QwenLM/Qwen3-TTS#custom-voice-generate)

## 官方试听入口

- [Kokoro 官方演示](https://huggingface.co/spaces/hexgrad/Kokoro-TTS)；[中英模型公开样例目录](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh/tree/main/samples)。
- [Piper 维护者链接的公开声源样例](https://rhasspy.github.io/piper-samples/)。
- [Qwen 官方演示](https://huggingface.co/spaces/Qwen/Qwen3-TTS)。

可先听已有公开样例。在线演示需要输入文字时，只用无隐私的测试句，不粘贴私人对话。没有独立听感对照前，不宣传这些后端比当前声音更自然或保证真人感。

## “在线声源”与本地模型

这里的“在线”指：程序把待朗读文字发给远端服务，由服务器生成音频再返回；“本地”指模型下载到电脑后在本机合成。开源模型也可以由别人托管成在线服务；同一个模型既能本地也能在线。因此“开源”“离线”“免费”是不同概念。

在线方案省去本机模型推理负担，但需要网络，可能按字符／音频计费，有额度、密钥、服务可用性及数据处理政策需要核对。自行托管也有服务器成本。本地方案没有逐次云 API 费用，但占磁盘、内存与计算资源；第一次下载仍需联网。具体供应商价格和隐私政策须在选定服务后另查，不能由“开源”推定。

## SpeakFromHere 接入建议（尚未实施）

1. 保留当前段落提取／回复边界；只替换“文字 → 音频”的后端。模型不扩大 Alt+E 的应用兼容范围。
2. 后端输出音频后由可控播放器负责暂停、继续、停止、倍速；不能直接沿用所有 SAPI COM 控制。取消旧合成、避免 GUI 卡顿和长文分段也要设计及测试。
3. 先用独立环境及公开测试句评估一个 Kokoro 中英文声源，测冷启动、首音、长文和取消；无需先克隆真人声音。
4. 模型按需下载，不默认塞进小便携包；明确来源、版本、校验和、许可证及离线状态。下载／安装需用户另行同意。
5. 若以后做在线后端，明确告知文字将发送到哪里、费用和数据政策，由用户主动启用；不能把本地失败静默转成云端上传。

本次仅调研，不安装模型、不修改播放实现、不推送或发布。
