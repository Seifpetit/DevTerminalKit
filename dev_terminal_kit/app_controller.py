from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from . import app_config as config
from .actions import (
    Action,
    LaunchSelectedAgent,
    SaveCurrentPaths,
    SelectAccentColor,
    SetColorMode,
    ToggleColorMode,
    ToggleTerminals,
)
from .app_settings import save_agent_project_root, save_color_mode, save_paths
from .app_state import AppState, load_initial_state
from .terminal_commands import (
    TerminalUserError,
    clear_pid_file,
    open_agent_terminal,
    open_windows_terminal_tabs,
    terminate_recorded_processes,
    validate_command_text,
    validate_project_path,
)


@dataclass(frozen=True)
class UserDialog:
    title: str
    message: str


@dataclass(frozen=True)
class ControllerResult:
    state: AppState
    dialog: UserDialog | None = None
    rebuild_ui: bool = False
    close_palette: bool = False


class AppController:
    def __init__(self, state: AppState) -> None:
        self.state = state
        config.apply_color_mode_tokens(state.color_mode)

    @classmethod
    def load(cls) -> "AppController":
        return cls(load_initial_state())

    def dispatch(self, action: Action) -> ControllerResult:
        if isinstance(action, ToggleColorMode):
            return self._toggle_color_mode()
        if isinstance(action, SetColorMode):
            return self._set_color_mode(action.mode)
        if isinstance(action, SelectAccentColor):
            return self._select_accent_color(action)
        if isinstance(action, SaveCurrentPaths):
            return self._save_current_paths(action)
        if isinstance(action, LaunchSelectedAgent):
            return self._launch_selected_agent(action)
        if isinstance(action, ToggleTerminals):
            return self._toggle_terminals(action)
        raise ValueError(f"Unsupported action: {action!r}")

    def _set_state(self, state: AppState) -> AppState:
        self.state = state
        return state

    def _toggle_color_mode(self) -> ControllerResult:
        next_mode = (
            config.COLOR_MODE_DAY
            if self.state.color_mode == config.COLOR_MODE_NIGHT
            else config.COLOR_MODE_NIGHT
        )
        return self._set_color_mode(next_mode)

    def _set_color_mode(self, mode: str) -> ControllerResult:
        next_mode = config.normalize_color_mode(mode)
        config.apply_color_mode_tokens(next_mode)
        save_color_mode(self.state.settings_file, next_mode)
        state = self._set_state(replace(self.state, color_mode=next_mode))
        return ControllerResult(state=state, close_palette=True)

    def _select_accent_color(self, action: SelectAccentColor) -> ControllerResult:
        state = self._set_state(replace(self.state, accent_color=action.color))
        return ControllerResult(state=state, close_palette=True)

    def _save_current_paths(self, action: SaveCurrentPaths) -> ControllerResult:
        state = self._set_state(
            replace(
                self.state,
                backend_path=action.backend_path,
                frontend_path=action.frontend_path,
                agent_project_root=action.agent_project_root,
            )
        )
        save_paths(
            state.settings_file,
            Path(action.backend_path).expanduser(),
            Path(action.frontend_path).expanduser(),
        )
        save_agent_project_root(
            state.settings_file,
            Path(action.agent_project_root).expanduser(),
        )
        return ControllerResult(state=state)

    def _launch_selected_agent(self, action: LaunchSelectedAgent) -> ControllerResult:
        if action.agent_name is None:
            return self._error("Missing agent", "Please choose an agent.")

        if action.agent_name not in config.AGENT_COMMANDS:
            return self._error("Invalid agent", f"Unknown agent: {action.agent_name}")

        state = self._set_state(replace(self.state, agent_project_root=action.project_root))

        try:
            project_root = validate_project_path(action.project_root, "agent project root")
            open_agent_terminal(
                action.agent_name,
                project_root,
                config.AGENT_COMMANDS[action.agent_name],
            )
        except TerminalUserError as error:
            return self._error(error.title, error.message)
        except OSError as error:
            return self._error("Agent launch failed", str(error))

        save_agent_project_root(state.settings_file, project_root)
        state = self._set_state(
            replace(
                state,
                agent_project_root=str(project_root),
                status_text=f"{action.agent_name} opened in {project_root}.",
            )
        )
        return ControllerResult(state=state)

    def _toggle_terminals(self, action: ToggleTerminals) -> ControllerResult:
        state = self._set_state(
            replace(
                self.state,
                backend_path=action.backend_path,
                frontend_path=action.frontend_path,
                backend_command=action.backend_command,
                frontend_command=action.frontend_command,
            )
        )

        if state.terminals_running:
            return self._end_terminals()
        return self._launch_workspace()

    def _end_terminals(self) -> ControllerResult:
        terminated = terminate_recorded_processes(self.state.pid_file)
        status_text = (
            "Terminal tasks ended."
            if terminated
            else "No recorded terminal tasks were running."
        )
        state = self._set_state(
            replace(
                self.state,
                terminals_running=False,
                status_text=status_text,
            )
        )
        return ControllerResult(state=state)

    def _launch_workspace(self) -> ControllerResult:
        try:
            backend = validate_project_path(self.state.backend_path, "backend")
            frontend = validate_project_path(self.state.frontend_path, "frontend")
            backend_command = validate_command_text(self.state.backend_command, "backend")
            frontend_command = validate_command_text(self.state.frontend_command, "frontend")
            clear_pid_file(self.state.pid_file)
            open_windows_terminal_tabs(
                backend,
                backend_command,
                frontend,
                frontend_command,
                self.state.pid_file,
            )
        except TerminalUserError as error:
            return self._error(error.title, error.message)
        except OSError as error:
            return self._error("Launch failed", str(error))

        save_paths(self.state.settings_file, backend, frontend)
        state = self._set_state(
            replace(
                self.state,
                backend_path=str(backend),
                frontend_path=str(frontend),
                terminals_running=True,
                status_text="Windows Terminal opened with backend and frontend tabs.",
            )
        )
        return ControllerResult(state=state)

    def _error(self, title: str, message: str) -> ControllerResult:
        return ControllerResult(
            state=self.state,
            dialog=UserDialog(title=title, message=message),
        )
