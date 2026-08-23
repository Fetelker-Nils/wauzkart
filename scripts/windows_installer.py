import os
import argparse
import ctypes
import shutil
import subprocess
import sys
import time
from pathlib import Path
from tkinter import Tk, messagebox, ttk, StringVar


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


def wait_for_pid(pid):
    if not pid:
        return
    try:
        pid = int(pid)
    except Exception:
        return
    try:
        synchronize = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
        if handle:
            ctypes.windll.kernel32.WaitForSingleObject(handle, 30000)
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        time.sleep(1.0)


class InstallerWindow:
    def __init__(self, root):
        self.root = root
        self.status = StringVar(value="Bereite Installation vor...")
        self.percent = StringVar(value="0%")
        root.title(APP_NAME)
        root.geometry("460x190")
        root.resizable(False, False)
        root.configure(bg="#070b13")

        title = ttk.Label(root, text="Wauz Kart Installation", font=("Arial", 17, "bold"))
        title.pack(pady=(20, 8))

        status = ttk.Label(root, textvariable=self.status, wraplength=400, anchor="center", justify="center")
        status.pack(pady=(0, 12))

        self.progress = ttk.Progressbar(root, orient="horizontal", length=380, mode="determinate", maximum=100)
        self.progress.pack(pady=(0, 6))

        percent = ttk.Label(root, textvariable=self.percent, font=("Arial", 11, "bold"))
        percent.pack()

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background="#070b13", foreground="#ffffff")
        style.configure("TProgressbar", troughcolor="#101927", background="#f4c945", bordercolor="#f4c945", lightcolor="#f4c945", darkcolor="#f4c945")

    def step(self, value, text):
        self.progress["value"] = int(value)
        self.percent.set(f"{int(value)}%")
        self.status.set(text)
        self.root.update_idletasks()
        self.root.update()


def install(progress=None, wait_pid_value=None):
    if progress:
        progress.step(5, "Suche eingebettete Spiel-Datei...")
    src = payload_path()
    if not src.exists():
        raise RuntimeError("Die eingebettete Wauz-Kart-Datei wurde nicht gefunden.")

    if wait_pid_value:
        if progress:
            progress.step(15, "Warte, bis die alte Version geschlossen ist...")
        wait_for_pid(wait_pid_value)

    if progress:
        progress.step(35, "Erstelle Installationsordner...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    if progress:
        progress.step(60, "Installiere neue Wauz-Kart-Dateien...")
    shutil.copy2(src, INSTALL_EXE)

    if progress:
        progress.step(82, "Aktualisiere Desktop- und Startmenue-Verknuepfungen...")
    create_shortcuts()

    if progress:
        progress.step(100, "Installation fertig.")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--auto-update", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--wait-pid", default="")
    args, _unknown = parser.parse_known_args()

    root = Tk()
    window = InstallerWindow(root)
    try:
        install(window, args.wait_pid)
    except PermissionError:
        root.withdraw()
        messagebox.showerror(
            APP_NAME,
            "Wauz Kart laeuft vermutlich noch. Bitte schliesse das Spiel und starte den Installer erneut.",
        )
        return 1
    except Exception as exc:
        root.withdraw()
        messagebox.showerror(APP_NAME, f"Installation fehlgeschlagen:\n{exc}")
        return 1

    if args.restart or args.auto_update:
        subprocess.Popen([str(INSTALL_EXE)], cwd=str(INSTALL_DIR))
        return 0

    if messagebox.askyesno(APP_NAME, "Wauz Kart wurde installiert oder aktualisiert.\nJetzt starten?"):
        subprocess.Popen([str(INSTALL_EXE)], cwd=str(INSTALL_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
