"""Headless player state and persisted GUI preferences; no chat history on disk."""
from dataclasses import replace
from collections import Counter
from chat_reader.settings import Settings, load_settings, save_settings


TEXT = {
    "en": {"play": "Play", "pause": "Pause", "resume": "Resume", "stop": "Stop",
           "ready": "Ready", "playing": "Reading", "paused": "Paused", "checking": "Checking paragraph",
           "error": "Could not read", "warning": "Settings warning", "settings": "Settings",
           "speed": "Speed", "slow": "Slow", "normal": "Normal", "fast": "Fast",
           "next": "Voice response to speed changes may lag", "guide": "Alt + S  Selection   ·   Alt + E  Paragraph",
           "empty": "Select text or point at a paragraph, then use the shortcut.",
           "subtitle": "AI reply reader · Local Windows voice", "hide": "Hide to tray", "exit": "Exit",
           "save": "Save", "restart": "Control-key changes apply after restarting.", "language": "Language",
           "reset": "Reset settings", "reset_confirm": "Replace saved preferences with defaults?",
           "saved": "Settings saved", "diagnostic": "Details", "cancel": "Cancel",
           "voice": "Local voice", "default_voice": "Windows default",
           "voice_preview": "Save voice & preview", "voice_unavailable": "Saved voice unavailable",
           "voice_hint": "Voice changes apply now while stopped. Preview saves the voice only.\nLocal SAPI voices; no automatic language switching or downloads.",
           "voice_fallback": "Saved voice unavailable; using Windows default. Choose another voice.",
           "skipped": "Skipped {count} · {kinds}", "code": "Code", "table": "Table",
           "editor": "Editable block", "edited_files": "Edited-files region", "system_status": "System status"},
    "zh-CN": {"play": "播放", "pause": "暂停", "resume": "继续", "stop": "停止",
              "ready": "就绪", "playing": "正在朗读", "paused": "已暂停", "checking": "正在检查段落",
              "error": "无法朗读", "warning": "设置警告", "settings": "设置",
              "speed": "语速", "slow": "慢", "normal": "标准", "fast": "快",
              "next": "语速变化可能稍有延迟", "guide": "Alt + S  选文朗读   ·   Alt + E  段落朗读",
              "empty": "选中文字或指向段落，再按对应快捷键开始。",
              "subtitle": "AI 回复朗读 · 本地 Windows 声音", "hide": "收起到托盘", "exit": "退出",
              "save": "保存", "restart": "控制键修改后需重启生效。", "language": "语言",
              "reset": "重置设置", "reset_confirm": "将已保存偏好替换为默认值？",
              "saved": "设置已保存", "diagnostic": "详细信息", "cancel": "取消",
              "voice": "本机声源", "default_voice": "Windows 默认",
              "voice_preview": "保存声源并试听", "voice_unavailable": "已保存声源不可用",
              "voice_hint": "停止朗读后切换立即生效；试听只保存声源选择。\n仅本机 SAPI 声源，不自动切换语言或下载声音。",
              "voice_fallback": "已保存声源不可用，正在使用 Windows 默认；请选择其他声源。",
              "skipped": "已跳过 {count} 处 · {kinds}", "code": "代码块", "table": "表格",
              "editor": "可编辑块", "edited_files": "已编辑文件区域", "system_status": "系统状态条"},
}


def skip_summary(skipped, language):
    if not skipped:
        return ""
    labels = TEXT[language]
    counts = Counter(item.kind for item in skipped)
    kinds = ", ".join(f"{labels[kind]} ×{count}" for kind, count in counts.items())
    return labels["skipped"].format(count=len(skipped), kinds=kinds)


def skip_details(skipped):
    if not skipped:
        return ""
    rows = ["Skipped content (ordered reply blocks, not screen coordinates):"]
    for item in skipped:
        location = "before the starting paragraph" if item.before_start else "in the remaining reply"
        rows.append(f"Reply block {item.ordinal}: {TEXT['en'][item.kind]} — {location}")
    rows.append("Skipped content is not spoken. Use Alt + S on a copyable selection to hear it.")
    return "\n".join(rows)


def bottom_right(work_area, width, height, margin=16):
    left, top, right, bottom = work_area
    return max(left, right - width - margin), max(top, bottom - height - margin)


def play_button(speaker, language):
    state = speaker.playback_state()
    key = {"playing": "pause", "paused": "resume", "idle": "play"}[state]
    return TEXT[language][key], state != "idle" or bool(speaker.last_text)


class PlayerPreferences:
    def __init__(self, path, value, speaker):
        self.path, self.value, self.speaker = path, value, speaker

    def update(self, **changes):
        value = replace(load_settings(self.path), **changes)
        return self._save(value)

    def reset(self):
        return self._save(Settings())

    def _save(self, value):
        previous_rate = self.speaker.engine.Rate
        voice_changed = value.voice_id != self.value.voice_id
        previous_voice = self.speaker.engine.Voice if voice_changed else None
        previous_id, previous_warning = self.speaker.voice_id, self.speaker.voice_warning
        voice_applied = False
        try:
            if voice_changed:
                self.speaker.set_voice(value.voice_id)
                voice_applied = True
            self.speaker.set_rate(value.rate)
            save_settings(self.path, value)
        except Exception:
            self.speaker.set_rate(previous_rate)
            if voice_applied:
                self.speaker.engine.Voice = previous_voice
                self.speaker.voice_id, self.speaker.voice_warning = previous_id, previous_warning
            raise
        self.value = value
        return value
