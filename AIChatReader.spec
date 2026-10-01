# A single-file Windows console application, with Python and dependencies included.
from pathlib import Path
import comtypes.client

project_root = Path(SPECPATH)
# Generate native COM bindings during the build and bundle them explicitly;
# the user's machine does not need a writable comtypes source installation.
uia_types = comtypes.client.GetModule("UIAutomationCore.dll")

analysis = Analysis(
    [str(project_root / "src" / "chat_reader" / "app.py")],
    pathex=[str(project_root / "src")],
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32", "win32timezone",
                   uia_types.__name__, uia_types.__wrapper_module__.__name__],
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
