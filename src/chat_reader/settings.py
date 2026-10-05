"""Local reading preferences; never store selected text or captured chats."""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import tempfile
from types import MappingProxyType


DEFAULT_HOTKEYS = {"pause": "Alt + P", "stop": "Alt + X", "exit": "Alt + Shift + Q"}


class SettingsError(ValueError):
    """A settings document or requested change is unsafe/unsupported."""


def parse_hotkey(chord):
    if not isinstance(chord, str):
        raise SettingsError("Hotkeys must be Alt + letter or Alt + Shift + letter.")
    normalized = re.sub(r"\s+", "", chord).upper()
    match = re.fullmatch(r"ALT\+(SHIFT\+)?([A-Z])", normalized)
    if not match:
        raise SettingsError("Hotkeys must be Alt + letter or Alt + Shift + letter (A-Z).")
    # Windows MOD_ALT=0x0001, MOD_SHIFT=0x0004; MOD_CONTROL=0x0002.
    return (5 if match[1] else 1, ord(match[2]))


def hotkey_label(chord):
    modifiers, key = parse_hotkey(chord)
    return ("Alt + Shift + " if modifiers == 5 else "Alt + ") + chr(key)


@dataclass(frozen=True)
class Settings:
    rate: int = 0
    hotkeys: object = field(default_factory=lambda: dict(DEFAULT_HOTKEYS))
    language: str = "en"
    voice_id: str = ""  # Empty means the local SAPI default, not an online service.

    def __post_init__(self):
        if (not isinstance(self.voice_id, str) or len(self.voice_id) > 1024
                or self.voice_id != self.voice_id.strip()
                or any(ord(char) < 32 or ord(char) == 127 for char in self.voice_id)):
            raise SettingsError("Voice ID must be text without control characters (up to 1024 characters).")
        if self.language not in ("en", "zh-CN"):
            raise SettingsError("UI language must be en or zh-CN.")
        if type(self.rate) is not int or not -10 <= self.rate <= 10:
            raise SettingsError("Rate must be an integer from -10 to 10.")
        if not isinstance(self.hotkeys, (dict, MappingProxyType)) or set(self.hotkeys) != set(DEFAULT_HOTKEYS):
            raise SettingsError("Hotkeys must contain only pause, stop and exit.")
        normalized = {action: hotkey_label(chord) for action, chord in self.hotkeys.items()}
        used = {(1, ord("S")), (1, ord("E"))}
        for action, chord in normalized.items():
            binding = parse_hotkey(chord)
            if binding in used:
                raise SettingsError(f"{action}: {chord} conflicts with another binding or reserved Alt + S / Alt + E.")
            used.add(binding)
        object.__setattr__(self, "hotkeys", MappingProxyType(normalized))


def settings_path():
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise SettingsError("LOCALAPPDATA is unavailable; use --settings-file PATH explicitly.")
    return Path(root) / "AIChatReader" / "settings.json"


def load_settings(path):
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return Settings()
    except UnicodeError as error:
        raise SettingsError("Settings file must use UTF-8; file left unchanged.") from error
    def unique_fields(pairs):
        document = {}
        for key, value in pairs:
            if key in document:
                raise SettingsError("Settings file contains duplicate fields; file left unchanged.")
            document[key] = value
        return document
    try:
        document = json.loads(content, object_pairs_hook=unique_fields)
    except (ValueError, RecursionError) as error:
        raise SettingsError("Settings file is not valid JSON; file left unchanged.") from error
    if not isinstance(document, dict):
        raise SettingsError("Settings file is not an object.")
    version = document.get("schema_version")
    if type(version) is not int or version not in (1, 2, 3):
        raise SettingsError("Unsupported settings schema_version; expected 1, 2 or 3. File left unchanged.")
    allowed = ({"schema_version", "rate", "hotkeys"} | ({"language"} if version >= 2 else set())
               | ({"voice_id"} if version == 3 else set()))
    if set(document) - allowed:
        raise SettingsError("Settings file has unknown fields.")
    return Settings(rate=document.get("rate", 0), hotkeys=document.get("hotkeys", DEFAULT_HOTKEYS),
                    language=document.get("language", "en"), voice_id=document.get("voice_id", ""))


def save_settings(path, value):
    value = Settings(rate=value.rate, hotkeys=value.hotkeys, language=value.language, voice_id=value.voice_id)
    document = {"schema_version": 3, "rate": value.rate, "hotkeys": dict(value.hotkeys),
                "language": value.language, "voice_id": value.voice_id}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="settings-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
