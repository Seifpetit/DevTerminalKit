from __future__ import annotations

from pathlib import Path


# =============================================================================
# App Configuration
# =============================================================================

UI_SCALE = 1.0


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
APP_GEOMETRY = "620x760"
APP_MIN_WIDTH = 560
APP_MIN_HEIGHT = 680
CARD_HEIGHT = 184
AGENT_CARD_HEIGHT = 188
LAUNCH_BUTTON_TEXT = "Open terminal tabs"
END_BUTTON_TEXT = "End terminals"
SETTINGS_DIR_NAME = "DevTerminalLauncher"
SETTINGS_FILE_NAME = "settings.json"
APP_ICON_FILE_NAME = "app-icon.ico"
COLOR_MODE_DAY = "day"
COLOR_MODE_NIGHT = "night"
DEFAULT_COLOR_MODE = COLOR_MODE_DAY

THEMES = {
    COLOR_MODE_DAY: {
        "bg_page": "#F1EFE8",
        "bg_card": "#FFFFFF",
        "bg_surface": "#F8F7F4",
        "border": "#E2DDD5",
        "border_accent": "#B5D4F4",
        "bg_accent": "#E6F1FB",
        "fill_accent": "#378ADD",
        "text_primary": "#1A1A18",
        "text_secondary": "#5F5E5A",
        "text_muted": "#888780",
        "text_accent": "#185FA5",
        "on_accent": "#FFFFFF",
        "bg_orange": "#FFF3E0",
        "icon_orange": "#F57C00",
        "bg_purple": "#EEEDFE",
        "icon_purple": "#534AB7",
        "status_green": "#28C840",
    },
    COLOR_MODE_NIGHT: {
        "bg_page": "#1A1A1E",
        "bg_card": "#26262C",
        "bg_surface": "#1E1E24",
        "border": "#3A3A42",
        "border_accent": "#2D5A8A",
        "bg_accent": "#0C2A44",
        "fill_accent": "#378ADD",
        "text_primary": "#F0EFE8",
        "text_secondary": "#A8A6A0",
        "text_muted": "#666460",
        "text_accent": "#85B7EB",
        "on_accent": "#FFFFFF",
        "bg_orange": "#2A1F10",
        "icon_orange": "#F59A40",
        "bg_purple": "#1E1A38",
        "icon_purple": "#AFA9EC",
        "status_green": "#28C840",
    },
}

current_theme = COLOR_MODE_DAY
COLORS = THEMES[current_theme]

FONT_MAIN = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 9)
FONT_HEAD = ("Segoe UI", 14, "bold")
FONT_SUB = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 9, "bold")
RADIUS = 8

# Compatibility aliases for helper modules that still import the old token names.
COLOR_THEMES = THEMES
OUTER_BG = COLORS["bg_page"]
BEZEL_BG = COLORS["bg_card"]
SCREEN_BG = COLORS["bg_page"]
CARD_BG = COLORS["bg_card"]
FIELD_BG = COLORS["bg_surface"]
FIELD_BORDER = COLORS["border"]
TEXT_PRIMARY = COLORS["text_primary"]
TEXT_SECONDARY = COLORS["text_secondary"]
SHADOW_BG = COLORS["border"]
OUTLINE_HOVER_BG = COLORS["bg_surface"]
DEFAULT_ACCENT = COLORS["fill_accent"]
END_ACCENT = "#FF5F57"
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
    return value if value in THEMES else DEFAULT_COLOR_MODE


# Copy the selected theme into the global color tokens used by custom widgets.
def apply_color_mode_tokens(color_mode: str) -> None:
    global current_theme
    global COLORS
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

    current_theme = normalize_color_mode(color_mode)
    COLORS = THEMES[current_theme]
    OUTER_BG = COLORS["bg_page"]
    BEZEL_BG = COLORS["bg_card"]
    SCREEN_BG = COLORS["bg_page"]
    CARD_BG = COLORS["bg_card"]
    FIELD_BG = COLORS["bg_surface"]
    FIELD_BORDER = COLORS["border"]
    TEXT_PRIMARY = COLORS["text_primary"]
    TEXT_SECONDARY = COLORS["text_secondary"]
    SHADOW_BG = COLORS["border"]
    OUTLINE_HOVER_BG = COLORS["bg_surface"]
