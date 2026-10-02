"""Isolated accessibility capture and verified reply extraction."""

import argparse
import json
from pathlib import PureWindowsPath
import sys

from chat_reader.codex_adapter import plan_at_point
from chat_reader.paragraphs import ParagraphUnavailable
from chat_reader.uia_probe import ProbeUnavailable
from chat_reader.windows_context import process_identity


CODEX_PACKAGE_FAMILY = "OpenAI.Codex_2p2nqsd0c76g0"


def read_paragraph(point, *, capture=None, lookup_identity=process_identity, with_plan=False):
    if capture is None:
        from chat_reader.uia_probe import WindowsUIA, capture_probe
        capture = lambda position: capture_probe(WindowsUIA(), position)
    snapshot = capture(point)
    if snapshot.get("point") != list(point):
        raise ParagraphUnavailable("The mouse position changed during capture. Try again.")
    pid = snapshot.get("tree", {}).get("process_id")
    if not isinstance(pid, int) or pid <= 0:
        raise ParagraphUnavailable("The pointed application's identity is unavailable.")
    identity = lookup_identity(pid)
    fields = (identity.image_path, identity.package_family, identity.package_full_name, identity.package_path)
    if not all(isinstance(value, str) and value.strip() for value in fields):
        raise ParagraphUnavailable("This app is not a verified Codex package. Use Alt + S.")
    path, package_path = PureWindowsPath(identity.image_path), PureWindowsPath(identity.package_path)
    if (identity.package_family.casefold() != CODEX_PACKAGE_FAMILY.casefold()
            or not path.is_absolute() or not package_path.is_absolute()
            or path != package_path / "app" / "ChatGPT.exe"):
        raise ParagraphUnavailable("This app is not a verified Codex package. Use Alt + S.")
    # Numeric version is diagnostic metadata, never permission to bypass the
    # inspected adapter's ownership, completion and protected-text checks.
    plan = plan_at_point(snapshot)
    return plan if with_plan else plan.text


def main(argv=None):
    parser = argparse.ArgumentParser(description="Isolated paragraph capture worker.")
    parser.add_argument("x", type=int)
    parser.add_argument("y", type=int)
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        point = (args.x, args.y)
        plan = read_paragraph(point, with_plan=True)
        print(json.dumps({"point": list(point), **plan.to_payload()}, ensure_ascii=False))
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
