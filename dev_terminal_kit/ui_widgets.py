from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from . import app_config as config


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    **options: str,
) -> int:
    radius = max(1, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=config.PANEL_SPLINE_STEPS, **options)


# Convert CSS-style hex colors into channels for simple color math.
def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


# Pick readable foreground text for the current accent button color.
def contrast_text_color(background: str) -> str:
    red, green, blue = hex_to_rgb(background)
    brightness = (red * 299 + green * 587 + blue * 114) / 1000
    return "#080b10" if brightness > 145 else "#ffffff"


# Used for hover/pressed states on accent buttons.
def darken(color: str, amount: float = 0.18) -> str:
    red, green, blue = hex_to_rgb(color)
    return "#{:02x}{:02x}{:02x}".format(
        max(0, int(red * (1 - amount))),
        max(0, int(green * (1 - amount))),
        max(0, int(blue * (1 - amount))),
    )


# =============================================================================
# Custom Canvas Widgets
# =============================================================================

# RoundedPanel provides card/surface backgrounds plus an embedded content frame.
class RoundedPanel(tk.Canvas):
    # Create a rounded canvas with a child Frame mounted inside it.
    def __init__(
        self,
        parent: tk.Widget,
        *,
        fill: str,
        parent_bg: str,
        radius: int,
        padding: int,
        height: int | None = None,
        shadow: bool = False,
    ) -> None:
        super().__init__(
            parent,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            height=height,
        )
        self.fill = fill
        self.radius = radius
        self.padding = padding
        self.shadow = shadow
        self._last_size: tuple[int, int] | None = None
        self.content = tk.Frame(self, bg=fill)
        self._content_window = self.create_window(
            padding,
            padding,
            anchor="nw",
            window=self.content,
        )
        self.bind("<Configure>", self._redraw)

    # Redraw only when size changes to avoid slow repeated canvas work.
    def _redraw(self, event: tk.Event) -> None:
        width = max(1, event.width)
        height = max(1, event.height)
        if self._last_size == (width, height):
            return
        self._last_size = (width, height)
        self.delete("panel")

        if self.shadow:
            draw_rounded_rect(
                self,
                config.scaled_px(6),
                config.scaled_px(8),
                width - config.scaled_px(2),
                height - config.scaled_px(2),
                self.radius,
                fill=config.SHADOW_BG,
                outline="",
                tags="panel",
            )

        draw_rounded_rect(
            self,
            1,
            1,
            width - config.scaled_px(7) if self.shadow else width - 1,
            height - config.scaled_px(9) if self.shadow else height - 1,
            self.radius,
            fill=self.fill,
            outline="",
            tags="panel",
        )

        inner_width = max(1, width - (self.padding * 2) - (config.scaled_px(8) if self.shadow else 0))
        inner_height = max(1, height - (self.padding * 2) - (config.scaled_px(10) if self.shadow else 0))
        self.itemconfigure(self._content_window, width=inner_width, height=inner_height)
        self.tag_lower("panel")


# RoundedEntry wraps a normal Entry inside a rounded canvas shell.
class RoundedEntry(tk.Canvas):
    # Create a single-line entry with a rounded drawn background.
    def __init__(
        self,
        parent: tk.Widget,
        *,
        variable: tk.StringVar,
        accent: str,
        width: int = config.scaled_px(360),
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=config.scaled_px(42),
            bg=config.CARD_BG,
            bd=0,
            highlightthickness=0,
        )
        self.accent = accent
        self.focused = False
        self._last_draw: tuple[int, int, str, bool] | None = None
        self.entry = tk.Entry(
            self,
            textvariable=variable,
            bg=config.FIELD_BG,
            fg=config.TEXT_PRIMARY,
            insertbackground=config.TEXT_PRIMARY,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", config.scaled_font(10)),
        )
        self._entry_window = self.create_window(config.scaled_px(16), config.scaled_px(21), anchor="w", window=self.entry)
        self.bind("<Configure>", self._redraw)
        self.entry.bind("<FocusIn>", self._set_focus)
        self.entry.bind("<FocusOut>", self._clear_focus)

    # Accent changes affect focus rings, so the field needs a redraw.
    def set_accent(self, accent: str) -> None:
        self.accent = accent
        self._redraw()

    # Focus state controls whether the accent border is visible.
    def _set_focus(self, _event: tk.Event) -> None:
        self.focused = True
        self._redraw()

    # Remove the accent border when focus leaves the entry.
    def _clear_focus(self, _event: tk.Event) -> None:
        self.focused = False
        self._redraw()

    # Cache the last drawn state so resize/focus events do not repaint needlessly.
    def _redraw(self, event: tk.Event | None = None) -> None:
        width = max(1, self.winfo_width() if event is None else event.width)
        height = max(1, self.winfo_height() if event is None else event.height)
        draw_state = (width, height, self.accent, self.focused)
        if self._last_draw == draw_state:
            return
        self._last_draw = draw_state
        outline = self.accent if self.focused else config.FIELD_BORDER
        self.delete("field")
        draw_rounded_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            config.scaled_px(18),
            fill=config.FIELD_BG,
            outline=outline,
            tags="field",
        )
        self.itemconfigure(self._entry_window, width=max(1, width - config.scaled_px(32)), height=config.scaled_px(24))
        self.tag_lower("field")


