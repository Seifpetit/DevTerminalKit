from __future__ import annotations

from dev_terminal_kit.launcher_app import DevTerminalLauncher


# =============================================================================
# Entry Point
# =============================================================================

# Keep creation behind main() so packaging tools can import this module safely.
def main() -> None:
    app = DevTerminalLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
