"""Local SAPI voice metadata; no registry writes or network speech services."""
from dataclasses import dataclass
import locale
from comtypes import COMError


@dataclass(frozen=True)
class VoiceOption:
    id: str
    name: str
    language: str


def voice_options(engine):
    tokens = engine.GetVoices()
    options = []
    for index in range(tokens.Count):
        token = tokens.Item(index)
        try:
            identifiers = token.GetAttribute('Language').split(';')
        except (OSError, ValueError, COMError):
            identifiers = []  # Optional attribute; the token can still be used.
        languages = []
        for identifier in identifiers:
            try:
                languages.append(locale.windows_locale.get(int(identifier, 16), identifier))
            except ValueError:
                languages.append(identifier)
        options.append(VoiceOption(token.Id, token.GetDescription(), ', '.join(languages)))
    return tuple(options)
