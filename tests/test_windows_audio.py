"""Opt-in, muted device-position tests through the actual console runtime factory.

Each scenario runs in a disposable process: a broken native pause/cancel path
must fail with a timeout instead of wedging the test runner or user's reader.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


def load_runtime():
    if os.environ.get("CHAT_READER_AUDIO_ARCHIVE"):
        # Build QA must exercise the bytecode actually shipped in each entry,
        # not accidentally import the editable source checkout in its children.
        import importlib
        import importlib.util
        import marshal
        import types
        from PyInstaller.archive.readers import CArchiveReader
        archive = CArchiveReader(os.environ["CHAT_READER_AUDIO_ARCHIVE"])
        embedded = archive.open_embedded_archive("PYZ.pyz")
        for short in ("windows_audio", "app"):
            full = "chat_reader." + short
            code = (embedded.extract(full) if full in embedded.toc
                    else marshal.loads(archive.extract(short)))
            module = types.ModuleType(full)
            module.__spec__ = importlib.util.spec_from_loader(full, loader=None)
            sys.modules[full] = module
            setattr(importlib.import_module("chat_reader"), short, module)
            exec(code, module.__dict__)
    from chat_reader import app
    return app


def native_case(case):
    app = load_runtime()

    result = {"cycles": []}

    def exercise(_desktop, speaker, **_options):
        voice = speaker.engine
        voice.Volume = 0  # This voice only; no system mute or recording.
        output = voice.AudioOutputStream
        text = "一二三四五。这里是暂停和继续测试。 " * 20
        try:
            result["initial_state"] = speaker.toggle_pause()
            speaker.speak(text)
            time.sleep(.05)  # Also pause during the new first-read cue.
            if case in ("cue_stop", "cue_replace"):
                result["cue_pause"] = speaker.toggle_pause()
                start = time.perf_counter()
                if case == "cue_stop":
                    speaker.stop()
                else:
                    speaker.speak("一。Replacement.")
                result["cue_cancel_ms"] = (time.perf_counter() - start) * 1000
                result["cue_cancel_complete"] = bool(voice.WaitUntilDone(5000))
                result["cue_cancel_state"] = speaker.playback_state()
                speaker.speak(text)
                time.sleep(.05)
            for _ in range(2):
                start = time.perf_counter()
                state = speaker.toggle_pause()
                elapsed = (time.perf_counter() - start) * 1000
                time.sleep(.2)  # Allow the provisional 200 ms settling budget.
                position = int(output.Status.CurrentDevicePosition)
                time.sleep(.2)
                after = int(output.Status.CurrentDevicePosition)
                resume = speaker.toggle_pause()
                time.sleep(.3)
                result["cycles"].append({"pause": state, "pause_ms": elapsed,
                    "held": position == after, "resume": resume,
                    "advanced": int(output.Status.CurrentDevicePosition) > after})
            if case == "rate":
                speaker.toggle_pause()
                time.sleep(.2)
                before = int(output.Status.CurrentDevicePosition)
                speaker.set_rate(3)
                time.sleep(.2)
                result["rate"] = int(voice.Rate)
                result["rate_held"] = int(output.Status.CurrentDevicePosition) == before
                speaker.toggle_pause()
                time.sleep(.3)
                result["rate_resumed"] = int(output.Status.CurrentDevicePosition) > before
            elif case == "replace":
                speaker.toggle_pause()
                start = time.perf_counter()
                speaker.speak("一二三四五。Replacement selection.")
                result["replace_ms"] = (time.perf_counter() - start) * 1000
                result["replacement_completed"] = bool(voice.WaitUntilDone(5000))
                result["replacement_text"] = speaker.last_text
                result["replacement_state"] = speaker.playback_state()
            elif case == "stop":
                speaker.toggle_pause()
                start = time.perf_counter()
                speaker.stop()
                result["stop_ms"] = (time.perf_counter() - start) * 1000
                result["stop_completed"] = bool(voice.WaitUntilDone(1000))
                result["stop_state"] = speaker.playback_state()
                result["replay"] = speaker.play_pause()
                time.sleep(.4)
                result["replay_advances"] = int(output.Status.CurrentDevicePosition) > 0
            speaker.stop()
            voice.WaitUntilDone(1000)
            # Exercise pause before the asynchronous device has necessarily opened.
            speaker.speak(text)
            result["early_pause"] = speaker.toggle_pause()
            result["early_resume"] = speaker.toggle_pause()
        finally:
            speaker.stop()  # Same cleanup path used by the real loop on exit.
            result["exit_completed"] = bool(voice.WaitUntilDone(1000))

    with tempfile.TemporaryDirectory(prefix="reader-audio-test-") as folder, \
            patch.object(app, "run_reader_loop", exercise):
        app.run(["--settings-file", str(Path(folder) / "settings.json")])
    print("AUDIO_RESULT=" + json.dumps(result), flush=True)


def startup_case(*, muted=False):
    """Render the real factory's speech to owned files; no device sound/recording."""
    from array import array
    import wave
    app = load_runtime()
    text = '一，二，三。Hello! <silence msec="2000"/> & goodbye.'
    result = {}
    with tempfile.TemporaryDirectory(prefix="reader-startup-test-") as folder:
        speaker = app.create_windows_speaker(rate=-2)
        voice = speaker.engine
        if muted:
            voice.Volume = 0

        def render(name, speak):
            import comtypes.client
            stream = comtypes.client.CreateObject("SAPI.SpFileStream", dynamic=True)
            stream.Format.Type = 22  # Windows SAPI: 22.05 kHz / 16-bit / mono.
            path = Path(folder) / (name + ".wav")
            stream.Open(str(path), 3)
            try:
                voice.AllowAudioOutputFormatChangesOnNextSet = False
                voice.AudioOutputStream = stream
                speak()
                if not voice.WaitUntilDone(15000):
                    raise AssertionError("Synthetic file speech timed out")
            finally:
                stream.Close()
            with wave.open(str(path), "rb") as audio:
                assert (audio.getframerate(), audio.getsampwidth(), audio.getnchannels()) == (22050, 2, 1)
                samples = array("h", audio.readframes(audio.getnframes()))
            return samples

        # Stop/idle controls and changing rate must not consume the first-read cue.
        speaker.stop()
        assert voice.WaitUntilDone(1000), "Idle setup must await asynchronous stop"
        result["idle"] = speaker.toggle_pause()
        speaker.speak("")  # Empty input must not consume startup warming.
        assert voice.WaitUntilDone(1000)
        speaker.set_rate(0)
        speaker.set_rate(-2)
        first = render("first", lambda: speaker.speak(text))
        result["text"] = speaker.last_text
        speaker.stop()
        result["replay"] = None

        def replay():
            result["replay"] = speaker.play_pause()

        repeated = render("replay", replay)
        another = render("another", lambda: speaker.speak(text))
        # Plain-text baseline on this voice, same rate: not the code's cue builder.
        baseline = render("baseline", lambda: voice.Speak(text, 16))
        prefix = first[:8820]  # 400 ms independently derived at 22,050 frames/s.
        # A 660 Hz cue has 264 cycles: count positive zero-crossings, not its source.
        crossings = sum(left <= 0 < right for left, right in zip(prefix, prefix[1:]))
        result.update(first_frames=len(first), repeat_frames=len(repeated),
                      another_frames=len(another), baseline_frames=len(baseline),
                      prefix_peak=max(abs(value) for value in prefix),
                      prefix_crossings=crossings, prefix_edges=[prefix[0], prefix[-1]],
                      speech_peak=max(abs(value) for value in first[8820:]),
                      rate=int(voice.Rate))
        speaker.stop()
    print("STARTUP_RESULT=" + json.dumps(result), flush=True)


