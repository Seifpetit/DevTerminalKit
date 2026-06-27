from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

from . import app_config as config
from .actions import (
    Action,
    LaunchSelectedAgent,
    SaveCurrentPaths,
    SetColorMode,
    ToggleTerminals,
)
from .app_controller import AppController, ControllerResult
from .app_settings import set_window_icon
from .ui_widgets import draw_rounded_rect


HOVER_PRIMARY = "#2D7ACC"
LEFT_TRAFFIC_DOTS = (
    ("#FEBC2E", "minimize"),
    ("#28C840", "idle"),
)


class RoundedSurface(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        *,
        fill_key: str,
        outside_key: str,
        border_key: str | None = None,
        radius: int = config.RADIUS,
        border_width: int = 0,
        padding_x: int = 0,
        padding_y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        super().__init__(
            parent,
            bg=config.COLORS[outside_key],
            bd=0,
            highlightthickness=0,
            width=width,
            height=height,
        )
        self.fill_key = fill_key
        self.outside_key = outside_key
        self.border_key = border_key
        self.radius = radius
        self.border_width = border_width
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.fixed_width = width
        self.fixed_height = height
        self.content = tk.Frame(self, bg=config.COLORS[fill_key])
        self._content_window = self.create_window(
            border_width + padding_x,
            border_width + padding_y,
            anchor="nw",
            window=self.content,
        )
        self.content.bind("<Configure>", self._resize_to_content)
        self.bind("<Configure>", self._redraw)

    def _resize_to_content(self, _event: tk.Event) -> None:
        total_x = (self.border_width * 2) + (self.padding_x * 2)
        total_y = (self.border_width * 2) + (self.padding_y * 2)
        updates: dict[str, int] = {}
        if self.fixed_width is None:
            updates["width"] = self.content.winfo_reqwidth() + total_x
        if self.fixed_height is None:
            updates["height"] = self.content.winfo_reqheight() + total_y
        if updates:
            self.configure(**updates)

    def apply_theme(self) -> None:
        self.configure(bg=config.COLORS[self.outside_key])
        self.content.configure(bg=config.COLORS[self.fill_key])
        self._redraw()

    def _redraw(self, event: tk.Event | None = None) -> None:
        width = max(1, self.winfo_width() if event is None else event.width)
        height = max(1, self.winfo_height() if event is None else event.height)
        self.delete("surface")

        if self.border_key is not None and self.border_width:
            draw_rounded_rect(
                self,
                0,
                0,
                width,
                height,
                self.radius,
                fill=config.COLORS[self.border_key],
                outline="",
                tags="surface",
            )

        inset = self.border_width
        fill_radius = max(1, self.radius - inset)
        draw_rounded_rect(
            self,
            inset,
            inset,
            width - inset,
            height - inset,
            fill_radius,
            fill=config.COLORS[self.fill_key],
            outline="",
            tags="surface",
        )

        inner_width = max(1, width - (self.border_width * 2) - (self.padding_x * 2))
        inner_height = max(1, height - (self.border_width * 2) - (self.padding_y * 2))
        self.itemconfigure(self._content_window, width=inner_width, height=inner_height)
        self.tag_lower("surface")


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        *,
        text: str,
        command: Callable[[], None],
        font: tuple[str, int] | tuple[str, int, str],
        width: int,
        height: int,
        outside_key: str,
        radius: int = config.RADIUS,
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.font = font
        self.radius = radius
        self.outside_key = outside_key
        self.fill = config.COLORS["bg_surface"]
        self.foreground = config.COLORS["text_primary"]
        self.border = config.COLORS["border"]
        self.hovered = False
        self.pressed = False
        self.on_hover_change: Callable[[bool], None] | None = None

        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Configure>", lambda _event: self._redraw())
        self._redraw()

    def set_text(self, text: str) -> None:
        self.text = text
        self._redraw()

    def set_colors(self, *, fill: str, foreground: str, border: str) -> None:
        self.fill = fill
        self.foreground = foreground
        self.border = border
        self.configure(bg=config.COLORS[self.outside_key])
        self._redraw()

    def _redraw(self) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        self.delete("button")
        draw_rounded_rect(
            self,
            0,
            0,
            width,
            height,
            self.radius,
            fill=self.border,
            outline="",
            tags="button",
        )
        draw_rounded_rect(
            self,
            1,
            1,
            width - 1,
            height - 1,
            max(1, self.radius - 1),
            fill=self.fill,
            outline="",
            tags="button",
        )
        self.create_text(
            width // 2,
            height // 2,
            text=self.text,
            fill=self.foreground,
            font=self.font,
            tags="button",
        )

    def _enter(self, _event: tk.Event) -> None:
        self.hovered = True
        if self.on_hover_change is not None:
            self.on_hover_change(True)

    def _leave(self, _event: tk.Event) -> None:
        self.hovered = False
        self.pressed = False
        if self.on_hover_change is not None:
            self.on_hover_change(False)

    def _press(self, _event: tk.Event) -> None:
        self.pressed = True

    def _release(self, _event: tk.Event) -> None:
        was_pressed = self.pressed
        self.pressed = False
        if was_pressed and self.hovered:
            self.command()


class DevTerminalLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.controller = AppController.load()
        self.state = self.controller.state

        self.theme_registry: list[tuple[str, tk.Widget, str]] = []
        self.rounded_surfaces: list[RoundedSurface] = []
        self.button_registry: list[dict[str, object]] = []
        self.listboxes: list[tk.Listbox] = []
        self.theme_buttons: dict[str, dict[str, object]] = {}
        self.terminal_button: RoundedButton | None = None
        self.agent_listbox: tk.Listbox | None = None
        self.status_dot: tk.Canvas | None = None
        self.content_canvas: tk.Canvas | None = None
        self._drag_offset = (0, 0)

        self.backend_path = tk.StringVar(value=self.state.backend_path)
        self.frontend_path = tk.StringVar(value=self.state.frontend_path)
        self.agent_project_root = tk.StringVar(value=self.state.agent_project_root)
        self.backend_command = tk.StringVar(value=self.state.backend_command)
        self.frontend_command = tk.StringVar(value=self.state.frontend_command)
        self.status_text = tk.StringVar(value=self.state.status_text)

        self._configure_window()
        self._configure_ttk()
        self._build_ui()
        self.apply_theme(self.state.color_mode, dispatch=False)
        self.render()

    def _configure_window(self) -> None:
        self.title(config.APP_TITLE)
        set_window_icon(self)
        self.geometry(config.APP_GEOMETRY)
        self.minsize(config.APP_MIN_WIDTH, config.APP_MIN_HEIGHT)
        self.overrideredirect(True)
        self.bind("<Map>", self._restore_chrome_after_minimize)

    def _configure_ttk(self) -> None:
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        self._build_titlebar()
        self._build_header()
        self._build_scroll_area()
        self._build_footer()

    def dispatch(self, action: Action) -> None:
        self._apply_result(self.controller.dispatch(action))

    def _apply_result(self, result: ControllerResult) -> None:
        self.state = result.state
        self.render()
        if result.dialog is not None:
            messagebox.showerror(result.dialog.title, result.dialog.message)

    def render(self) -> None:
        self._sync_vars_from_state()
        self.status_text.set(self.state.status_text)
        if self.terminal_button is not None:
            text = config.END_BUTTON_TEXT if self.state.terminals_running else config.LAUNCH_BUTTON_TEXT
            self.terminal_button.configure(text=text)
        self.apply_theme(self.state.color_mode, dispatch=False)

    def _sync_vars_from_state(self) -> None:
        self._set_if_changed(self.backend_path, self.state.backend_path)
        self._set_if_changed(self.frontend_path, self.state.frontend_path)
        self._set_if_changed(self.agent_project_root, self.state.agent_project_root)
        self._set_if_changed(self.backend_command, self.state.backend_command)
        self._set_if_changed(self.frontend_command, self.state.frontend_command)

    @staticmethod
    def _set_if_changed(variable: tk.StringVar, value: str) -> None:
        if variable.get() != value:
            variable.set(value)

    def apply_theme(self, mode: str, *, dispatch: bool = True) -> None:
        next_mode = config.normalize_color_mode(mode)
        if dispatch and next_mode != self.state.color_mode:
            self.dispatch(SetColorMode(next_mode))
            return

        config.apply_color_mode_tokens(next_mode)
        colors = config.COLORS
        self.configure(bg=colors["bg_page"])
        self._configure_ttk_colors()

        for option, widget, color_key in self.theme_registry:
            try:
                widget.configure(**{option: colors[color_key]})
            except tk.TclError:
                continue

        for listbox in self.listboxes:
            listbox.configure(
                bg=colors["bg_surface"],
                fg=colors["text_primary"],
                selectbackground=colors["fill_accent"],
                selectforeground=colors["on_accent"],
            )

        for surface in self.rounded_surfaces:
            surface.apply_theme()
        self._draw_status_dot()
        for button_info in self.button_registry:
            self._style_button(button_info)

    def _configure_ttk_colors(self) -> None:
        colors = config.COLORS
        self.style.configure(
            "Vertical.TScrollbar",
            background=colors["bg_surface"],
            troughcolor=colors["bg_page"],
            bordercolor=colors["border"],
            arrowcolor=colors["text_muted"],
            relief="flat",
        )

    def _register_theme(self, widget: tk.Widget, option: str, color_key: str) -> None:
        self.theme_registry.append((option, widget, color_key))
        widget.configure(**{option: config.COLORS[color_key]})

    def _themed_frame(self, parent: tk.Widget, color_key: str, **options: object) -> tk.Frame:
        frame = tk.Frame(parent, bg=config.COLORS[color_key], **options)
        self._register_theme(frame, "bg", color_key)
        return frame

    def _rounded_content(
        self,
        parent: tk.Widget,
        *,
        fill_key: str,
        outside_key: str,
        border_key: str | None = None,
        radius: int = config.RADIUS,
        border_width: int = 0,
        padding_x: int = 0,
        padding_y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> tuple[RoundedSurface, tk.Frame]:
        surface = RoundedSurface(
            parent,
            fill_key=fill_key,
            outside_key=outside_key,
            border_key=border_key,
            radius=radius,
            border_width=border_width,
            padding_x=padding_x,
            padding_y=padding_y,
            width=width,
            height=height,
        )
        self.rounded_surfaces.append(surface)
        return surface, surface.content

    def _themed_label(
        self,
        parent: tk.Widget,
        *,
        text: str | None = None,
        textvariable: tk.StringVar | None = None,
        bg: str,
        fg: str,
        font: tuple[str, int] | tuple[str, int, str],
        **options: object,
    ) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            textvariable=textvariable,
            bg=config.COLORS[bg],
            fg=config.COLORS[fg],
            font=font,
            **options,
        )
        self._register_theme(label, "bg", bg)
        self._register_theme(label, "fg", fg)
        return label

    def _build_titlebar(self) -> None:
        titlebar = self._themed_frame(self, "bg_page", height=36)
        titlebar.pack(fill="x")
        titlebar.grid_columnconfigure(0, minsize=76)
        titlebar.grid_columnconfigure(1, weight=1)
        titlebar.grid_columnconfigure(2, minsize=76)
        self._bind_drag(titlebar)

        dots = self._themed_frame(titlebar, "bg_page")
        dots.grid(row=0, column=0, sticky="w", padx=(16, 0), pady=12)
        for color, action in LEFT_TRAFFIC_DOTS:
            dot = self._traffic_dot(dots, color)
            dot.pack(side="left", padx=(0, 8))
            if action == "minimize":
                dot.bind("<Button-1>", lambda _event: self._minimize_window())

        title = self._themed_label(
            titlebar,
            text=config.APP_TITLE,
            bg="bg_page",
            fg="text_muted",
            font=config.FONT_SUB,
        )
        title.grid(row=0, column=1, pady=9)
        self._bind_drag(title)

        close_area = self._themed_frame(titlebar, "bg_page")
        close_area.grid(row=0, column=2, sticky="e", padx=(0, 16), pady=12)
        close_dot = self._traffic_dot(close_area, "#FF5F57")
        close_dot.pack()
        close_dot.bind("<Button-1>", lambda _event: self.destroy())

    def _traffic_dot(self, parent: tk.Widget, color: str) -> tk.Canvas:
        dot = tk.Canvas(parent, width=12, height=12, bg=config.COLORS["bg_page"], bd=0, highlightthickness=0)
        self._register_theme(dot, "bg", "bg_page")
        dot.create_oval(1, 1, 11, 11, fill=color, outline=color)
        dot.configure(cursor="hand2")
        return dot

    def _build_header(self) -> None:
        header = self._themed_frame(self, "bg_page")
        header.pack(fill="x", padx=24, pady=(6, 0))
        header.grid_columnconfigure(0, weight=1)

        brand = self._themed_frame(header, "bg_page")
        brand.grid(row=0, column=0, sticky="w")

        icon = self._icon_box(brand, ">_", "bg_accent", "text_accent", size=24, outside_key="bg_page")
        icon.pack(side="left")
        self._themed_label(
            brand,
            text="terminal studio",
            bg="bg_page",
            fg="text_muted",
            font=config.FONT_SUB,
        ).pack(side="left", padx=(8, 0))

        toggle = self._themed_frame(header, "bg_page")
        toggle.grid(row=0, column=1, sticky="e")
        self._make_button(
            toggle,
            text="Day",
            command=lambda: self.apply_theme(config.COLOR_MODE_DAY),
            variant="theme",
            mode=config.COLOR_MODE_DAY,
            outside_key="bg_page",
            padx=12,
            pady=5,
        ).pack(side="left", padx=(0, 4))
        self._make_button(
            toggle,
            text="Night",
            command=lambda: self.apply_theme(config.COLOR_MODE_NIGHT),
            variant="theme",
            mode=config.COLOR_MODE_NIGHT,
            outside_key="bg_page",
            padx=12,
            pady=5,
        ).pack(side="left")

        self._themed_label(
            header,
            text="Launch workspace",
            bg="bg_page",
            fg="text_primary",
            font=config.FONT_HEAD,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(18, 2))

        self._themed_label(
            header,
            text="Two named PowerShell tabs. One path and one command per workspace.",
            bg="bg_page",
            fg="text_muted",
            font=config.FONT_SUB,
        ).grid(row=2, column=0, columnspan=2, sticky="w")

        underline = self._themed_frame(header, "fill_accent", width=36, height=2)
        underline.grid(row=3, column=0, sticky="w", pady=(14, 16))
        underline.grid_propagate(False)

        border = self._themed_frame(self, "border", height=1)
        border.pack(fill="x")
        border.pack_propagate(False)

    def _build_scroll_area(self) -> None:
        shell = self._themed_frame(self, "bg_page")
        shell.pack(fill="both", expand=True)

        canvas = tk.Canvas(shell, bg=config.COLORS["bg_page"], bd=0, highlightthickness=0)
        self.content_canvas = canvas
        self._register_theme(canvas, "bg", "bg_page")
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        cards = self._themed_frame(canvas, "bg_page", padx=16, pady=16)
        window_id = canvas.create_window((0, 0), window=cards, anchor="nw")

        cards.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
        canvas.bind("<MouseWheel>", self._on_mousewheel)
        cards.bind("<MouseWheel>", self._on_mousewheel)

        self._build_workspace_card(
            cards,
            title="Backend",
            badge="PowerShell tab",
            icon_text="API",
            icon_bg="bg_accent",
            icon_fg="text_accent",
            path_label="Path",
            path_variable=self.backend_path,
            command_variable=self.backend_command,
        )
        self._build_workspace_card(
            cards,
            title="Frontend",
            badge="PowerShell tab",
            icon_text="UI",
            icon_bg="bg_orange",
            icon_fg="icon_orange",
            path_label="Path",
            path_variable=self.frontend_path,
            command_variable=self.frontend_command,
        )
        self._build_agent_card(cards)

    def _build_footer(self) -> None:
        border = self._themed_frame(self, "border", height=1)
        border.pack(fill="x")
        border.pack_propagate(False)

        footer = self._themed_frame(self, "bg_page", padx=24, pady=14)
        footer.pack(fill="x")
        footer.grid_columnconfigure(0, weight=1)

        status = self._themed_frame(footer, "bg_page")
        status.grid(row=0, column=0, sticky="w")

        self.status_dot = tk.Canvas(status, width=6, height=6, bg=config.COLORS["bg_page"], bd=0, highlightthickness=0)
        self._register_theme(self.status_dot, "bg", "bg_page")
        self.status_dot.pack(side="left", pady=6)
        self._draw_status_dot()

        self._themed_label(
            status,
            textvariable=self.status_text,
            bg="bg_page",
            fg="text_muted",
            font=config.FONT_SUB,
        ).pack(side="left", padx=(8, 0))

        button_frame = self._make_button(
            footer,
            text=config.LAUNCH_BUTTON_TEXT,
            command=self.toggle_terminals,
            variant="primary",
            role="terminal",
            outside_key="bg_page",
            padx=18,
            pady=9,
            font=("Segoe UI", 10, "bold"),
        )
        button_frame.grid(row=0, column=1, sticky="e")
        self.terminal_button = button_frame

    def _build_workspace_card(
        self,
        parent: tk.Widget,
        *,
        title: str,
        badge: str,
        icon_text: str,
        icon_bg: str,
        icon_fg: str,
        path_label: str,
        path_variable: tk.StringVar,
        command_variable: tk.StringVar,
    ) -> None:
        card = self._card(parent)
        self._card_header(card, title, badge, icon_text, icon_bg, icon_fg)
        self._field_row(card, 1, path_label, path_variable, browse=True)
        self._field_row(card, 2, "Command", command_variable, browse=False)

    def _build_agent_card(self, parent: tk.Widget) -> None:
        card = self._card(parent)
        self._card_header(card, "Agent", "Interactive terminal", "AI", "bg_purple", "icon_purple")
        self._field_row(card, 1, "Project root", self.agent_project_root, browse=True)
        self._agent_row(card, 2)

    def _card(self, parent: tk.Widget) -> tk.Frame:
        surface, card = self._rounded_content(
            parent,
            fill_key="bg_card",
            outside_key="bg_page",
            border_key="border",
            radius=10,
            border_width=1,
            padding_x=16,
            padding_y=16,
        )
        surface.pack(fill="x", pady=(0, 12))
        card.grid_columnconfigure(0, minsize=80)
        card.grid_columnconfigure(1, weight=1)
        return card

    def _card_header(
        self,
        card: tk.Widget,
        title: str,
        badge: str,
        icon_text: str,
        icon_bg: str,
        icon_fg: str,
    ) -> None:
        header = self._themed_frame(card, "bg_card")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(1, weight=1)

        icon = self._icon_box(header, icon_text, icon_bg, icon_fg, size=24)
        icon.grid(row=0, column=0, sticky="w")

        self._themed_label(
            header,
            text=title,
            bg="bg_card",
            fg="text_primary",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        badge_outer, badge_inner = self._rounded_content(
            header,
            fill_key="bg_surface",
            outside_key="bg_card",
            border_key="border",
            radius=5,
            border_width=1,
            padding_x=8,
            padding_y=3,
        )
        badge_outer.grid(row=0, column=2, sticky="e")
        self._themed_label(
            badge_inner,
            text=badge,
            bg="bg_surface",
            fg="text_muted",
            font=config.FONT_SUB,
        ).pack()

    def _field_row(
        self,
        card: tk.Widget,
        row: int,
        label_text: str,
        variable: tk.StringVar,
        *,
        browse: bool,
    ) -> None:
        self._field_label(card, label_text).grid(row=row, column=0, sticky="w", pady=5)
        self._entry(card, variable).grid(row=row, column=1, sticky="ew", padx=(10, 8), pady=5)
        if browse:
            self._make_button(
                card,
                text="Browse",
                command=lambda: self.choose_folder(variable),
                variant="browse",
                padx=13,
                pady=7,
            ).grid(row=row, column=2, sticky="e", pady=5)
        else:
            spacer = self._themed_frame(card, "bg_card", width=88, height=1)
            spacer.grid(row=row, column=2, sticky="e", pady=5)
            spacer.grid_propagate(False)

    def _agent_row(self, card: tk.Widget, row: int) -> None:
        self._field_label(card, "Agent").grid(row=row, column=0, sticky="w", pady=5)

        listbox_outer, listbox_inner = self._rounded_content(
            card,
            fill_key="bg_surface",
            outside_key="bg_card",
            border_key="border",
            radius=6,
            border_width=1,
            padding_x=7,
            padding_y=4,
        )
        listbox_outer.grid(row=row, column=1, sticky="ew", padx=(10, 8), pady=5)

        listbox = tk.Listbox(
            listbox_inner,
            height=1,
            activestyle="none",
            bg=config.COLORS["bg_surface"],
            fg=config.COLORS["text_primary"],
            selectbackground=config.COLORS["fill_accent"],
            selectforeground=config.COLORS["on_accent"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            exportselection=False,
            selectmode=tk.SINGLE,
            font=config.FONT_MONO,
        )
        listbox.pack(fill="x")
        for agent_name in config.AGENT_COMMANDS:
            listbox.insert(tk.END, agent_name)
        listbox.selection_set(0)
        self.agent_listbox = listbox
        self.listboxes.append(listbox)

        self._make_button(
            card,
            text="Launch agent",
            command=self.launch_selected_agent,
            variant="primary",
            padx=14,
            pady=8,
        ).grid(row=row, column=2, sticky="e", pady=5)

    def _field_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return self._themed_label(
            parent,
            text=text,
            bg="bg_card",
            fg="text_muted",
            font=config.FONT_LABEL,
            anchor="w",
        )

    def _entry(self, parent: tk.Widget, variable: tk.StringVar) -> tk.Frame:
        outer, inner = self._rounded_content(
            parent,
            fill_key="bg_surface",
            outside_key="bg_card",
            border_key="border",
            radius=6,
            border_width=1,
            padding_x=7,
            padding_y=4,
        )
        entry = tk.Entry(
            inner,
            textvariable=variable,
            bg=config.COLORS["bg_surface"],
            fg=config.COLORS["text_primary"],
            insertbackground=config.COLORS["text_primary"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=config.FONT_MONO,
        )
        self._register_theme(entry, "bg", "bg_surface")
        self._register_theme(entry, "fg", "text_primary")
        self._register_theme(entry, "insertbackground", "text_primary")
        entry.pack(fill="x")
        return outer

    def _icon_box(
        self,
        parent: tk.Widget,
        text: str,
        bg_key: str,
        fg_key: str,
        *,
        size: int,
        outside_key: str = "bg_card",
    ) -> RoundedSurface:
        surface, box = self._rounded_content(
            parent,
            fill_key=bg_key,
            outside_key=outside_key,
            radius=6,
            padding_x=1,
            padding_y=1,
            width=size,
            height=size,
        )
        self._themed_label(
            box,
            text=text,
            bg=bg_key,
            fg=fg_key,
            font=("Segoe UI", 8, "bold"),
        ).pack(expand=True)
        return surface

    def _make_button(
        self,
        parent: tk.Widget,
        *,
        text: str,
        command: Callable[[], None],
        variant: str,
        mode: str | None = None,
        role: str | None = None,
        outside_key: str = "bg_card",
        padx: int = 10,
        pady: int = 6,
        font: tuple[str, int] | tuple[str, int, str] = config.FONT_BTN,
    ) -> RoundedButton:
        width = max(44, round(len(text) * 7.2) + (padx * 2))
        height = max(24, 18 + (pady * 2))
        if variant == "browse":
            width = max(width, 82)
        elif variant == "primary" and role == "terminal":
            width = max(width, 164)
        elif variant == "primary":
            width = max(width, 112)
        elif variant == "theme":
            width = max(width, 58)

        button = RoundedButton(
            parent,
            text=text,
            command=command,
            font=font,
            width=width,
            height=height,
            outside_key=outside_key,
            radius=config.RADIUS,
        )

        info: dict[str, object] = {
            "button": button,
            "variant": variant,
            "mode": mode,
            "role": role,
            "hover": False,
        }
        self.button_registry.append(info)
        if variant == "theme" and mode is not None:
            self.theme_buttons[mode] = info

        button.on_hover_change = lambda hovered, item=info: self._set_button_hover(item, hovered)
        self._style_button(info)
        return button

    def _set_button_hover(self, button_info: dict[str, object], hovered: bool) -> None:
        button_info["hover"] = hovered
        self._style_button(button_info)

    def _style_button(self, button_info: dict[str, object]) -> None:
        colors = config.COLORS
        button = button_info["button"]
        if not isinstance(button, RoundedButton):
            return

        variant = button_info["variant"]
        hovered = bool(button_info["hover"])
        bg = colors["bg_surface"]
        fg = colors["text_primary"]
        border = colors["border"]

        if variant == "primary":
            bg = config.END_ACCENT if button_info.get("role") == "terminal" and self.state.terminals_running else colors["fill_accent"]
            bg = self._darken(bg, 0.08) if hovered else bg
            fg = colors["on_accent"]
            border = bg
        elif variant == "browse":
            bg = colors["fill_accent"] if hovered else colors["bg_accent"]
            fg = colors["on_accent"] if hovered else colors["text_accent"]
            border = colors["fill_accent"] if hovered else colors["border_accent"]
        elif variant == "theme":
            active = button_info.get("mode") == self.state.color_mode
            if active:
                bg = colors["bg_card"]
                fg = colors["text_primary"]
                border = colors["border_accent"]
            elif hovered:
                bg = colors["bg_accent"]
                fg = colors["text_accent"]
                border = colors["border_accent"]
            else:
                bg = colors["bg_surface"]
                fg = colors["text_secondary"]
                border = colors["border"]

        button.set_colors(fill=bg, foreground=fg, border=border)

    @staticmethod
    def _darken(color: str, amount: float) -> str:
        color = color.lstrip("#")
        red = max(0, int(int(color[0:2], 16) * (1 - amount)))
        green = max(0, int(int(color[2:4], 16) * (1 - amount)))
        blue = max(0, int(int(color[4:6], 16) * (1 - amount)))
        return f"#{red:02x}{green:02x}{blue:02x}"

    def _draw_status_dot(self) -> None:
        if self.status_dot is None:
            return
        self.status_dot.delete("all")
        self.status_dot.create_oval(
            0,
            0,
            6,
            6,
            fill=config.COLORS["status_green"],
            outline=config.COLORS["status_green"],
        )

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.content_canvas is not None:
            self.content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_drag(self, widget: tk.Widget) -> None:
        widget.bind("<ButtonPress-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._drag_window)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _drag_window(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.geometry(f"+{x}+{y}")

    def _minimize_window(self) -> None:
        self.overrideredirect(False)
        self.iconify()

    def _restore_chrome_after_minimize(self, _event: tk.Event) -> None:
        if tk.Tk.state(self) == "normal":
            self.overrideredirect(True)

    def choose_folder(self, variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=variable.get() or str(config.ROOT_DIR))
        if selected:
            variable.set(selected)
            self.save_current_paths()

    def save_current_paths(self) -> None:
        self.dispatch(
            SaveCurrentPaths(
                backend_path=self.backend_path.get(),
                frontend_path=self.frontend_path.get(),
                agent_project_root=self.agent_project_root.get(),
            )
        )

    def get_selected_agent_name(self) -> str | None:
        if self.agent_listbox is None:
            return None
        selection = self.agent_listbox.curselection()
        if not selection:
            return None
        agent_name = self.agent_listbox.get(selection[0])
        return agent_name if agent_name in config.AGENT_COMMANDS else None

    def launch_selected_agent(self) -> None:
        self.dispatch(
            LaunchSelectedAgent(
                agent_name=self.get_selected_agent_name(),
                project_root=self.agent_project_root.get(),
            )
        )

    def toggle_terminals(self) -> None:
        self.dispatch(
            ToggleTerminals(
                backend_path=self.backend_path.get(),
                frontend_path=self.frontend_path.get(),
                backend_command=self.backend_command.get(),
                frontend_command=self.frontend_command.get(),
            )
        )
