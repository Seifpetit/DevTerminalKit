from __future__ import annotations

from pathlib import Path


# =============================================================================
# App Configuration
# =============================================================================

UI_SCALE = 0.6


# Scale pixel dimensions from the design baseline.
def scaled_px(value: int) -> int:
    return max(1, round(value * UI_SCALE))


# Scale type while keeping small labels readable.
def scaled_font(value: int) -> int:
    return max(8, round(value * UI_SCALE))


# Convert an unscaled design size into a Tk geometry string.
def scaled_geometry(width: int, height: int) -> str:
    return f"{scaled_px(width)}x{scaled_px(height)}"


# The launcher defaults assume the app sits beside backend/ and frontend/ folders.
APP_TITLE = "Dev Terminal Launcher"
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BACKEND_PATH = ROOT_DIR / "backend"
DEFAULT_FRONTEND_PATH = ROOT_DIR / "frontend"
DEFAULT_COMMAND = "npm run dev"
BACKEND_TAB_TITLE = "Backend"
FRONTEND_TAB_TITLE = "Frontend"
APP_GEOMETRY = scaled_geometry(900, 860)
APP_MIN_WIDTH = scaled_px(800)
APP_MIN_HEIGHT = scaled_px(920)
CARD_HEIGHT = scaled_px(184)
AGENT_CARD_HEIGHT = scaled_px(188)
LAUNCH_BUTTON_TEXT = "Open Terminal Tabs"
END_BUTTON_TEXT = "End Terminals"
SETTINGS_DIR_NAME = "DevTerminalLauncher"
SETTINGS_FILE_NAME = "settings.json"
APP_ICON_FILE_NAME = "app-icon.ico"
COLOR_MODE_DAY = "day"
COLOR_MODE_NIGHT = "night"
DEFAULT_COLOR_MODE = COLOR_MODE_DAY

COLOR_THEMES = {
    COLOR_MODE_NIGHT: {
        "outer_bg": "#c9c4cc",
        "bezel_bg": "#05070d",
        "screen_bg": "#101520",
        "card_bg": "#171d2a",
        "field_bg": "#0c111a",
        "field_border": "#2a3244",
        "text_primary": "#f5f7fb",
        "text_secondary": "#9ca8ba",
        "shadow_bg": "#080b12",
        "outline_hover_bg": "#111827",
    },
    COLOR_MODE_DAY: {
        "outer_bg": "#d7dde8",
        "bezel_bg": "#f7f9fc",
        "screen_bg": "#f7f9fc",
        "card_bg": "#ffffff",
        "field_bg": "#eef3f8",
        "field_border": "#c6ceda",
        "text_primary": "#172033",
        "text_secondary": "#5b6678",
        "shadow_bg": "#c4ccd8",
        "outline_hover_bg": "#edf2f7",
    },
}

# Color tokens used by the custom Tkinter canvas widgets.
OUTER_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["outer_bg"]
BEZEL_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["bezel_bg"]
SCREEN_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["screen_bg"]
CARD_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["card_bg"]
FIELD_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["field_bg"]
FIELD_BORDER = COLOR_THEMES[DEFAULT_COLOR_MODE]["field_border"]
TEXT_PRIMARY = COLOR_THEMES[DEFAULT_COLOR_MODE]["text_primary"]
TEXT_SECONDARY = COLOR_THEMES[DEFAULT_COLOR_MODE]["text_secondary"]
SHADOW_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["shadow_bg"]
OUTLINE_HOVER_BG = COLOR_THEMES[DEFAULT_COLOR_MODE]["outline_hover_bg"]
DEFAULT_ACCENT = "#06b6d4"
END_ACCENT = "#ef4444"
PANEL_SPLINE_STEPS = 12
AGENT_COMMANDS = {
    "Codex": "codex",
}

# Fixed accent palette used by the Customize appearance popup.
ACCENT_COLORS = (
    "#9cff1a",
    "#22c55e",
    "#06b6d4",
    "#38bdf8",
    "#3b82f6",
    "#a855f7",
    "#ec4899",
    "#f43f5e",
    "#f97316",
    "#facc15",
)


# =============================================================================
# Theme Helpers
# =============================================================================


def normalize_color_mode(value: object) -> str:
    return value if value in COLOR_THEMES else DEFAULT_COLOR_MODE


# Copy the selected theme into the global color tokens used by custom widgets.
def apply_color_mode_tokens(color_mode: str) -> None:
    global OUTER_BG
    global BEZEL_BG
    global SCREEN_BG
    global CARD_BG
    global FIELD_BG
    global FIELD_BORDER
    global TEXT_PRIMARY
    global TEXT_SECONDARY
    global SHADOW_BG
    global OUTLINE_HOVER_BG

    theme = COLOR_THEMES[normalize_color_mode(color_mode)]
    OUTER_BG = theme["outer_bg"]
    BEZEL_BG = theme["bezel_bg"]
    SCREEN_BG = theme["screen_bg"]
    CARD_BG = theme["card_bg"]
    FIELD_BG = theme["field_bg"]
    FIELD_BORDER = theme["field_border"]
    TEXT_PRIMARY = theme["text_primary"]
    TEXT_SECONDARY = theme["text_secondary"]
    SHADOW_BG = theme["shadow_bg"]
    OUTLINE_HOVER_BG = theme["outline_hover_bg"]
