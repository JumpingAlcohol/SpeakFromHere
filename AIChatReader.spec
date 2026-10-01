# A single-file Windows console application, with Python and dependencies included.
from pathlib import Path

project_root = Path(SPECPATH)

analysis = Analysis(
    [str(project_root / "src" / "chat_reader" / "app.py")],
    pathex=[str(project_root / "src")],
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32", "win32timezone"],
)
archive = PYZ(analysis.pure)
application = EXE(
    archive,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="AIChatReader",
    console=True,
    debug=False,
    strip=False,
    upx=False,
)
