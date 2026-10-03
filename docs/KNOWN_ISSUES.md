# Known issues and requested behavior / 已知问题与期望行为

Recorded and updated 2026-10-01 during candidate feedback. Status and evidence are tracked per issue; open reports are not completed fixes. The initial recording-only task changed documentation; subsequent diagnosis/implementation evidence is noted below. Automated test success is not manual acceptance.

记录并更新于 2026-10-01 候选版反馈阶段。每项分别记录状态和证据，待处理反馈不代表已完成修复。最初仅记录的任务只改文档，后续诊断／实现证据分别见下文；自动测试通过不等于手动验收通过。

## ISSUE-001 — Playback latency and missing opening characters / 播放延迟与开头吞字

### English

- Release preparation 2026-10-02: user confirms the tested new-bundle workflow works and explicitly authorizes v0.3.1 publication. Final source checks pass 199 tests without skips; embedded GUI/console pass 99 each, helper 66, plus two portable startup/control/exit runs. Earlier candidate and pending-listening entries below are chronological evidence, superseded for this tested workflow only. ISSUE-001 is not universally closed; no all-device or long-idle remedy is claimed.
- v0.3.1 diagnosis 2026-10-02: the user confirms v0.3.0 has delayed pause, immediate resume and first-playback opening loss on an external wired speaker. No Bluetooth/device cause is assumed. Nine baseline SAPI Pause calls returned in 0.01–0.29 ms, but a separate muted native device-position loop proved output kept advancing: actual stopping took approximately 648–1798 ms. API-return timing alone was misleading. Phoneme-boundary and smaller-buffer changes did not meet the provisional 200 ms output budget; direct SpAudio state changes stalled resume and were rejected.
- Local v0.3.1.dev0 candidate: GUI/console share an owned SAPI waveform controller using pointer-sized native handles. Waveform pause/restart retain the queued audio and listening position; stop/new reads reset only that voice's buffers before SAPI cancellation, avoiding paused-writer deadlocks and old-buffer replay. Test calls took about 1–9 ms and held real output position. Four timeout-isolated native regressions first failed on advancing paused output, then passed including resume, replacement, stop/replay, paused rate changes, early pause and exit. Existing/fallback SAPI semantics remain for non-waveform/unopened outputs; do not claim all devices or zero delay. This is local, not published. The user recorded “stops quickly” in a synthetic listening test; real GUI/Alt+S/Alt+E repeated listening acceptance remains pending.
- Opening loss remains unverified/unfixed. A Windows GUI adaptation of the diagnosis step/capture loop compared fresh same-voice plain playback (A) against a trusted synthetic 350 ms silence prefix (B), playing only on button presses. Local observations: A uncertain, B complete, new pause fast. This is not a red/green proof of the missing-prefix bug. The experimental silence is not in production. Only observation codes are stored in ignored work/, never system audio or chat text; no hardware cause is concluded.
- Starting selected-text playback with **Alt + S** can also be delayed, not just paragraph playback with Alt + E.
- The user reports a delay on essentially every pause action. Playback start and pause responsiveness both need investigation.
- The first playback may omit the opening one or two characters.
- Opening-loss cause is unconfirmed. The previously measured Windows paragraph-worker process-creation delay does **not** establish the cause of selected-text/pause delays or missing opening audio. The native pause-output issue now has separate reproduction evidence above.
- User follow-up after the first listening loop: first A possibly lost “一”, later plays complete; suspects only the first utterance after process startup. A second diagnostic uses a new process for every single utterance (A/B/B/A, equal 10 s quiet gaps), with only local observation codes. Await results before startup hypotheses or a production prefix. Synthetic/owned tests never publish private chats.
- Completed fresh-process comparison: all four A/B/B/A observations lost the opening “一”, including both 350 ms silence variants. This supersedes the earlier inconclusive same-process impression; silence-only startup padding is rejected as an evidenced fix. File-only synthesis verifies the 350 ms later signal onset, not audible acceptance. Further completed listening: the exact same generated WAV loses “一” on first playback and is complete on repeat; first SAPI speech without purge also loses “一” and repeats completely. The saved syllable exists; playback/output startup is implicated, not a particular driver or speaker. A two-case 400/800 ms mild audible-primer experiment queues PCM and text on the same SAPI output; file-only validation confirms the exact PCM prefix precedes speech. BOTH fresh-process listening trials preserve “一”. User reports the first cue was perhaps inaudible and the second audible; this does not establish exactly what happened to the cue or general reliability. No hardware blame, recording or remote upload.
- User approved the temporary first-read cue on 2026-10-02. Local v0.3.1.dev1 queues one faded, modest 400 ms PCM cue before the first nonempty speech per reader launch, through the same SAPI voice/output. Launch/settings/empty or failed captures remain silent; resume, replay and later reads do not repeat it. Speech-submission failure cancels queued audio without marking new replay text successful. No settings schema/UI expansion or system-volume/device change. A real factory file regression first failed (missing 400 ms prefix), then passed checking cue amplitude/fade/duration, full plain-text speech at configured rate and no repeated cue. A real text-error test first left the cue playing, then passed after cancellation. File-only mute characterization found SpeakStream ignores SpVoice.Volume (cue peak 3276 at volume 0); explicitly scaling this voice's cue now yields zero and keeps native tests inaudible. Muted native checks include pause/stop/replacement during the first cue. All 199 opt-in source/native/GUI/UIA/portable tests pass, no skips. Bundle QA and actual Alt+S/Alt+E cold-start listening acceptance remain separate; ISSUE-001 is not universally closed, and clipping after long idle is not addressed. Not published.
- Acceptance: check cold first playback and repeated playback through both paths, audible opening characters, repeated pause/resume during long passages, replacement while paused, stop and exit. Measure actual user-visible delays and agree on a responsiveness threshold; mocked calls or silent audio tests alone cannot establish audible acceptance.