def startup_failure_case():
    app = load_runtime()
    speaker = app.create_windows_speaker()
    voice = speaker.engine
    voice.Volume = 0

    class RejectText:
        def __getattr__(self, name):
            return getattr(voice, name)

        def Speak(self, text, flags):
            if text:
                raise RuntimeError("Synthetic text submission failure")
            return voice.Speak(text, flags)

    # Real voice/PCM cue; fail only the following external text-submission boundary.
    speaker.engine = RejectText()
    try:
        try:
            speaker.speak("一，二，三。")
        except RuntimeError as error:
            assert str(error) == "Synthetic text submission failure"
        else:
            raise AssertionError("Expected text boundary failure")
        result = {"cancelled": bool(voice.WaitUntilDone(150)), "last_text": speaker.last_text}
    finally:
        speaker.stop()
        assert voice.WaitUntilDone(1000)
    print("FAILURE_RESULT=" + json.dumps(result), flush=True)


@unittest.skipUnless(os.environ.get("CHAT_READER_WINDOWS_TESTS") == "1",
                     "Opt-in file-only real SAPI startup cue check")
class StartupCueTests(unittest.TestCase):
    def test_muting_only_this_voice_also_mutes_its_startup_cue(self):
        """A PCM cue that ignores the voice's mute would make native tests audible."""
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--startup-muted"],
                             capture_output=True, text=True, encoding="utf-8", timeout=25,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        value = json.loads(next(line.removeprefix("STARTUP_RESULT=")
                                for line in run.stdout.splitlines() if line.startswith("STARTUP_RESULT=")))
        self.assertEqual(0, value["prefix_peak"], "Voice mute must include its cue")
        self.assertEqual(0, value["speech_peak"])

    def test_text_submission_error_cancels_the_already_queued_cue(self):
        """Leaving the cue playing after a reported read failure fails this check."""
        run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--startup-failure"],
                             capture_output=True, text=True, encoding="utf-8", timeout=10,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        value = json.loads(next(line.removeprefix("FAILURE_RESULT=")
                                for line in run.stdout.splitlines() if line.startswith("FAILURE_RESULT=")))
        self.assertTrue(value["cancelled"], "A failed read left its cue playing")
        self.assertEqual("", value["last_text"])

    def test_first_read_has_soft_pcm_primer_without_repeating_it_or_parsing_text_as_xml(self):
        """Missing cue, purging it, repeating it, or dropping plain-text flags fail."""
        try:
            run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--startup-case"],
                                 capture_output=True, text=True, encoding="utf-8", timeout=25,
                                 env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired:
            self.fail("Startup cue or file rendering blocked the real speaker")
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        value = json.loads(next(line.removeprefix("STARTUP_RESULT=")
                                for line in run.stdout.splitlines() if line.startswith("STARTUP_RESULT=")))
        self.assertAlmostEqual(8820, value["first_frames"] - value["baseline_frames"], delta=600,
                               msg="First-read PCM must contain a 400 ms cue before full plain-text speech")
        self.assertAlmostEqual(value["baseline_frames"], value["repeat_frames"], delta=600)
        self.assertAlmostEqual(value["baseline_frames"], value["another_frames"], delta=600)
        self.assertGreater(value["prefix_peak"], 3000, "Silence cannot warm this output path")
        self.assertLessEqual(value["prefix_peak"], 3276, "Cue must remain modest, not full scale")
        self.assertAlmostEqual(264, value["prefix_crossings"], delta=1)
        self.assertEqual([0, 0], value["prefix_edges"], "Fade prevents boundary clicks")
        self.assertEqual('一，二，三。Hello! <silence msec="2000"/> & goodbye.', value["text"])
        self.assertEqual("idle", value["idle"])
        self.assertEqual("replaying", value["replay"])
        self.assertEqual(-2, value["rate"])


