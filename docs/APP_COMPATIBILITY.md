# Application compatibility / 应用兼容策略

## English

The local v0.3.0 candidate replaces the exact Codex version path gate with two independent requirements. Older published readers remain unchanged.

1. **Application identity:** from the captured document's PID, open one limited-query process handle and read its image path, package family and package full name. Resolve that exact package's registered install directory. Accept only `OpenAI.Codex_2p2nqsd0c76g0` and the image at that directory's `app/ChatGPT.exe`. Unpackaged apps, lookalike names/folders, other families and failed identity queries do not fall back to path guessing. This trusts Windows-reported package membership; it is not a separate signature audit or a guarantee against a compromised local OS.
2. **Reply structure:** retain the existing complete Chrome capture, unique identities, hidden assistant marker, unambiguous supported paragraph, explicit reply completion, protected-text and same-reply ending checks. Current generating replies and unknown/unsafe structures still reject. No window flattening or automatic clipboard fallback.

The numeric version remains available in `ProcessIdentity.package_full_name` for local diagnostics, but is not a permission check. A trusted compatible Codex update can pass without editing a version allowlist; a changed layout or executable location may still require an adapter update. Other applications are **not** automatically supported by a similar UI. A future adapter must first establish its own trusted application identity and inspected reply structure, then may use this version-independent policy.

Implementation: [windows_context.py](../src/chat_reader/windows_context.py), [paragraph_worker.py](../src/chat_reader/paragraph_worker.py), [codex_adapter.py](../src/chat_reader/codex_adapter.py). Package queries follow Microsoft documentation for [GetPackageFamilyName](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefamilyname), [GetPackageFullName](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagefullname) and [GetPackagePathByFullName](https://learn.microsoft.com/en-us/windows/win32/api/appmodel/nf-appmodel-getpackagepathbyfullname).

Verification scope: real local package membership for `26.928.4866.0`; synthetic old/current/future version suffix reading and rejection boundaries; handle/buffer/error tests. A fresh 846-node nontruncated capture passed application identity but rejected its current generating state. An explicitly in-memory simulated-idle replay accepted its 38-character suffix (withheld). This is structural diagnostic evidence, not live readiness, audio acceptance or universal compatibility. Original private snapshots remain unchanged in ignored `work/`; production generation checks are unchanged. See `CONTEXT.md` for rebuilt artifact checks and outstanding manual acceptance.

## 简体中文

本地 v0.3.0 候选版将精确 Codex 版本路径限制改为两个独立要求；旧的已发布朗读器不变。

1. **应用身份：**从捕获文档的 PID 打开一个只查询身份的进程句柄，读取程序路径、包家族及完整包名，再取得该包注册的安装目录。只接受 `OpenAI.Codex_2p2nqsd0c76g0` 以及该目录中的 `app/ChatGPT.exe`。没有包身份、名称／目录仿冒、其他包家族或身份查询失败时，不退回路径猜测。这信任 Windows 返回的包归属，不是额外的数字签名审计，也不能保证已被入侵的本地系统可信。
2. **回复结构：**保留 Chrome 检查完整性、唯一节点身份、隐藏 AI 标记、明确的支持段落起点、回复完成标记、受保护文字及同一回复末尾检查。当前正在生成的回复、未知或不安全结构仍拒读；不拼读整个窗口，不自动复制兜底。

数字版本仍保存在 `ProcessIdentity.package_full_name` 中供本地诊断，但不作为放行条件。可信且结构兼容的 Codex 更新无需修改版本白名单；布局或程序位置变化仍可能需要更新适配器。界面相似的其他应用**不会**自动支持。未来新增应用须先建立独立可信身份验证和已检查的回复结构，之后可采用相同的版本无关策略。

实现：[windows_context.py](../src/chat_reader/windows_context.py)、[paragraph_worker.py](../src/chat_reader/paragraph_worker.py)、[codex_adapter.py](../src/chat_reader/codex_adapter.py)。包查询依据上方三个 Microsoft 官方 API 文档。

验证范围：本机 `26.928.4866.0` 的真实包归属；合成旧版／当前版／未来版后缀读取和拒绝边界；句柄、缓冲区及错误测试。新 846 节点完整检查已通过应用身份，但因当前生成状态拒读；明确标注的内存“空闲状态模拟”回放可提取 38 字符后缀（不显示正文）。这是结构诊断证据，不是实时可读、声音验收或通用兼容。原私人文件留在忽略的 `work/` 中且未改动，正式代码的生成状态保护不变。重新打包检查及待完成手动验收见 `CONTEXT.md`。