### 简体中文

- 发布准备（2026-10-02）：用户确认新版所测流程正常，明确授权发布 v0.3.1。最终源码 199 项无跳过通过；包内 GUI／终端各 99 项、辅助程序 66 项及两次便携启动／控制／退出通过。下方早期候选与待听感验收记录是时间顺序证据，仅在本次所测流程范围内由新确认取代。ISSUE-001 未全面关闭，不宣称所有设备或长时间闲置问题已解决。
- v0.3.1 诊断（2026-10-02）：用户确认 v0.3.0 仅暂停延迟，继续播放无延迟，外接有线音响仍有首次开头丢字。不假定蓝牙／设备原因。九次基线 SAPI Pause API 虽在约 0.01–0.29 毫秒返回，独立静音原生播放位置检查却确认仍在播放，实际停止约 648–1798 毫秒；仅测 API 返回会误导。改音素边界／缩小缓冲未达到暂定 200 毫秒播放预算；直接修改 SpAudio 状态导致恢复卡住，已放弃。
- 本地 v0.3.1.dev0 候选版：GUI／终端共用自有 SAPI 波形控制，以完整指针宽度获取原生句柄。暂停／继续保留音频与位置；停止／新读取先清除该声源缓冲，再交给 SAPI 取消，避免暂停写入者死锁及旧缓冲重播。测试暂停调用约 1–9 毫秒，真实输出位置保持。四项有超时的独立原生回归先因暂停后仍播放而失败，现包含恢复、替换、停止／重播、暂停时变速、提早暂停和退出的检查通过。非波形／尚未打开输出保留原 SAPI 行为；不承诺所有设备或零延迟。仍是本地候选，未发布。用户在合成听感测试中记录“很快停下”；真实 GUI／Alt+S／Alt+E 反复听感验收仍待完成。
- 开头丢字仍未验证／未修复。把诊断技能的 step／capture 流程适配为 Windows 测试 GUI，对比新建相同声源的原样播放 A 与加可信 350 毫秒静音的合成句子 B，仅按钮点击发声。本地观察为 A 不确定、B 完整、新暂停很快；这不构成吞字问题的失败／通过证明。实验静音未加入正式程序。观察选项只保存在被忽略的 work/，不录音／读取聊天，不归咎硬件。
- 不只是 Alt + E 段落起读；**Alt + S 选文朗读也可能起读延迟**。
- 用户反馈**基本每次暂停都有延迟**，起读和暂停的响应都需排查。
- **第一次朗读可能吞掉最开始的一两个字**。
- 开头丢字原因尚未确认。此前测得的 Windows 段落读取进程启动延迟，**不能直接解释选文／暂停延迟或开头丢字**；原生暂停输出问题现有上方独立复现证据。
- 首次听感对照后的用户补充：第一遍 A 可能漏“一”，之后完整，怀疑仅程序启动后的第一次出声。第二个诊断每次新建进程、仅读一次，按 A／B／B／A、相同 10 秒安静间隔对比，只存本机观察选项；等待结果后再做启动假设／正式前缀。合成／自有测试不公开私人聊天。
- 新进程对照已完成：A／B／B／A 四次均漏开头“一”，包括两次 350 毫秒静音，取代此前同进程的不确定印象，不能把纯静音当作已证实修复。文件验证了 350 毫秒声音起点延后，不等于听感通过。后续听感也已完成：完全相同的 WAV 首遍漏“一”、第二遍完整；SAPI 首次不清队列也首遍漏“一”、第二遍完整。音节已存于文件，问题在播放输出起步环节，但不能锁定驱动或音响。400／800 毫秒柔和有声提示音实验在同一 SAPI 输出中排队播放提示音与正文，文件验证提示音 PCM 完整位于正文之前；两个新进程听感均完整读出“一”。用户第一组好像未听到提示音、第二组听到，不能据此确定提示音如何变化或宣称普遍可靠。不归咎硬件、不录音／上传。
- 用户于 2026-10-02 同意暂时首读提示音。本地 v0.3.1.dev1 每次启动后仅首次非空语音前，通过同一 SAPI 声源／输出排队播放 400 毫秒柔和、淡入淡出的 PCM 提示音。打开程序／设置／空选文或读取失败不发声；继续、重播、后续朗读不重复。语音提交失败取消已排队音频，失败文本不成为新重播内容。不增加设置 schema／UI 或修改系统音量／设备。真实工厂文件回归先因缺少 400 毫秒前缀失败，现检查提示音幅度／淡入淡出／长度、配置语速下完整纯文本正文及不重复提示音通过。真实提交错误测试先因提示音继续播放失败，补取消后通过。文件静音检查发现 SpeakStream 忽略 SpVoice.Volume（音量 0 时提示音峰值仍 3276），明确按本声源音量缩放后输出为零，原生测试现不出声。原生静音检查包含首段提示音期间暂停／停止／替换；199 项完整源码／原生／GUI／UIA／便携测试通过，无跳过。包内检查与实际 Alt+S／Alt+E 冷启动听感是独立验收，ISSUE-001 未全面关闭，不处理长时间闲置后的潜在吞字。未发布。
- 验收：两条路径的首次冷启动、连续起读、开头完整出声、长文反复暂停／继续、暂停时替换文字、停止与退出。记录实际听感延迟，再确定可接受的响应标准；模拟调用或静音音频测试不能代替声音验收。

