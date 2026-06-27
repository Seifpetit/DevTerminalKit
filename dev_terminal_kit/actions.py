from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class ToggleColorMode:
    pass


@dataclass(frozen=True)
class SetColorMode:
    mode: str


@dataclass(frozen=True)
class SelectAccentColor:
    color: str


@dataclass(frozen=True)
class SaveCurrentPaths:
    backend_path: str
    frontend_path: str
    agent_project_root: str


@dataclass(frozen=True)
class LaunchSelectedAgent:
    agent_name: str | None
    project_root: str


@dataclass(frozen=True)
class ToggleTerminals:
    backend_path: str
    frontend_path: str
    backend_command: str
    frontend_command: str


Action = Union[
    ToggleColorMode,
    SetColorMode,
    SelectAccentColor,
    SaveCurrentPaths,
    LaunchSelectedAgent,
    ToggleTerminals,
]
