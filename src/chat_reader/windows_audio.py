"""Position-preserving control of the waveform output owned by our SAPI voice.

Never changes the default device, system volume, another process or SAPI's
ISpAudio state. The borrowed waveform handle must not be closed or reused after
purging speech. Non-waveform streams retain the ordinary SAPI pause path.
"""
import ctypes
from array import array
import math

import comtypes
import comtypes.client


class _ISpMMSysAudio(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{15806F6E-1D70-4B48-98E6-3B1A007509AB}")
    _methods_ = []


def _wave_handle(output):
    """Use the native pointer-sized GetMMHandle, not automation's 32-bit LONG.

    The Windows SDK sapi.h layout is IUnknown / IStream / ISpStreamFormat /
    ISpAudio / ISpMMSysAudio: GetMMHandle is slot 28. QueryInterface proves this
    precise interface before using that slot; comtypes owns/releases its pointer.
    """
    try:
        native = output._comobj.QueryInterface(_ISpMMSysAudio)
    except (comtypes.COMError, AttributeError):
        return None  # E.g. a file stream, or a device that has not opened yet.
    pointer = ctypes.cast(native, ctypes.c_void_p)
    methods = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    get_handle = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p,
                                   ctypes.POINTER(ctypes.c_void_p))(methods[28])
    handle = ctypes.c_void_p()
    if get_handle(pointer, ctypes.byref(handle)) < 0:
        return None
    return handle.value


class WaveOutputControl:
    def __init__(self, voice):
        self.voice = voice
        self._paused_handle = None
        self._paused_output = None
        self._api = ctypes.WinDLL("winmm")
        for name in ("waveOutPause", "waveOutRestart", "waveOutReset"):
            function = getattr(self._api, name)
            function.argtypes = [ctypes.c_void_p]
            function.restype = ctypes.c_uint

    def pause(self):
        output = self.voice.AudioOutputStream
        handle = _wave_handle(output)
        if handle is None:
            return False
        code = self._api.waveOutPause(handle)
        if code in (5, 8):  # Closed handle / driver does not support this control.
            return False
        if code:
            raise RuntimeError(f"Cannot pause this voice's audio output (Windows multimedia error {code}).")
        self._paused_handle = handle
        self._paused_output = output
        return True

    def resume(self):
        if self._paused_handle is None:
            raise RuntimeError("No paused audio output to resume.")
        code = self._api.waveOutRestart(self._paused_handle)
        if code:
            raise RuntimeError(f"Cannot resume this voice's audio output (Windows multimedia error {code}).")
        self._paused_handle = None
        self._paused_output = None

    def cancel(self):
        """Discard this voice's queued buffers before SAPI purges the utterance.

        Restarting first could briefly play old buffered speech and wait for it.
        Reset wakes the paused writer without replay; only use it for cancel,
        never pause/resume where the listening position must be retained.
        """
        if self._paused_handle is None:
            raise RuntimeError("No paused audio output to cancel.")
        code = self._api.waveOutReset(self._paused_handle)
        if code:
            raise RuntimeError(f"Cannot cancel this voice's audio output (Windows multimedia error {code}).")
        self._paused_handle = None
        self._paused_output = None


class StartupCue:
    """Queue one modest 400 ms PCM cue on this voice before its first read.

    Retain the memory stream for the asynchronous queue's lifetime. There is no
    background playback, XML input, volume change or second output device.
    """
    def __init__(self, voice):
        self.voice = voice
        self._stream = None

    def queue_once(self):
        if self._stream is not None:
            return False
        rate = 22050
        frames = rate * 400 // 1000
        fade = rate * 40 // 1000
        # SpeakStream copies PCM without applying SpVoice.Volume (unlike TTS).
        # Respect this voice's level explicitly, including test-instance mute.
        peak = 3276 * int(self.voice.Volume) / 100
        samples = array("h", (
            round(peak * min(1, index / fade, (frames - 1 - index) / fade)
                  * math.sin(2 * math.pi * 660 * index / rate))
            for index in range(frames)
        ))
        stream = comtypes.client.CreateObject("SAPI.SpMemoryStream", dynamic=True)
        stream.Format.Type = 22  # SAFT22kHz16BitMono from Windows SAPI type library.
        stream.SetData(array("B", samples.tobytes()))
        self.voice.SpeakStream(stream, 1 | 2)  # Async, purge only before the cue.
        self._stream = stream
        return True


def create_voice():
    # Dynamic dispatch avoids generating SAPI wrappers on the user's machine.
    # Unlike automation's LONG MMHandle, the native interface preserves x64 bits.
    return comtypes.client.CreateObject("SAPI.SpVoice", dynamic=True)