## ISSUE-002 — One unsupported block rejects the whole reply / 一个不兼容块导致整条回复拒读

### English

- Latest 2026-10-02: user authorized bounded skipping with explicit omission disclosure, not silent omission. Implemented locally for recognized code/Table (50036)/writing-block wrappers, inspected collapsed edited-files groups and simple post-Copy activity metadata. Unknown/protected/incomplete/ambiguous structures still reject. Hovering a skip region never guesses the next paragraph; selected-text fallback remains manual. The historical report/acceptance requirements below still govern unverified layouts.
- User acceptance 2026-10-02 after Codex client update: reports the requested ordinary-paragraph/table tests work without issues; tested editable-block/file skipping was already confirmed. The inspected table case is accepted, not all unknown layouts or future client releases. Exact updated package version was not captured; ISSUE-001's original latency/opening-audio reports are not independently closed by this confirmation. Source commit/push authorized, not a new GitHub Release.
- Actual edited-files capture: 1050 nodes, complete; first blocker was `group/turn-diff-header`, followed by three file-row buttons and one view action. In-memory differential accepted after removing just those five known nodes. No filenames, paths or reply body saved/uploaded. The adapter treats the inspected contiguous region as one skipped item; orphan rows, hidden markers, protected descendants and changed/expanded structures reject. A post-fix user-positioned check accepted real prose and returned one `edited_files` omission at reply-block ordinal 3. This is silent structural verification, not portable/audio acceptance.
- `ReadingPlan` carries only prose and typed omission records (ordered reply-block number, before-start flag). Both worker routes serialize it; pipe validation is bounded and malformed metadata fails rather than losing the notice. The amber GUI notice summarizes all target-reply omissions, including those before the start; Details provides the English list without skipped text or filenames. Pause/replay retain it; replacement/cancellation do not attach stale notices to a new result. No capture/history/upload, original-text coloring or actual-audio progress tracking added.
- Earlier user feedback 2026-10-02: editable-block and edited-files skipping succeeds in the local candidate. A supplied table example with prose before/after still fails; full error, actual application and UIA shape need inspection. Do not generalize this editor acceptance to every layout or mark all of ISSUE-002 resolved. Original-text highlighting remains later separately verified work in both roadmaps; ISSUE-001 remains open.
- Table diagnosis 2026-10-02: twice-reproduced 546-node complete Codex capture identified a `group/app-widget _TableContainer_*` containing grid/Table (50036) plus a two-action overlay, then standalone post-Copy leaf buttons labeled Regenerate response and More actions in Chinese. In-memory removal of only these three nodes restored bounded prose. The narrow widget and known footer-leaf rules now pass six new regressions (three positive failures before implementation), including changed CSS hashes, suffix order/omission metadata, no cell starts, protection/process/hidden-marker/unknown-control guards. No body/cell text saved or output. A fresh post-fix user-positioned capture accepted the same-length bounded prose suffix and reported exactly one table omission at ordinal 2. The user subsequently confirmed ordinary/table reading after a client update; no blanket skipping or table narration.
- A table or other incompatible block can currently make paragraph reading reject the entire assistant reply, including otherwise readable prose.
- Critical Codex desktop case: after editing code, the reply shows a footer such as **“edited N files”**. The user reports that this block causes rejection of almost every code-editing reply. Its exact accessibility structure and rejection path have not been captured/verified for this report.
- Requested behavior: **skip the unreadable block and continue with readable text in the same assistant reply**, instead of vetoing the whole reply. Prioritize the edited-files footer, tables and other recognized unsupported blocks, including editable writing blocks.
- This request is to skip content, not to read tables/editors/diffs, support another app/build, or read across an entire conversation. Keep reply ownership and ending boundaries unchanged.
- Future implementation must identify skip-safe block types in the inspected app. Do not blindly ignore every unknown node, guess ownership, cross into another reply, accept incomplete capture or expose protected/editable text. If boundaries cannot be verified, retain explicit rejection and the manual Alt + S fallback. No automatic copying after Alt + E failure.
- Acceptance: readable text before and after a table/editor remains readable in order; a code-editing reply with the edited-files footer reads its prose and omits the footer; first/middle/last valid paragraph starts stay within that reply. Skipped blocks do not speak UI metadata or edit code. Replies with no readable suffix report that clearly; unsafe/ambiguous layouts still reject. Starting directly on a skipped block needs an explicit behavior decision before implementation.

### 简体中文

