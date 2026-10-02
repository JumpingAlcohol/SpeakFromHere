# Two standalone entries: a windowed player and an advanced console reader.
from pathlib import Path
import comtypes.client
from PyInstaller.utils.hooks.tcl_tk import tcltk_info

project_root = Path(SPECPATH)
if not tcltk_info.available:
    raise SystemExit("Tk cannot be inspected here. Install Python's Tcl/Tk component and build in a normal Windows desktop environment; do not ship a GUI-less bundle.")
# Generate native COM bindings during the build and bundle them explicitly;
# the user's machine does not need a writable comtypes source installation.
uia_types = comtypes.client.GetModule("UIAutomationCore.dll")

analysis = Analysis(
    [str(project_root / "src" / "chat_reader" / "gui_entry.py")],
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
    name="SpeakFromHere",
    console=False,
    debug=False,
    strip=False,
    upx=False,
)
console_analysis = Analysis(
    [str(project_root / "src" / "chat_reader" / "app.py")],
    pathex=[str(project_root / "src")],
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32", "win32timezone",
                   uia_types.__name__, uia_types.__wrapper_module__.__name__],
)
console_archive = PYZ(console_analysis.pure)
console_application = EXE(
    console_archive, console_analysis.scripts, console_analysis.binaries, console_analysis.datas, [],
    name="SpeakFromHereConsole", console=True, debug=False, strip=False, upx=False,
)

# Capture-only one-directory helper: avoids unpacking the GUI/voice runtime on
# every Alt+E request. Both entries use this same executable and adapter.
worker_analysis = Analysis(
    [str(project_root / "src" / "chat_reader" / "paragraph_worker.py")],
    pathex=[str(project_root / "src")],
    hiddenimports=[uia_types.__name__, uia_types.__wrapper_module__.__name__],
)
worker_archive = PYZ(worker_analysis.pure)
worker_application = EXE(
    worker_archive, worker_analysis.scripts, [], exclude_binaries=True,
    name="SpeakFromHereWorker", console=True, debug=False, strip=False, upx=False,
)
worker_folder = COLLECT(
    worker_application, worker_analysis.binaries, worker_analysis.datas,
    name="reader-worker", strip=False, upx=False,
)
