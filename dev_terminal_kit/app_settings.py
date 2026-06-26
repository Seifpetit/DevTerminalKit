from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from pathlib import Path

from . import app_config as config


# =============================================================================
# Settings And Resources
# =============================================================================

def get_settings_file_path() -> Path:
    app_data = os.environ.get("APPDATA")
    settings_root = Path(app_data) if app_data else Path.home()
    return settings_root / config.SETTINGS_DIR_NAME / config.SETTINGS_FILE_NAME


# Resolve bundled files both from source and from the PyInstaller temp folder.
def get_resource_path(file_name: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", config.ROOT_DIR))
    return base_path / file_name


# Apply the packaged icon when Tk can read the ICO file.
def set_window_icon(window: tk.Tk | tk.Toplevel) -> None:
    icon_path = get_resource_path(config.APP_ICON_FILE_NAME)
    if not icon_path.is_file():
        return

    try:
        window.iconbitmap(default=str(icon_path))
    except tk.TclError:
        return


# Read the settings JSON defensively so corrupt files do not block startup.
def load_saved_settings(settings_file: Path) -> dict[str, object]:
    try:
        data = json.loads(settings_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


# Load backend and frontend paths, falling back to repo-adjacent defaults.
def load_saved_paths(settings_file: Path) -> tuple[Path, Path]:
    data = load_saved_settings(settings_file)
    backend_path = data.get("backend_path")
    frontend_path = data.get("frontend_path")
    backend = Path(backend_path) if isinstance(backend_path, str) and backend_path else config.DEFAULT_BACKEND_PATH
    frontend = Path(frontend_path) if isinstance(frontend_path, str) and frontend_path else config.DEFAULT_FRONTEND_PATH
    return backend, frontend


# Use the shared parent when backend and frontend look like sibling folders.
def infer_agent_project_root(backend_path: Path, frontend_path: Path) -> Path:
    if backend_path.parent == frontend_path.parent:
        return backend_path.parent
    return config.ROOT_DIR


# Load the Codex project root or infer it from the saved workspace paths.
def load_saved_agent_project_root(
    settings_file: Path,
    backend_path: Path,
    frontend_path: Path,
) -> Path:
    data = load_saved_settings(settings_file)
    agent_project_root = data.get("agent_project_root")
    if isinstance(agent_project_root, str) and agent_project_root:
        return Path(agent_project_root)
    return infer_agent_project_root(backend_path, frontend_path)


# Load the saved day/night mode.
def load_saved_color_mode(settings_file: Path) -> str:
    return config.normalize_color_mode(load_saved_settings(settings_file).get("color_mode"))


# Persist workspace paths without overwriting other settings keys.
def save_paths(settings_file: Path, backend_path: Path, frontend_path: Path) -> None:
    settings = load_saved_settings(settings_file)
    settings["backend_path"] = str(backend_path)
    settings["frontend_path"] = str(frontend_path)
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        return


# Persist the selected day/night mode without overwriting other settings keys.
def save_color_mode(settings_file: Path, color_mode: str) -> None:
    settings = load_saved_settings(settings_file)
    settings["color_mode"] = config.normalize_color_mode(color_mode)
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        return


# Persist the project root used by interactive agents.
def save_agent_project_root(settings_file: Path, project_root: Path) -> None:
    settings = load_saved_settings(settings_file)
    settings["agent_project_root"] = str(project_root)
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError:
        return