- 2026-10-02 更新 Codex 客户端后，用户确认所请求的普通段落／表格测试没有问题；编辑块／文件跳过此前已确认。已检查的表格案例通过，不代表所有未知布局或未来客户端均兼容。未记录新包精确版本；此确认不单独关闭 ISSUE-001 原延迟／开头吞字反馈。用户授权源码提交／推送，不是发布新 GitHub Release。
- 2026-10-02 最新状态：用户授权有边界的跳过及明确省略提示，不静默省略。本地已实现已识别的代码／Table（50036）／写作块容器、已检查的折叠文件组及简单“复制”页尾后活动元数据跳过。未知／受保护／不完整／边界不明结构仍拒读；鼠标指向省略区域不会猜测下一段，选文兜底仍由用户主动触发。下方历史报告及验收要求仍适用于未验证布局。
- 真实文件区域检查：1050 节点、完整；首个阻挡为 `group/turn-diff-header`，之后是三个文件行按钮及一个查看操作。内存里仅移除这五个已知节点即可恢复提取；未保存／上传文件名、路径或正文。适配器把这组已检查的连续区域作为一处省略，孤立行、隐藏回复标记、受保护子节点和改变／展开的结构仍拒读。修正后用户定位的真实检查成功提取正文，返回回复块序号 3 的一处 `edited_files` 省略。这是静音结构验证，不是便携版／声音验收。
- `ReadingPlan` 只携带正文及类型化省略记录（顺序块号、是否位于起点之前），两读取入口均序列化；管道验证有界，错误元数据拒绝而不悄悄丢弃提示。GUI 橙色提示统计目标回复内全部省略，包括起点前的块；详细信息列出英文清单，不包含省略文字或文件名。暂停／重播保留，替换／取消不会把旧提示附给新结果。不新增抓取记录／历史／上传、原文着色或实际发声进度跟踪。
- 2026-10-02 较早用户反馈：本地候选版的可编辑块和已编辑文件区域跳过成功。用户提供的前后都有正文的表格示例仍失败，需检查完整错误、实际应用及 UIA 结构。不能推断所有编辑器／布局均兼容，也不能把全部 ISSUE-002 标为解决。原文高亮仍是两份路线图中的后续独立验证功能；ISSUE-001 仍开放。
- 2026-10-02 表格诊断：两次复现的 546 节点完整 Codex 检查定位到 `group/app-widget _TableContainer_*`（内部为 grid／Table 50036 和双按钮工具栏），及“复制”后的独立“重新生成回复／更多操作”叶按钮。仅在内存移除这三个节点即可恢复同一回复正文。严格限定的表格容器和已知页尾叶节点规则现通过六项新回归测试（实现前有三个正向失败），覆盖变化的 CSS 哈希、正文顺序／跳过元数据、禁止单元格起读、保护／进程／隐藏回复标记／未知控件边界。不保存或输出正文／单元格文字。修改后的新用户定位检查已接受等长的同一回复正文后缀，报告恰好一次表格跳过（序号 2）；用户随后确认客户端更新后普通段落／表格测试通过。不是无条件跳过或表格朗读。
- 当前回复只要出现表格或其他不兼容块，段落读取就可能**拒绝整条 AI 回复**，连正常正文也无法读。
- **优先处理的严重场景**：Codex 桌面端修改代码后，回复底部出现“**已编辑 N 个文件**”一类区域。用户反馈这个块会导致几乎每条改代码的回复都不能朗读。本次反馈对应的无障碍结构和实际拒绝分支尚未捕获／验证。
- 期望改为：**跳过不可读块，继续朗读同一条回复内其余可读正文**，而不是整条拒绝。重点覆盖已编辑文件摘要、表格和其他已识别的不支持块，包括可编辑写作块。
- 这是“跳过”，不是实现表格／编辑器／代码差异朗读，也不是扩展应用或版本。用户所称“整篇对话”在本项目中仍按**当前这条 AI 回复**处理，不自动跨到其他回复。
- 后续实现须在已检查应用中识别哪些块可安全跳过。不能无条件忽略所有未知节点、猜测所属回复、跨回复、接受不完整检查，或读取受保护／可编辑内容。无法确认正文边界时仍须明确拒绝，保留用户主动选择的 Alt + S；Alt + E 失败不能自动复制兜底。
- 验收：表格／编辑块前后的普通正文按顺序朗读；包含“已编辑 N 个文件”的改代码回复能读正文、跳过该区域；首段／中段／末段起读仍停在同一回复末尾。跳过时不读界面元数据、不操作代码；后续没有可读内容时明确提示，危险／边界不清的布局仍拒绝。鼠标直接指向被跳过块时的行为，须在实现前单独确定。

## ISSUE-003 — Slow executable paragraph detection / exe 段落识别慢

### English

- Status: optimized in the local candidate; real-chat/manual target acceptance pending. Alt+E detection in the executable feels slow. Track separately from SAPI start/pause and missing audio (ISSUE-001).
- Previous local baseline against an owned nonchat window: source 1.080–1.122s, GUI worker 1.923–1.982s, console worker 1.954–2.110s. This is historical startup/small-capture evidence, not real-chat latency or proof of a particular cause.
- Follow-up owned-window baseline: GUI internal worker 3.032–3.111s, console 2.095–2.168s, source 1.218–2.206s. A capture-only one-directory prototype measured 1.060–1.245s in interleaved runs. This motivated a shared `reader-worker/` helper instead of repeatedly unpacking/importing the full reader. No UIA/reply safety rules were relaxed. Final rebuilt measurements are recorded in CONTEXT.md.
- Native process startup now runs off the control thread; regression tests cover cancellation during launch, late-child cleanup, replacement/stale results, launch errors and a timeout including startup. Both portable entries use the same helper; source pythonw launches neighboring python.exe for working redirected streams. Extract the entire ZIP.
- Acceptance: record final before/after timings and an agreed user-visible target; repeat reads and cancellation must remain correct. No performance fix published yet; owned-window speed is not real-chat latency or SAPI/audio acceptance.

### 简体中文

