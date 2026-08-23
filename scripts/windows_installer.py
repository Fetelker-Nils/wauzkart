import os
import shutil
import subprocess
import sys
from pathlib import Path
from tkinter import Tk, messagebox


APP_NAME = "Wauz Kart"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WauzKart"
INSTALL_EXE = INSTALL_DIR / "wauzkart.exe"


def payload_path():
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / "wauzkart.exe"


def run_powershell(script):
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def create_shortcuts():
    install_path = str(INSTALL_EXE)
    install_dir = str(INSTALL_DIR)
    ps = rf'''
$desktop = [Environment]::GetFolderPath("Desktop")
$programs = [Environment]::GetFolderPath("Programs")
$startDir = Join-Path $programs "Wauz Kart"
New-Item -ItemType Directory -Force -Path $startDir | Out-Null
$shell = New-Object -ComObject WScript.Shell
foreach ($path in @((Join-Path $desktop "Wauz Kart.lnk"), (Join-Path $startDir "Wauz Kart.lnk"))) {{
  $shortcut = $shell.CreateShortcut($path)
  $shortcut.TargetPath = "{install_path}"
  $shortcut.WorkingDirectory = "{install_dir}"
  $shortcut.IconLocation = "{install_path},0"
  $shortcut.Save()
}}
'''
    run_powershell(ps)


def install():
    src = payload_path()
    if not src.exists():
        raise RuntimeError("Die eingebettete Wauz-Kart-Datei wurde nicht gefunden.")

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, INSTALL_EXE)
    create_shortcuts()


def main():
    root = Tk()
    root.withdraw()
    try:
        install()
    except PermissionError:
        messagebox.showerror(
            APP_NAME,
            "Wauz Kart laeuft vermutlich noch. Bitte schliesse das Spiel und starte den Installer erneut.",
        )
        return 1
    except Exception as exc:
        messagebox.showerror(APP_NAME, f"Installation fehlgeschlagen:\n{exc}")
        return 1

    if messagebox.askyesno(APP_NAME, "Wauz Kart wurde installiert oder aktualisiert.\nJetzt starten?"):
        subprocess.Popen([str(INSTALL_EXE)], cwd=str(INSTALL_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