# PillButton is a canvas button with rounded shape, hover, pressed, and recolor states.
class PillButton(tk.Canvas):
    # Create a clickable rounded canvas button.
    def __init__(
        self,
        parent: tk.Widget,
        *,
        text: str,
        command: Callable[[], None],
        accent: str,
        variant: str = "accent",
        width: int = config.scaled_px(150),
        height: int = config.scaled_px(38),
        parent_bg: str = config.CARD_BG,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.accent = accent
        self.variant = variant
        self.hovered = False
        self.pressed = False
        self._last_draw: tuple[int, int, str, str, str, bool, bool] | None = None

        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", lambda _event: self._redraw())
        self._redraw()

    # Accent colors can change from the appearance palette.
    def set_accent(self, accent: str) -> None:
        self.accent = accent
        self._redraw()

    # The launch button switches text between launch and terminate modes.
    def set_text(self, text: str) -> None:
        self.text = text
        self._redraw()

    # Resolve visual colors from variant and interaction state.
    def _colors(self) -> tuple[str, str, str]:
        if self.variant == "outline":
            fill = config.OUTLINE_HOVER_BG if self.hovered else config.SCREEN_BG
            return fill, self.accent, self.accent

        fill = darken(self.accent, 0.12 if self.hovered else 0.0)
        if self.pressed:
            fill = darken(self.accent, 0.22)
        return fill, "", contrast_text_color(fill)

    # Redraw the canvas button only when one of its visual inputs changes.
    def _redraw(self) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        fill, outline, foreground = self._colors()
        draw_state = (
            width,
            height,
            self.text,
            self.accent,
            self.variant,
            self.hovered,
            self.pressed,
        )
        if self._last_draw == draw_state:
            return
        self._last_draw = draw_state
        self.delete("button")
        draw_rounded_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            height // 2,
            fill=fill,
            outline=outline,
            tags="button",
        )
        self.create_text(
            width // 2,
            height // 2,
            text=self.text,
            fill=foreground,
            font=("Segoe UI", config.scaled_font(10), "bold"),
            tags="button",
        )

    # Mouse handlers intentionally keep all button behavior inside this widget.
    def _press(self, _event: tk.Event) -> None:
        self.pressed = True
        self._redraw()

    # Invoke the button command only for click-release inside the button.
    def _release(self, _event: tk.Event) -> None:
        was_pressed = self.pressed
        self.pressed = False
        self._redraw()
        if was_pressed and self.hovered:
            self.command()

    # Track hover state for button styling.
    def _enter(self, _event: tk.Event) -> None:
        self.hovered = True
        self._redraw()

    # Clear transient interaction state after leaving the button.
    def _leave(self, _event: tk.Event) -> None:
        self.hovered = False
        self.pressed = False
        self._redraw()


# ColorModeSwitch toggles the persisted day/night theme.
class ColorModeSwitch(tk.Canvas):
    # Create a two-segment switch using the current accent color.
    def __init__(
        self,
        parent: tk.Widget,
        *,
        mode: str,
        command: Callable[[], None],
        accent: str,
        width: int = config.scaled_px(118),
        height: int = config.scaled_px(34),
        parent_bg: str = config.SCREEN_BG,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.mode = config.normalize_color_mode(mode)
        self.command = command
        self.accent = accent
        self.hovered = False
        self.pressed = False
        self._last_draw: tuple[int, int, str, str, bool, bool] | None = None

        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", lambda _event: self._redraw())
        self._redraw()

    # Keep the active segment in sync with palette changes.
    def set_accent(self, accent: str) -> None:
        self.accent = accent
        self._redraw()

    # Update the selected segment after a mode change.
    def set_mode(self, mode: str) -> None:
        self.mode = config.normalize_color_mode(mode)
        self._redraw()

    # Draw the segmented day/night switch.
    def _redraw(self) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        draw_state = (width, height, self.mode, self.accent, self.hovered, self.pressed)
        if self._last_draw == draw_state:
            return
        self._last_draw = draw_state

        radius = height // 2
        inset = config.scaled_px(3)
        segment_width = (width - inset * 2) // 2
        active_x = inset if self.mode == config.COLOR_MODE_DAY else width - inset - segment_width
        active_fill = darken(self.accent, 0.12) if self.pressed else self.accent
        if self.hovered and not self.pressed:
            active_fill = darken(self.accent, 0.06)

        self.delete("switch")
        draw_rounded_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            radius,
            fill=config.FIELD_BG,
            outline=config.FIELD_BORDER,
            tags="switch",
        )
        draw_rounded_rect(
            self,
            active_x,
            inset,
            active_x + segment_width,
            height - inset,
            radius - inset,
            fill=active_fill,
            outline="",
            tags="switch",
        )
        self.create_text(
            width // 4,
            height // 2,
            text="Day",
            fill=contrast_text_color(active_fill) if self.mode == config.COLOR_MODE_DAY else config.TEXT_SECONDARY,
            font=("Segoe UI", config.scaled_font(9), "bold"),
            tags="switch",
        )
        self.create_text(
            (width * 3) // 4,
            height // 2,
            text="Night",
            fill=contrast_text_color(active_fill) if self.mode == config.COLOR_MODE_NIGHT else config.TEXT_SECONDARY,
            font=("Segoe UI", config.scaled_font(9), "bold"),
            tags="switch",
        )

    # Mark the switch as pressed for immediate visual feedback.
    def _press(self, _event: tk.Event) -> None:
        self.pressed = True
        self._redraw()

    # Toggle the mode only when release happens over the switch.
    def _release(self, _event: tk.Event) -> None:
        was_pressed = self.pressed
        self.pressed = False
        self._redraw()
        if was_pressed and self.hovered:
            self.command()

    # Track hover state for switch styling.
    def _enter(self, _event: tk.Event) -> None:
        self.hovered = True
        self._redraw()

    # Clear transient switch state when the pointer leaves.
    def _leave(self, _event: tk.Event) -> None:
        self.hovered = False
        self.pressed = False
        self._redraw()