- 状态：本地候选版已优化，真实聊天／用户目标验收待完成。exe 的 Alt+E 段落识别体感慢；与 ISSUE-001 的语音起读／暂停延迟及丢字分开跟踪。
- 上次自有非聊天测试窗口的基础耗时：源码 1.080–1.122 秒，GUI 读取进程 1.923–1.982 秒，console 读取进程 1.954–2.110 秒。这是历史启动／小型检查证据，不是真实聊天耗时，也未确认具体原因。
- 后续自有窗口基线：GUI 内部读取进程 3.032–3.111 秒，console 2.095–2.168 秒，源码 1.218–2.206 秒；仅做读取的单目录原型交错测试为 1.060–1.245 秒。据此接入共用 `reader-worker/`，不再每次解包／导入整个朗读器。UIA／回复安全检查没有放宽，最终重打包测量见 CONTEXT.md。
- 系统进程启动现不占用控制线程；回归测试覆盖启动中取消、迟到进程回收、替换／过时结果、启动错误及包含启动的超时。两便携入口共用同一辅助程序，源码 pythonw 改用旁边的 python.exe 返回重定向结果。须完整解压 ZIP。
- 验收：记录最终优化前后耗时并确认用户可接受目标；连续读取和取消仍正确。尚未发布性能修复，自有窗口提速不等于真实聊天耗时或 SAPI／听感验收。

## ISSUE-004 — GUI rejects replies that console can read / 仅 GUI 拒读

### English

- Status: coordinate-mismatch cause captured and fixed locally; real-chat manual acceptance remains open. Some replies read in console but reject in GUI; other replies reject in both. The previous separator/generating-guard fix addresses a captured both-entry case, not proof that all GUI-only cases are solved.
- 2026-10-02 approved local metadata trace: GUI request coordinates were approximately twice the unaware helper's cursor coordinates; the actual helper was nonrestricted/non-elevated and captured another process (one target rejected package membership, another failed OpenProcess/error 5). Native owned-window tests independently reproduced incorrect hit targeting and halved paragraph bounds on the scaled desktop. Scoped per-monitor-aware calls now cover cursor sampling, UIA point lookup and cache construction; each restores its caller's thread context. No guessed scale multiplier, process-wide GUI scaling change, identity bypass or elevation. Temporary trace code/tests/marker removed; metadata archived only in ignored local work. New tests first failed then passed; rebuilt executable acceptance is recorded in CONTEXT.md. Tables/editors/edited-files and ISSUE-001 remain separate.
- Record exact executable/source versions, settings profile, target build, same pointed paragraph and detailed error; run one reader at a time. Compare capture/result routing without saving or publishing private text.
- The newly reported version-gate rejection after a Codex update is tracked as ISSUE-005; do not conflate it with this entry-specific failure.
- Latest same-point comparison: two direct reads each through GUI internal worker, console internal worker and source all succeeded with the same 160-character suffix (text withheld). GUI timings 1.552/2.562s, console 1.553/1.748s, source 0.692/1.709s. The full GUI action has not reproduced in this comparison; it does not prove the user's failure resolved.
- The user's visible detail begins `Could not read this paragraph: The pointed application's`; the rest was clipped by the two-line panel, so the exact Windows identity-query failure remains unknown. The new **Details** dialog exposes the full selectable error in memory; identity errors now retain API stage and numeric Windows code. No automatic copy, log, chat capture or upload. Request this complete error from the new candidate before attributing a cause; do not disable identity checks.
- 2026-10-02: full user error now confirms `OpenProcess failed (Windows error 5)` (access denied), before executable/package verification or reply parsing. A read-only native process-identity loop against the same 12 current Codex PIDs failed for all in the restricted tool environment (8 OpenProcess/error 5, 4 package-path/error 1168), and passed for all outside it. Both callers were non-elevated; only the failing caller reported a restricted token. This reproduces an environment-dependent identity failure, not the full user's GUI launch. Actual GUI startup source/token still needs confirmation; no parser/identity bypass, automatic elevation or runtime fix was added.
- User subsequently confirmed launching by Explorer double-click. No running reader was found during the scoped checks; request that they leave the failing GUI open for executable/helper/token inspection. The tool-sandbox reproduction is not established as their cause. Existing six identity boundary tests pass; runtime is unchanged.
- Earlier diagnostic checkpoint, before the current retry: the expected reopened GUI/bootloader were nonrestricted/non-elevated, but the transient helper was not yet observed. User-approved metadata-only instrumentation was installed after privacy/disable/I/O tests; desktop opt-ins were skipped while the player was open. The current retry and cleanup results are above; this was never a released fix.
- Acceptance: the same valid reply succeeds via both entries, both retain equivalent unsafe-layout rejection, and repeated captures/cancellation behave correctly.

### 简体中文

- 状态：已捕获坐标不一致原因并在本地修正，真实聊天手动验收仍开放。有些回复 console 能读而 GUI 拒读，另一些两者都拒读。上次分隔线／生成状态修复解决了已捕获的双入口失败，不能据此宣称所有 GUI 独有情况均已解决。
- 2026-10-02 已授权本地元数据诊断：GUI 请求坐标约为未处理缩放的辅助进程鼠标坐标的两倍；实际辅助进程非受限、非管理员，捕获了另一个进程，其中一次拒绝包身份，另一次 OpenProcess／错误 5。原生自有窗口测试独立复现错误目标及减半的段落边界。现对鼠标取点、UIA 点定位、缓存构建使用局部的按显示器缩放感知调用，每次恢复原线程状态。不猜比例、不改变 GUI 全进程缩放、不绕过身份、不提权。临时诊断代码／测试／标记已移除，元数据仅归档到本地忽略的 work。新增测试先失败后通过，重新打包验收记录见 CONTEXT.md。表格／编辑块／已编辑文件与 ISSUE-001 仍独立待处理。
- 记录准确的程序／源码版本、配置、目标应用版本、同一指向段落及完整错误；一次只运行一个朗读器。对比检查及结果传递，不保存或公开私人正文。
- 更新 Codex 后新增的版本限制拒读单列为 ISSUE-005，不与入口差异混为一谈。
- 最新同一点对比：GUI 内部读取、console 内部读取及源码各两次均成功，返回相同的 160 字符后缀（不显示正文）。GUI 为 1.552／2.562 秒，console 1.553／1.748 秒，源码 0.692／1.709 秒。该对比未复现完整 GUI 操作失败，不证明用户问题已解决。
- 用户可见错误以 `Could not read this paragraph: The pointed application's` 开头，两行面板截掉了结尾，确切 Windows 身份查询失败仍未知。新增**详细信息**窗口在内存中展示可选中的完整错误，身份错误保留 API 阶段及数字错误码。不自动复制、记录、捕获聊天或上传。归因前需取得新候选版完整错误，不能关掉身份验证。
- 2026-10-02：完整用户错误现确认为 `OpenProcess failed (Windows error 5)`（访问被拒绝），发生在程序／包身份及回复解析之前。对同一批 12 个当前 Codex 进程做只读原生身份查询：受限工具环境全部失败，其中 8 个 OpenProcess／错误 5、4 个包路径／错误 1168；退出该受限环境后全部通过。两次均非管理员，只有失败调用者带受限令牌。这复现了环境相关身份失败，不等于复现用户完整 GUI 启动；仍需确认实际启动方式／令牌。未绕过解析／身份保护，未自动提权或新增运行修复。
- 用户随后确认从资源管理器双击启动。范围内检查未发现正在运行的朗读器，已请用户保持失败 GUI 打开，检查实际程序／辅助程序／令牌。工具沙箱复现不能据此认定为用户原因；现有六项身份边界测试通过，运行代码未改。
- 此前诊断阶段（本次重试前）：重新打开的实际 GUI／启动进程均非受限、非管理员，但短暂运行的辅助进程尚未观测。经过隐私／关闭／写入失败测试后，安装用户授权的元数据诊断；播放器打开时跳过桌面测试。本次重试及清理结果见上文；临时诊断从未作为修复发布。
- 验收：同一有效回复两个入口均成功，危险布局的拒绝行为一致，重复检查及取消仍正确。

