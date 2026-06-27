from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


# =============================================================================
# Entry Point
# =============================================================================


def _first_existing_file(candidates: tuple[Path, ...], file_name: str) -> Path | None:
    for candidate in candidates:
        if (candidate / file_name).is_file():
            return candidate
    return None


def _relax_exact_version_check(file_path: Path, exact: str, relaxed: str) -> None:
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError:
        return

    patched = text.replace(exact, relaxed)
    if patched != text:
        file_path.write_text(patched, encoding="utf-8")


def configure_tk_runtime() -> None:
    """Point Tk at a usable Tcl/Tk runtime before creating the root window."""

    base_path = Path(getattr(sys, "_MEIPASS", sys.base_prefix))
    source_tcl = _first_existing_file(
        (
            base_path / "tcl",
            base_path / "tcl" / "tcl8.6",
        ),
        "init.tcl",
    )
    source_tk = _first_existing_file(
        (
            base_path / "tk",
            base_path / "tcl" / "tk8.6",
        ),
        "tk.tcl",
    )

    if source_tcl is None or source_tk is None:
        return

    runtime_root = Path(__file__).resolve().parent / ".tk-runtime"
    patched_tcl = runtime_root / "tcl"
    patched_tk = runtime_root / "tk"

    shutil.copytree(source_tcl, patched_tcl, dirs_exist_ok=True)
    shutil.copytree(source_tk, patched_tk, dirs_exist_ok=True)

    tcl8_source = source_tcl.parent / "tcl8"
    if tcl8_source.is_dir():
        shutil.copytree(tcl8_source, runtime_root / "tcl8", dirs_exist_ok=True)

    _relax_exact_version_check(
        patched_tcl / "init.tcl",
        "package require -exact Tcl 8.6.9",
        "package require Tcl 8.6",
    )
    _relax_exact_version_check(
        patched_tk / "tk.tcl",
        "package require -exact Tk  8.6.9",
        "package require Tk 8.6",
    )

    os.environ["TCL_LIBRARY"] = str(patched_tcl)
    os.environ["TK_LIBRARY"] = str(patched_tk)


# Keep creation behind main() so packaging tools can import this module safely.
def main() -> None:
    configure_tk_runtime()
    from dev_terminal_kit.launcher_app import DevTerminalLauncher

    app = DevTerminalLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
