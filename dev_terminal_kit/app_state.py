from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import app_config as config
from .app_settings import (
    get_settings_file_path,
    load_saved_agent_project_root,
    load_saved_color_mode,
    load_saved_paths,
)
from .terminal_commands import get_pid_file_path


READY_STATUS = "Ready to launch backend and frontend"


@dataclass(frozen=True)
class AppState:
    settings_file: Path
    pid_file: Path
    backend_path: str
    frontend_path: str
    agent_project_root: str
    backend_command: str
    frontend_command: str
    color_mode: str
    accent_color: str = config.DEFAULT_ACCENT
    terminals_running: bool = False
    status_text: str = READY_STATUS


def load_initial_state() -> AppState:
    settings_file = get_settings_file_path()
    saved_backend_path, saved_frontend_path = load_saved_paths(settings_file)
    saved_agent_project_root = load_saved_agent_project_root(
        settings_file,
        saved_backend_path,
        saved_frontend_path,
    )
    return AppState(
        settings_file=settings_file,
        pid_file=get_pid_file_path(),
        backend_path=str(saved_backend_path),
        frontend_path=str(saved_frontend_path),
        agent_project_root=str(saved_agent_project_root),
        backend_command=config.DEFAULT_COMMAND,
        frontend_command=config.DEFAULT_COMMAND,
        color_mode=load_saved_color_mode(settings_file),
    )