## ISSUE-005 — Codex update trips the exact-version gate / Codex 更新触发精确版本限制

### English

- Status: exact-version cause verified; now fixed in the local v0.3.0 candidate, manual audio acceptance pending. Installed metadata reports `OpenAI.Codex_26.928.4866.0_x64__2p2nqsd0c76g0`; the earlier reader required `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0` and `app/ChatGPT.exe`. Old published readers retain that gate.
- A deterministic invocation of the real `read_paragraph` with a synthetic valid capture accepts the old package path and twice rejects the updated path with `This app/build has not been inspected for paragraph reading. Use Alt + S.` Only the version path changes. This establishes the version gate, not whether the new build's real UI structure remains compatible.
- Implemented with regression tests first: query Windows package family/full name and image through one process handle, resolve the registered package directory and require its `app/ChatGPT.exe`. Numeric version is metadata, not a gate; the existing reply-owner, starting-paragraph, completion, protected-text and capture-integrity checks remain mandatory. Wrong application identity now reports a different error from unsupported layout. See [compatibility policy](APP_COMPATIBILITY.md).
- Do not merely accept any `ChatGPT.exe`, wildcard an arbitrary directory, or omit reply-boundary validation. Inspect the new build locally and test recognized/unsafe structures before broadening support. Future structural changes can still require an adapter update; no universal or permanent compatibility guarantee.
- Acceptance: a trusted updated Codex with compatible inspected structure reads the same bounded suffix; other apps, spoofed package paths, changed/ambiguous/protected/incomplete layouts reject. Verify both bundled entries, with manual Alt+S fallback and no automatic copying.
- The earlier recording-only task changed no runtime. The user subsequently authorized this compatibility implementation. Actual Windows identity for the new build passed. The fresh nontruncated 846-node capture passed identity but rejected current generation; an explicit in-memory idle simulation passed structural replay. Production generation protection is unchanged; this does not establish live/audio acceptance. See CONTEXT.md for rebuild results. Alt+S remains the manual fallback; ISSUE-001/002/003/004 remain open.

### 简体中文

- 状态：已确认精确版本限制原因；本地 v0.3.0 候选版已修复，声音手动验收待完成。本机包现为 `OpenAI.Codex_26.928.4866.0_x64__2p2nqsd0c76g0`，之前朗读器要求 `OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0` 及 `app/ChatGPT.exe`；旧已发布版本仍保留该限制。
- 使用真实 `read_paragraph` 和合成有效检查，只改变版本路径：旧路径可读，新路径连续两次报 `This app/build has not been inspected for paragraph reading. Use Alt + S.`。这确认了版本限制，不代表已检查新版的实际界面结构是否兼容。
- 已先补回归测试再实现：通过同一进程句柄查询 Windows 包家族／完整包名及程序路径，取得该包注册目录，要求其 `app/ChatGPT.exe`。数字版本只作诊断，不作限制；回复归属、段落起点、完成状态、受保护文字和检查完整性仍必须通过。应用身份错误与结构不支持现在分别提示。详见[兼容策略](APP_COMPATIBILITY.md)。
- 不能仅凭 `ChatGPT.exe` 名称放行、对任意目录使用通配符，或取消回复边界检查。扩大支持前先本地检查新版本，并覆盖可读和危险结构。未来界面结构变化仍可能需要修改适配器，不能保证永久／通用兼容。
- 验收：可信新版 Codex 的已检查兼容结构能读同一回复内的后缀；其他应用、伪造包路径、改变／模糊／受保护／不完整布局仍拒绝。验证两个便携入口，保留用户主动 Alt+S 兜底，不自动复制。
- 之前仅记录的任务未改运行逻辑；随后用户已授权兼容改造。新版真实 Windows 包身份检查通过；新 846 节点完整检查通过身份但因生成状态拒读，明确标注的内存空闲模拟通过结构回放。正式生成状态保护不变，不能据此认定实时／声音验收已完成。重打包结果见 CONTEXT.md。Alt+S 仍为手动兜底，ISSUE-001/002/003/004 仍开放。