@unittest.skipUnless(os.environ.get("CHAT_READER_WINDOWS_TESTS") == "1",
                     "Opt-in muted native audio output checks")
class NativeAudioTests(unittest.TestCase):
    def run_case(self, case):
        try:
            run = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                  "--native-case", case], capture_output=True,
                                 text=True, encoding="utf-8", timeout=20,
                                 env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired:
            self.fail(f"Native {case} hung; pause/cancel must leave controls usable")
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        payload = next(line.removeprefix("AUDIO_RESULT=") for line in run.stdout.splitlines()
                       if line.startswith("AUDIO_RESULT="))
        value = json.loads(payload)
        self.assertEqual("idle", value["initial_state"])
        for cycle in value["cycles"]:
            self.assertEqual("paused", cycle["pause"])
            self.assertLess(cycle["pause_ms"], 200, cycle)
            self.assertTrue(cycle["held"], f"Audio kept advancing after pause: {cycle}")
            self.assertEqual("resumed", cycle["resume"])
            self.assertTrue(cycle["advanced"], "Resume must retain and advance the position")
        self.assertEqual("paused", value["early_pause"])
        self.assertEqual("resumed", value["early_resume"])
        self.assertTrue(value["exit_completed"], "Exit left speech paused or pending")
        return value

    def test_pause_holds_real_output_within_budget_and_resume_keeps_position(self):
        """Using boundary-only SAPI Pause instead of output control fails this test."""
        self.run_case("pause")

    def test_paused_stop_completes_and_replay_is_not_left_paused(self):
        """Purging before releasing a paused device hangs this runtime scenario."""
        value = self.run_case("stop")
        self.assertLess(value["stop_ms"], 200)
        self.assertTrue(value["stop_completed"])
        self.assertEqual("idle", value["stop_state"])
        self.assertEqual("replaying", value["replay"])
        self.assertTrue(value["replay_advances"])

    def test_paused_replacement_finishes_instead_of_blocking_or_replaying_old_text(self):
        value = self.run_case("replace")
        self.assertLess(value["replace_ms"], 200)
        self.assertTrue(value["replacement_completed"])
        self.assertEqual("一二三四五。Replacement selection.", value["replacement_text"])
        self.assertEqual("idle", value["replacement_state"])

    def test_rate_change_while_paused_keeps_position_and_can_resume(self):
        value = self.run_case("rate")
        self.assertEqual(3, value["rate"])
        self.assertTrue(value["rate_held"])
        self.assertTrue(value["rate_resumed"])

    def test_stop_during_paused_first_cue_cancels_cue_and_pending_text(self):
        value = self.run_case("cue_stop")
        self.assertEqual("paused", value["cue_pause"])
        self.assertLess(value["cue_cancel_ms"], 200)
        self.assertTrue(value["cue_cancel_complete"])
        self.assertEqual("idle", value["cue_cancel_state"])

    def test_replacement_during_paused_first_cue_does_not_wedge_the_stream_writer(self):
        value = self.run_case("cue_replace")
        self.assertEqual("paused", value["cue_pause"])
        self.assertLess(value["cue_cancel_ms"], 200)
        self.assertTrue(value["cue_cancel_complete"])
        self.assertEqual("idle", value["cue_cancel_state"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--native-case":
        native_case(sys.argv[2])
    elif sys.argv[1:] == ["--startup-case"]:
        startup_case()
    elif sys.argv[1:] == ["--startup-failure"]:
        startup_failure_case()
    elif sys.argv[1:] == ["--startup-muted"]:
        startup_case(muted=True)
    else:
        unittest.main()
