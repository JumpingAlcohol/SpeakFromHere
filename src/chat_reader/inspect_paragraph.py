"""Source-only mouse-point probe. It does not read aloud or register hotkeys."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from chat_reader.uia_probe import ProbeUnavailable


def inspect_and_save(point, output, *, runner=subprocess.run):
    """Isolate native provider calls so a hung app cannot hang the probe forever."""
    try:
        result = runner(
            [sys.executable, "-m", "chat_reader.inspect_paragraph", "--worker",
             str(point[0]), str(point[1])],
            capture_output=True, encoding="utf-8", timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as error:
        raise ProbeUnavailable("The app did not respond within 20 seconds. No new capture was saved.") from error
    if result.returncode:
        raise ProbeUnavailable(result.stderr.strip() or "The inspection worker failed.")
    try:
        capture = json.loads(result.stdout)
        if (capture.get("schema_version") != 1 or capture.get("point") != list(point)
                or capture.get("verified_reply") is not False or "tree" not in capture):
            raise ValueError("Invalid inspection result")
    except (ValueError, TypeError, AttributeError) as error:
        raise ProbeUnavailable("The worker did not return a valid inspection snapshot.") from error
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(capture, ensure_ascii=False, indent=2), encoding="utf-8")
    return capture


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only paragraph inspection; no speech or clipboard changes.")
    parser.add_argument("--delay", type=int, default=5, help="Seconds to position the mouse (0-30; default 5)")
    parser.add_argument("--output", type=Path, default=Path("work/paragraph-probe.json"), help="Local snapshot path; contains app text")
    parser.add_argument("--worker", nargs=2, type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("This probe requires Windows.")
    if not 0 <= args.delay <= 30:
        parser.error("--delay must be between 0 and 30 seconds.")
    if args.worker is not None:
        # Structured output only; ensure Unicode does not depend on the console code page.
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
        try:
            from chat_reader.uia_probe import WindowsUIA, capture_probe
            capture = capture_probe(WindowsUIA(), tuple(args.worker))
            print(json.dumps(capture, ensure_ascii=False))
            return 0
        except Exception as error:
            message = ("Install the paragraph dependency: python -m pip install -e \".[paragraph]\""
                       if isinstance(error, ModuleNotFoundError)
                       else str(error) if isinstance(error, ProbeUnavailable)
                       else "The Windows accessibility provider could not be initialized.")
            print(message, file=sys.stderr)
            return 1
    print("Read-only probe / 只读检查：不点击、不复制、不朗读、不上传。", flush=True)
    print("The local snapshot contains app text. Keep it private; do not commit or upload it.", flush=True)
    print(f"Move the mouse onto an ordinary AI reply paragraph within {args.delay} seconds.", flush=True)
    print(f"请在 {args.delay} 秒内把鼠标移到 AI 回复的一段普通正文上，无需点击或选中。", flush=True)
    try:
        time.sleep(args.delay)
        from chat_reader.windows_context import physical_cursor_position
        capture = inspect_and_save(physical_cursor_position(), args.output)
    except KeyboardInterrupt:
        print("Inspection cancelled / 已取消检查。")
        return 130
    except (ProbeUnavailable, OSError) as error:
        print(f"Inspection failed / 检查未完成：{error}", file=sys.stderr)
        return 1
    print(f"Saved local snapshot / 已保存本地检查结果：{args.output.resolve()}")
    print(f"Nodes: {capture['node_count']}; truncated: {capture['truncated']}; verified reply: False")
    print("This is diagnostic data, not confirmed paragraph-reading support. This probe does not enable Alt + E.")
    print("Experimental playback is separate: python -m chat_reader.app --paragraphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