## ISSUE-006 — Weekday-prefixed reply timestamp rejects prose / 带星期的页尾时间导致正文拒读

### English

- Status: fixed locally 2026-10-02 after user authorization; user subsequently confirmed the Chinese weekday timestamp works in real chat. Another completed reply still rejects with the same generic layout message; its cause is not yet identified. This does not reopen the independently verified timestamp cause or establish universal layout support. English real-interface acceptance remains open.
- Two user-positioned local checks reproduced that exact rejection with complete captures (950/952 nodes). The first rejected block is an unprotected, childless `description` / control type 50020 after the target's Copy footer. Boolean-only label checks confirm a Chinese weekday-prefixed clock, not a plain clock. No reply body or snapshot was saved/uploaded.
- Cause: the previous `_reply` rule recognized only a bare `HH:MM` footer. `星期四23:43` missed it and entered the generic unsupported-layout branch, rejecting the whole reply. The screenshot's ordinary paragraph, numbered list and download label were not this observed blocker.
- Minimized synthetic loop: `.venv/Scripts/python.exe -X utf8 work/repro-weekday-footer.py` failed before the fix and now passes. Nine new adapter tests cover Chinese weekday labels, full English weekday labels with English interface markers/Copy footer, same-reply completion, prose preservation, malformed labels and hidden/protected content. Weekday, invalid-clock and protected/descendant cases first failed then passed. All 30 adapter tests now pass; final full/bundled checks are recorded in CONTEXT.md.
- Narrow fix: only an unprotected, childless Text (50020) node with description/text role after a verified same-reply Copy footer qualifies. Accept valid 24-hour clocks with optional Chinese `星期` prefix or full English weekday name; never omit arbitrary prose, tables, editors or unknown nodes. Metadata is not a starting paragraph or proof of completion. Chinese labels were inspected locally; English labels have synthetic tests only. Abbreviations, AM/PM, relative dates and other uninspected formats remain unsupported, rather than guessed. No remote publication.

### 简体中文

- 状态：2026-10-02 用户授权后已在本地修正，随后确认中文星期时间在真实聊天中已正常。另一条已完成回复仍报同样的通用布局错误，原因尚未确定；不能据此推翻已独立验证的时间原因，也不代表所有布局都已兼容。英文真实界面验收仍待完成。
- 两次用户定位的本地检查均复现完全相同的错误，捕获完整（950／952 节点）。首个拒绝节点位于目标回复“复制”页尾之后，是无保护、无子节点的 `description`／控件类型 50020。只输出布尔分类的标签检查确认它是带中文星期的时间，不是纯时间。未保存／上传正文或快照。
- 原因：之前 `_reply` 只忽略单独的 `HH:MM` 页尾。`星期四23:43` 无法匹配，会进入通用的不支持布局分支，导致整条回复拒读。这次实际阻挡不是截图的普通正文、编号列表或下载标签。
- 合成最小复现：`.venv/Scripts/python.exe -X utf8 work/repro-weekday-footer.py` 修正前失败、现在通过。新增九项适配测试覆盖中文星期、带英文界面标记／Copy 页尾的完整英文星期、同一回复完成状态、正文保留、错误格式与隐藏／受保护内容。星期时间、非法时钟及保护／子节点用例均先失败再通过。全部 30 项适配测试现已通过，最终全套／打包检查见 CONTEXT.md。
- 窄修正：只有同一回复“复制”页尾已确认后，无保护、无子节点、Text（50020）类型且角色为 description/text 的节点才符合条件。接受有效 24 小时时钟，可带中文“星期”前缀或完整英文星期名称；不忽略任意正文、表格、编辑器或未知节点。时间元数据不能作为起点、不能证明回复完成。中文标签有本地检查，英文只有合成测试覆盖；缩写、AM/PM、相对日期及其他未检查格式仍不支持，不猜测。没有远端发布。

## ISSUE-007 — Activity container vetoes an earlier completed reply / 活动信息容器导致旧回复拒读

### English

- Latest 2026-10-02: a fresh user-positioned 960-node complete capture confirmed the single leaf is exactly the known compaction-status label (boolean-only classification, no saved text). It follows the target's Copy footer and precedes the next user marker; removing just this container in memory restored the original bounded suffix. A narrow, shape-based post-Copy skip is now implemented with tests for child/protection/class/completion guards. It is reported as `system_status`, never body/completion evidence. Fresh post-fix real status and portable/audio acceptance remain pending; earlier diagnostic checkpoints below are historical.
- Status: first rejecting node identified locally 2026-10-02; not fixed. After confirming the Chinese weekday timestamp correction, the user reported another completed reply with the same generic unsupported-layout error.
- User-positioned read-only capture reproduced the exact error with 956 nodes, without truncation. The actual `_reply` exception frame identifies segment index 8, after verified Copy completion: unprotected Group (50026), `outline-none`, containing another Group, then `group/activity-header`, then one unprotected Text (50020) description leaf. No body, leaf label, snapshot or URL was saved/uploaded. This is an activity container, not the previously inspected weekday timestamp leaf; its displayed label and ownership have not yet been verified.
- Synthetic minimal diagnostic `work/repro-activity-footer.py` reproduces the same error twice with a body paragraph, Copy footer and that container shape. Removing only the activity wrapper restores the synthetic bounded prose. This is synthetic isolation, not proof that removing it resolves every blocker in the real reply.
- A follow-up native check had 958 complete nodes but no unique pointed assistant paragraph, so its in-memory removal comparison did not run. Do not claim a successful real-snapshot differential or identify the container as this/next turn's duration without another user-positioned check. No runtime, safety rule or portable binary changed.
- Next: verify structural ownership and a tightly bounded metadata shape before proposing an adapter change. Never skip all unknown post-footer nodes or use an activity header as completion evidence. ISSUE-002's table/editor/edited-files skipping remains separate and unimplemented.

