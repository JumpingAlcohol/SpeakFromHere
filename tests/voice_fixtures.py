"""External SAPI token boundary; production catalog/storage remain real."""
from test_app import RecordingEngine


class Token:
    def __init__(self, token_id, name, language):
        self.Id, self.name, self.language = token_id, name, language

    def GetDescription(self):
        return self.name

    def GetAttribute(self, name):
        if name != 'Language':
            raise ValueError(name)
        return self.language


class Tokens:
    def __init__(self, values):
        self.values = values
        self.Count = len(values)

    def Item(self, index):
        return self.values[index]


class VoiceEngine(RecordingEngine):
    def __init__(self):
        super().__init__()
        self.tokens = [Token('token-A', 'Same name', '804'),
                       Token('token-B', 'Same name', '409;809')]
        self.Voice = self.tokens[0]

    def GetVoices(self):
        return Tokens(self.tokens)
