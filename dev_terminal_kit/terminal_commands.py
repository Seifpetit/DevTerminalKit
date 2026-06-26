from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from pathlib import Path
from tkinter import messagebox

from . import app_config as config


# =============================================================================
# Terminal And Process Helpers
# =============================================================================

def get_pid_file_path() -> Path:
    return Path(tempfile.gettempdir()) / "dev_terminal_launcher_pids.txt"


# Windows Terminal is the host app that creates the two visible tabs.
def is_windows_terminal_available() -> bool:
    return shutil.which("wt.exe") is not None


# Prefer PowerShell 7 when available, then fall back to Windows PowerShell.
def get_powershell_executable() -> str | None:
    for candidate in ("pwsh.exe", "powershell.exe"):
        if shutil.which(candidate) is not None:
            return candidate
    return None


# Quote values for generated PowerShell scripts without breaking paths containing quotes.
def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


# Windows PowerShell expects UTF-16LE for -EncodedCommand.
def encode_powershell_command(script: str) -> str:
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


# Missing PID files are normal when no terminal session is active.
def clear_pid_file(pid_file: Path) -> None:
    try:
        pid_file.unlink()
    except FileNotFoundError:
        return


# =============================================================================
# Input Validation
# =============================================================================

# Convert a path field into a real folder path before launching commands.
def validate_project_path(path_text: str, label: str) -> Path | None:
    path = Path(path_text).expanduser()

    if not path_text.strip():
        messagebox.showerror("Missing path", f"Please choose a {label} path.")
        return None

    if not path.exists() or not path.is_dir():
        messagebox.showerror("Invalid path", f"The {label} path is not a folder:\n{path}")
        return None

    return path.resolve()


# Prevent empty commands from opening tabs that immediately do nothing.
def validate_command_text(command_text: str, label: str) -> str | None:
    command = command_text.strip()

    if not command:
        messagebox.showerror("Missing command", f"Please enter a command for {label}.")
        return None

    return command


# =============================================================================
# Windows Terminal Command Construction
# =============================================================================

# Build one Windows Terminal tab definition. The command itself runs in PowerShell.
def build_tab_command(
    title: str,
    path: Path,
    command_text: str,
    pid_file: Path | None = None,
) -> list[str]:
    powershell = get_powershell_executable()
    if powershell is None:
        raise FileNotFoundError("PowerShell was not found on this machine.")

    script = build_powershell_script(title, path, command_text, pid_file)

    return [
        "new-tab",
        "--title",
        title,
        powershell,
        "-NoExit",
        "-EncodedCommand",
        encode_powershell_command(script),
    ]


# Each tab runs the same sequence: title, optional PID record, cd, user command.
def build_powershell_script(
    title: str,
    path: Path,
    command_text: str,
    pid_file: Path | None,
) -> str:
    lines = [
        f"$Host.UI.RawUI.WindowTitle = {powershell_quote(title)}",
        *build_pid_recording_lines(pid_file),
        f"Set-Location -LiteralPath {powershell_quote(str(path))}",
        command_text,
    ]
    return "\n".join(lines)


# The PID line is injected only for app-launched tabs that can later be closed.
def build_pid_recording_lines(pid_file: Path | None) -> list[str]:
    if pid_file is None:
        return []
    quoted_path = powershell_quote(str(pid_file))
    return [f"Add-Content -LiteralPath {quoted_path} -Value $PID"]


# Launch exactly two tabs in a fresh Windows Terminal window.
def open_windows_terminal_tabs(
    backend_path: Path,
    backend_command: str,
    frontend_path: Path,
    frontend_command: str,
    pid_file: Path | None = None,
) -> None:
    if not is_windows_terminal_available():
        messagebox.showerror(
            "Windows Terminal not found",
            "This launcher needs Windows Terminal installed so it can use wt.exe.",
        )
        return

    command = [
        "wt.exe",
        # A named fresh window keeps this session separate from the user's other terminals.
        "-w",
        "new",
        *build_tab_command(config.BACKEND_TAB_TITLE, backend_path, backend_command, pid_file),
        ";",
        *build_tab_command(config.FRONTEND_TAB_TITLE, frontend_path, frontend_command, pid_file),
    ]

    subprocess.Popen(command)


# Open one interactive agent session in a fresh Windows Terminal window.
def open_agent_terminal(agent_name: str, project_root: Path, command_text: str) -> bool:
    if not is_windows_terminal_available():
        messagebox.showerror(
            "Windows Terminal not found",
            "This launcher needs Windows Terminal installed so it can use wt.exe.",
        )
        return False

    command = [
        "wt.exe",
        "-w",
        "new",
        *build_tab_command(f"{agent_name} Agent", project_root, command_text),
    ]
    subprocess.Popen(command)
    return True


# Parse the PID file defensively; ignore any non-numeric lines.
def read_recorded_pids(pid_file: Path) -> list[int]:
    try:
        lines = pid_file.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []

    pids: list[int] = []
    for line in lines:
        if line.strip().isdigit():
            pids.append(int(line.strip()))
    return pids


# Kill the shell and any child process such as npm/node that it launched.
def terminate_process_tree(pid: int) -> bool:
    result = subprocess.run(
        ["taskkill", "/PID", str(pid), "/T", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


# End every recorded process tree and then reset the PID file.
def terminate_recorded_processes(pid_file: Path) -> int:
    terminated = 0
    for pid in read_recorded_pids(pid_file):
        if terminate_process_tree(pid):
            terminated += 1
    clear_pid_file(pid_file)
    return terminated
