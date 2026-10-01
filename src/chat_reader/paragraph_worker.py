"""Isolated accessibility capture and verified reply extraction."""

import argparse
import json
from pathlib import PureWindowsPath
import sys

from chat_reader.codex_adapter import text_at_point
from chat_reader.paragraphs import ParagraphUnavailable
from chat_reader.uia_probe import ProbeUnavailable
from chat_reader.windows_context import process_image_path


INSPECTED_PACKAGE = "OpenAI.Codex_26.928.3736.0_x64__2p2nqsd0c76g0"


def read_paragraph(point, *, capture=None, lookup_process=process_image_path):
    if capture is None:
        from chat_reader.uia_probe import WindowsUIA, capture_probe
        capture = lambda position: capture_probe(WindowsUIA(), position)
    snapshot = capture(point)
    if snapshot.get("point") != list(point):
        raise ParagraphUnavailable("The mouse position changed during capture. Try again.")
    pid = snapshot.get("tree", {}).get("process_id")
    if not isinstance(pid, int) or pid <= 0:
        raise ParagraphUnavailable("The pointed application's identity is unavailable.")
    path = PureWindowsPath(lookup_process(pid))
    if (path.name.casefold() != "chatgpt.exe" or path.parent.name.casefold() != "app"
            or path.parent.parent.name.casefold() != INSPECTED_PACKAGE.casefold()):
        raise ParagraphUnavailable("This app/build has not been inspected for paragraph reading. Use Alt + S.")
    return text_at_point(snapshot)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Isolated paragraph capture worker.")
    parser.add_argument("x", type=int)
    parser.add_argument("y", type=int)
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        point = (args.x, args.y)
        text = read_paragraph(point)
        print(json.dumps({"point": list(point), "text": text}, ensure_ascii=False))
        return 0
    except Exception as error:
        message = ("Install the paragraph dependency: python -m pip install -e \".[paragraph]\""
                   if isinstance(error, ModuleNotFoundError)
                   else str(error) if isinstance(error, (ParagraphUnavailable, ProbeUnavailable, OSError))
                   else "The Windows accessibility provider could not read this reply. Use Alt + S.")
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