### 简体中文

- 2026-10-02 最新状态：新用户定位检查完整捕获 960 节点，只输出布尔分类，确认唯一叶标签确为已知“已优化对话”状态。它在目标“复制”页尾后、下一用户标记前；内存中仅移除该容器即可恢复原始有边界的后缀。本地现已实现窄范围、结构匹配的页尾后跳过，测试覆盖子节点／保护／类名／完成条件；提示为 `system_status`，不是正文或完成证据。修正后的真实状态、便携版／听感验收仍待完成；下方早期诊断节点为历史记录。
- 状态：2026-10-02 已在本机定位首个拒绝节点，尚未修复。用户确认中文星期时间修正后，另一条已完成回复仍出现相同的通用布局错误。
- 用户定位的只读检查复现完全相同的错误，共 956 节点、无截断。实际 `_reply` 异常位置是“复制”完成标记之后的第 8 个节点：无保护的 Group（50026），类名 `outline-none`，内部依次为 Group、`group/activity-header`、一个无保护的 Text（50020）description 叶节点。未保存／上传正文、叶标签、快照或链接。这是活动信息容器，不是此前检查的星期时间叶节点；显示标签及所属轮次仍待确认。
- 最小合成检查 `work/repro-activity-footer.py` 使用正文段落、复制页尾和该容器结构，两次复现相同错误；只移除活动容器即可恢复合成正文读取。这是合成隔离结果，不代表真实回复的所有阻挡都已排除。
- 第二次真实检查捕获完整（958 节点），但鼠标位置没有唯一 AI 段落，因此未执行内存移除对比。不能声称真实快照对比通过，或未经重新定位就断言它是本轮／下一轮的耗时信息。未改运行逻辑、安全规则或便携包。
- 下一步：核对结构归属及严格限定的元数据形状，再提出适配修改。不能忽略所有页尾未知节点，也不能把活动信息当作完成证据。ISSUE-002 的表格／编辑器／已编辑文件跳过仍独立且未实现。

## Milestone impact / 对版本推进的影响

Follow-up 2026-10-01: the user distinguishes GUI-only rejection from replies rejected by both entries, and reports slow executable detection. A fresh user-positioned 828-node, nontruncated local capture reproduced two independent blockers: a verified non-text leaf separator vetoed prose, and the global generating guard rejected a completed earlier reply while a later reply generated. Six regression tests first failed on the minimized synthetic repros; the narrow fixes now allow the original private snapshot to return its 195-character suffix offline. No captured text is published. Tables/editors/edited-files skipping, GUI-only failure and audible acceptance remain open; unknown/protected/ambiguous structures still reject.

Baseline timing, three interleaved runs against a test-owned nonchat window (no private capture or speech): source workers 1.080–1.122s, windowed workers 1.923–1.982s, console workers 1.954–2.110s total; native launch 0.002–0.004s. This measures startup plus a small UIA capture/rejection, not the actual chat's detection time, and does not identify unpacking, antivirus or provider costs individually. Both bundled entries showed similar overhead; no performance fix is claimed. The user also reports gradual mid-playback rate adjustment; the next-playback-only hint was corrected. Voice timing is not independently measured.

2026-10-01 追加：用户区分了只有 GUI 拒读和两个入口都拒读，并反馈 exe 识别慢。新采集的 828 节点完整本地检查复现了两处独立阻挡：已确认的非文本叶节点分隔线导致正文拒读；全局生成状态又挡住了已有后续回复的完整旧回复。先用合成最小用例确认六个回归测试中的相关失败，再做窄范围修复，原私人检查现能离线提取 195 字符后缀。不公开聊天正文。表格／编辑区／已编辑文件跳过、GUI 独有失败及声音验收仍未完成；未知、受保护、边界不清结构仍拒读。

基础耗时：只对测试拥有的非聊天窗口交错测量三次，不捕获私人内容、不发声；源码进程总耗时 1.080–1.122 秒，GUI 进程 1.923–1.982 秒，console 进程 1.954–2.110 秒；原生启动 0.002–0.004 秒。这包含启动、小型 UIA 检查及拒读，不是实际聊天识别耗时，也未分别归因到解包、杀毒或提供者成本。两个 exe 的基础开销相近，未宣称性能已修复。用户另反馈播放中语速逐渐变化，已纠正“只能下次生效”提示；实际声音响应未独立测量。

These reports keep manual acceptance open. On 2026-10-01 the user explicitly prioritized the v0.3.0 floating GUI before these fixes. GUI work may proceed, but neither issue is fixed or accepted by that milestone. Safe skipping remains a requirement, not a capability. Publication still needs explicit approval after acceptance.

这些反馈使手动验收继续保持开放。2026-10-01 用户明确要求先做 v0.3.0 悬浮 GUI，再处理问题，因此可以推进界面，但不能据此宣称两项问题已修复或验收。安全跳过仍是要求，不是现有能力。验收后发布仍需明确授权。
