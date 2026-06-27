from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox

from . import app_config as config
from .actions import (
    Action,
    LaunchSelectedAgent,
    SaveCurrentPaths,
    SelectAccentColor,
    ToggleColorMode,
    ToggleTerminals,
)
from .app_controller import AppController, ControllerResult
from .app_settings import set_window_icon
from .ui_tree import UINode, mount_ui_tree, rounded_panel_content
from .ui_widgets import (
    ColorModeSwitch,
    PillButton,
    RoundedEntry,
    RoundedPanel,
    contrast_text_color,
    draw_rounded_rect,
)


# =============================================================================
# Main Application Window
# =============================================================================

class DevTerminalLauncher(tk.Tk):
    # Initialize settings, state variables, and the frontend tree.
    def __init__(self) -> None:
        super().__init__()

        self.controller = AppController.load()
        self.state = self.controller.state

        self.title(config.APP_TITLE)
        set_window_icon(self)
        self.geometry(config.APP_GEOMETRY)
        self.minsize(config.APP_MIN_WIDTH, config.APP_MIN_HEIGHT)
        self.configure(bg=config.OUTER_BG)

        self.accent_widgets: list[PillButton | ColorModeSwitch] = []
        self.agent_listbox: tk.Listbox | None = None
        self.field_widgets: list[RoundedEntry] = []
        self.launch_button: PillButton | None = None
        self.palette_window: tk.Toplevel | None = None
        self.shell_panel: RoundedPanel | None = None

        self.backend_path = tk.StringVar(value=self.state.backend_path)
        self.frontend_path = tk.StringVar(value=self.state.frontend_path)
        self.agent_project_root = tk.StringVar(value=self.state.agent_project_root)
        self.backend_command = tk.StringVar(value=self.state.backend_command)
        self.frontend_command = tk.StringVar(value=self.state.frontend_command)
        self.status_text = tk.StringVar(value=self.state.status_text)

        self._build_ui()
        self.render()

    # Compose the main sections from small builders.
    def _build_ui(self) -> None:
        mount_ui_tree(self, self._frontend_tree())

    # Recreate theme-dependent widgets after day/night changes.
    def _rebuild_ui(self) -> None:
        self._close_palette()
        if self.shell_panel is not None:
            self.shell_panel.destroy()
            self.shell_panel = None
        self.configure(bg=config.OUTER_BG)
        self.accent_widgets = []
        self.agent_listbox = None
        self.field_widgets = []
        self.launch_button = None
        self._build_ui()

    def dispatch(self, action: Action) -> None:
        result = self.controller.dispatch(action)
        self._apply_result(result)

    def _apply_result(self, result: ControllerResult) -> None:
        self.state = result.state
        if result.close_palette:
            self._close_palette()
        if result.rebuild_ui:
            self._rebuild_ui()
        self.render()
        if result.dialog is not None:
            messagebox.showerror(result.dialog.title, result.dialog.message)

    def render(self) -> None:
        self.status_text.set(self.state.status_text)
        self._render_accent_color()
        self._render_terminal_state()

    # Root UI tree: shell, header, cards, and footer.
    def _frontend_tree(self) -> UINode:
        return UINode(
            create=lambda parent: RoundedPanel(
                parent,
                fill=config.SCREEN_BG,
                parent_bg=config.OUTER_BG,
                radius=config.scaled_px(28),
                padding=config.scaled_px(24),
                shadow=False,
            ),
            layout="pack",
            layout_options={
                "fill": "both",
                "expand": True,
                "padx": config.scaled_px(8),
                "pady": config.scaled_px(8),
            },
            child_parent=rounded_panel_content,
            after_create=self._store_shell_panel,
            children=[
                self._header_tree(),
                *self._workspace_card_trees(),
                self._footer_tree(),
            ],
        )

    # Keep a reference to the shell so it can be rebuilt on theme changes.
    def _store_shell_panel(self, widget: tk.Widget) -> None:
        if isinstance(widget, RoundedPanel):
            self.shell_panel = widget

    # Header tree with brand, controls, copy, and accent rule.
    def _header_tree(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Frame(parent, bg=config.SCREEN_BG),
            layout="pack",
            layout_options={"fill": "x", "pady": (0, config.scaled_px(18))},
            column_weights={1: 1},
            children=[
                self._brand_node(),
                self._header_controls_tree(),
                self._header_title_node(),
                self._header_subtitle_node(),
                self._accent_rule_node(),
            ],
        )

    # Small brand label shown in the header.
    def _brand_node(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Label(
                parent,
                text="terminal studio",
                bg=config.SCREEN_BG,
                fg=config.TEXT_SECONDARY,
                font=("Segoe UI", config.scaled_font(9), "bold"),
            ),
            layout="grid",
            layout_options={"row": 0, "column": 0, "sticky": "w"},
        )

    # Right-side header controls for mode and appearance.
    def _header_controls_tree(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Frame(parent, bg=config.SCREEN_BG),
            layout="grid",
            layout_options={"row": 0, "column": 2, "sticky": "e"},
            children=[
                self._color_mode_switch_node(),
                self._customize_button_node(),
            ],
        )

    # Day/night mode switch node.
    def _color_mode_switch_node(self) -> UINode:
        return UINode(
            create=lambda parent: ColorModeSwitch(
                parent,
                mode=self.state.color_mode,
                command=self.toggle_color_mode,
                accent=self.state.accent_color,
                width=config.scaled_px(118),
                height=config.scaled_px(34),
                parent_bg=config.SCREEN_BG,
            ),
            layout="pack",
            layout_options={"side": "left", "padx": (0, config.scaled_px(10))},
            after_create=self._register_accent_widget,
        )

    # Appearance palette button node.
    def _customize_button_node(self) -> UINode:
        return UINode(
            create=lambda parent: PillButton(
                parent,
                text="Customize appearance",
                command=self.open_appearance_menu,
                accent=self.state.accent_color,
                variant="outline",
                width=config.scaled_px(220),
                height=config.scaled_px(34),
                parent_bg=config.SCREEN_BG,
            ),
            layout="pack",
            layout_options={"side": "left"},
            after_create=self._register_accent_widget,
        )

    # Track widgets that need accent-color updates.
    def _register_accent_widget(self, widget: tk.Widget) -> None:
        if isinstance(widget, (PillButton, ColorModeSwitch)):
            self.accent_widgets.append(widget)

    # Track rounded fields that need focus-ring recoloring.
    def _register_field_widget(self, widget: tk.Widget) -> None:
        if isinstance(widget, RoundedEntry):
            self.field_widgets.append(widget)

    # Main title node for the launcher.
    def _header_title_node(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Label(
                parent,
                text="Launch Workspace",
                bg=config.SCREEN_BG,
                fg=config.TEXT_PRIMARY,
                font=("Segoe UI", config.scaled_font(26), "bold"),
            ),
            layout="grid",
            layout_options={
                "row": 1,
                "column": 0,
                "columnspan": 2,
                "sticky": "w",
                "pady": (config.scaled_px(10), 0),
            },
        )

    # Subtitle node below the main title.
    def _header_subtitle_node(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Label(
                parent,
                text="Two named PowerShell tabs. One path and one command per workspace.",
                bg=config.SCREEN_BG,
                fg=config.TEXT_SECONDARY,
                font=("Segoe UI", config.scaled_font(10)),
            ),
            layout="grid",
            layout_options={
                "row": 2,
                "column": 0,
                "columnspan": 3,
                "sticky": "w",
                "pady": (config.scaled_px(4), 0),
            },
        )

    # Accent rule canvas node.
    def _accent_rule_node(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Canvas(
                parent,
                height=config.scaled_px(4),
                bg=config.SCREEN_BG,
                bd=0,
                highlightthickness=0,
            ),
            layout="grid",
            layout_options={
                "row": 3,
                "column": 0,
                "columnspan": 3,
                "sticky": "ew",
                "pady": (config.scaled_px(16), 0),
            },
            after_create=self._register_accent_rule,
        )

    # Store and draw the accent rule after its canvas exists.
    def _register_accent_rule(self, widget: tk.Widget) -> None:
        if isinstance(widget, tk.Canvas):
            self.accent_rule = widget
            self._draw_accent_rule()

    # Project and agent cards mounted below the header.
    def _workspace_card_trees(self) -> list[UINode]:
        return [
            self._project_card_tree(config.BACKEND_TAB_TITLE, self.backend_path, self.backend_command),
            self._project_card_tree(config.FRONTEND_TAB_TITLE, self.frontend_path, self.frontend_command),
            self._agent_card_tree(),
        ]

    # Footer tree containing status text and launch/end button.
    def _footer_tree(self) -> UINode:
        return UINode(
            create=lambda parent: tk.Frame(parent, bg=config.SCREEN_BG),
            layout="pack",
            layout_options={"fill": "x", "pady": (config.scaled_px(8), 0)},
            column_weights={0: 1},
            children=[
                UINode(
                    create=lambda parent: tk.Label(
                        parent,
                        textvariable=self.status_text,
                        bg=config.SCREEN_BG,
                        fg=config.TEXT_SECONDARY,
                        font=("Segoe UI", config.scaled_font(10)),
                    ),
                    layout="grid",
                    layout_options={"row": 0, "column": 0, "sticky": "w"},
                ),
                UINode(
                    create=lambda parent: PillButton(
                        parent,
                        text=config.LAUNCH_BUTTON_TEXT,
                        command=self.toggle_terminals,
                        accent=self.state.accent_color,
                        variant="accent",
                        width=config.scaled_px(190),
                        height=config.scaled_px(44),
                        parent_bg=config.SCREEN_BG,
                    ),
                    layout="grid",
                    layout_options={"row": 0, "column": 1, "sticky": "e"},
                    after_create=self._store_launch_button,
                ),
            ],
        )

    # Keep a reference to the launch button for state changes.
    def _store_launch_button(self, widget: tk.Widget) -> None:
        if isinstance(widget, PillButton):
            self.launch_button = widget

    # Bind resize once, then draw the initial accent rule.
    def _draw_accent_rule(self) -> None:
        self.accent_rule.delete("all")
        self.accent_rule.bind(
            "<Configure>",
            lambda event: self._redraw_accent_rule(event.width),
        )
        self._redraw_accent_rule(self.accent_rule.winfo_width())

    # Keep the rule short and proportional to the header width.
    def _redraw_accent_rule(self, width: int) -> None:
        self.accent_rule.delete("all")
        draw_rounded_rect(
            self.accent_rule,
            0,
            0,
            max(config.scaled_px(80), width // 3),
            config.scaled_px(4),
            config.scaled_px(2),
            fill=self.state.accent_color,
            outline="",
        )

    # Build a backend or frontend command card.
    def _project_card_tree(
        self,
        title: str,
        path_variable: tk.StringVar,
        command_variable: tk.StringVar,
    ) -> UINode:
        return self._card_tree(
            config.CARD_HEIGHT,
            [
                *self._card_header_nodes(title, "PowerShell tab"),
                *self._form_row_nodes(1, "Path", path_variable, browse=True),
                *self._form_row_nodes(2, "Enter command:", command_variable, browse=False),
            ],
        )

    # Build the interactive agent launcher card.
    def _agent_card_tree(self) -> UINode:
        return self._card_tree(
            config.AGENT_CARD_HEIGHT,
            [
                *self._card_header_nodes("Agent", "Interactive terminal"),
                *self._form_row_nodes(1, "Project root", self.agent_project_root, browse=True),
                *self._agent_selector_nodes(),
            ],
        )

    # Shared rounded card wrapper used by workspace and agent cards.
    def _card_tree(self, height: int, children: list[UINode]) -> UINode:
        return UINode(
            create=lambda parent: RoundedPanel(
                parent,
                fill=config.CARD_BG,
                parent_bg=config.SCREEN_BG,
                radius=config.scaled_px(24),
                padding=config.scaled_px(18),
                height=height,
                shadow=True,
            ),
            layout="pack",
            layout_options={"fill": "x", "pady": (0, config.scaled_px(14))},
            child_parent=rounded_panel_content,
            after_create=self._configure_card_content,
            children=children,
        )

    # Give card content rows a stretchy field column.
    def _configure_card_content(self, widget: tk.Widget) -> None:
        if isinstance(widget, RoundedPanel):
            widget.content.columnconfigure(1, weight=1)

    # Header nodes used inside each card.
    def _card_header_nodes(self, title: str, tag: str) -> list[UINode]:
        return [
            UINode(
                create=lambda parent: tk.Label(
                    parent,
                    text=title,
                    bg=config.CARD_BG,
                    fg=config.TEXT_PRIMARY,
                    font=("Segoe UI", config.scaled_font(14), "bold"),
                ),
                layout="grid",
                layout_options={
                    "row": 0,
                    "column": 0,
                    "sticky": "w",
                    "pady": (0, config.scaled_px(12)),
                },
            ),
            UINode(
                create=lambda parent: tk.Label(
                    parent,
                    text=tag,
                    bg=config.CARD_BG,
                    fg=config.TEXT_SECONDARY,
                    font=("Segoe UI", config.scaled_font(9)),
                ),
                layout="grid",
                layout_options={
                    "row": 0,
                    "column": 1,
                    "columnspan": 2,
                    "sticky": "e",
                    "pady": (0, config.scaled_px(12)),
                },
            ),
        ]

    # Build a labeled path or command row.
    def _form_row_nodes(
        self,
        row: int,
        label_text: str,
        variable: tk.StringVar,
        *,
        browse: bool,
    ) -> list[UINode]:
        action_node = self._browse_button_node(row, variable) if browse else self._row_spacer_node(row)
        return [
            UINode(
                create=lambda parent: tk.Label(
                    parent,
                    text=label_text,
                    bg=config.CARD_BG,
                    fg=config.TEXT_SECONDARY,
                    font=("Segoe UI", config.scaled_font(10), "bold"),
                    width=15,
                    anchor="w",
                ),
                layout="grid",
                layout_options={"row": row, "column": 0, "sticky": "w", "pady": config.scaled_px(4)},
            ),
            UINode(
                create=lambda parent: RoundedEntry(parent, variable=variable, accent=self.state.accent_color),
                layout="grid",
                layout_options={
                    "row": row,
                    "column": 1,
                    "sticky": "ew",
                    "padx": (config.scaled_px(8), config.scaled_px(10)),
                    "pady": config.scaled_px(4),
                },
                after_create=self._register_field_widget,
            ),
            action_node,
        ]

    # Browse button node for folder-selection rows.
    def _browse_button_node(self, row: int, variable: tk.StringVar) -> UINode:
        return UINode(
            create=lambda parent: PillButton(
                parent,
                text="Browse",
                command=lambda: self.choose_folder(variable),
                accent=self.state.accent_color,
                variant="accent",
                width=config.scaled_px(102),
                height=config.scaled_px(38),
                parent_bg=config.CARD_BG,
            ),
            layout="grid",
            layout_options={"row": row, "column": 2, "sticky": "e", "pady": config.scaled_px(4)},
            after_create=self._register_accent_widget,
        )

    # Placeholder that keeps command rows aligned with browse rows.
    def _row_spacer_node(self, row: int) -> UINode:
        return UINode(
            create=lambda parent: tk.Frame(
                parent,
                bg=config.CARD_BG,
                width=config.scaled_px(102),
                height=config.scaled_px(38),
            ),
            layout="grid",
            layout_options={"row": row, "column": 2, "sticky": "e", "pady": config.scaled_px(4)},
        )

    # Agent list and launch button nodes.
    def _agent_selector_nodes(self) -> list[UINode]:
        return [
            UINode(
                create=lambda parent: tk.Label(
                    parent,
                    text="Agent",
                    bg=config.CARD_BG,
                    fg=config.TEXT_SECONDARY,
                    font=("Segoe UI", config.scaled_font(10), "bold"),
                    width=15,
                    anchor="w",
                ),
                layout="grid",
                layout_options={"row": 2, "column": 0, "sticky": "nw", "pady": config.scaled_px(4)},
            ),
            UINode(
                create=lambda parent: tk.Listbox(
                    parent,
                    height=2,
                    activestyle="none",
                    bg=config.FIELD_BG,
                    fg=config.TEXT_PRIMARY,
                    selectbackground=self.state.accent_color,
                    selectforeground=contrast_text_color(self.state.accent_color),
                    relief="flat",
                    borderwidth=0,
                    highlightthickness=1,
                    highlightbackground=config.FIELD_BORDER,
                    highlightcolor=self.state.accent_color,
                    exportselection=False,
                    selectmode=tk.SINGLE,
                    font=("Segoe UI", config.scaled_font(10)),
                ),
                layout="grid",
                layout_options={
                    "row": 2,
                    "column": 1,
                    "sticky": "ew",
                    "padx": (config.scaled_px(8), config.scaled_px(10)),
                    "pady": config.scaled_px(4),
                },
                after_create=self._store_agent_listbox,
            ),
            UINode(
                create=lambda parent: PillButton(
                    parent,
                    text="Launch Agent",
                    command=self.launch_selected_agent,
                    accent=self.state.accent_color,
                    variant="accent",
                    width=config.scaled_px(132),
                    height=config.scaled_px(42),
                    parent_bg=config.CARD_BG,
                ),
                layout="grid",
                layout_options={"row": 2, "column": 2, "sticky": "ne", "pady": config.scaled_px(4)},
                after_create=self._register_accent_widget,
            ),
        ]

    # Fill and store the agent listbox after Tk creates it.
    def _store_agent_listbox(self, widget: tk.Widget) -> None:
        if not isinstance(widget, tk.Listbox):
            return
        for agent_name in config.AGENT_COMMANDS:
            widget.insert(tk.END, agent_name)
        widget.selection_set(0)
        self.agent_listbox = widget

    # Open a custom palette instead of the native color picker.
    def open_appearance_menu(self) -> None:
        self._close_palette()
        palette = tk.Toplevel(self)
        self.palette_window = palette
        palette.title("Customize appearance")
        set_window_icon(palette)
        palette.configure(bg=config.CARD_BG)
        palette.resizable(False, False)
        palette.protocol("WM_DELETE_WINDOW", self._close_palette)
        self._position_palette(palette)
        mount_ui_tree(palette, self._palette_tree(palette))

    # Close any open appearance palette before rebuilding or reopening it.
    def _close_palette(self) -> None:
        if self.palette_window is None:
            return
        try:
            if self.palette_window.winfo_exists():
                self.palette_window.destroy()
        finally:
            self.palette_window = None

    # Place the palette near the top-right customize button.
    def _position_palette(self, palette: tk.Toplevel) -> None:
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - config.scaled_px(330)
        y = self.winfo_rooty() + config.scaled_px(92)
        palette.geometry(f"{config.scaled_px(280)}x{config.scaled_px(168)}+{x}+{y}")

    # Palette content tree for choosing an accent color.
    def _palette_tree(self, palette: tk.Toplevel) -> UINode:
        return UINode(
            create=lambda parent: tk.Frame(
                parent,
                bg=config.CARD_BG,
                padx=config.scaled_px(16),
                pady=config.scaled_px(14),
            ),
            layout="pack",
            layout_options={"fill": "both", "expand": True},
            children=[
                UINode(
                    create=lambda parent: tk.Label(
                        parent,
                        text="Main color",
                        bg=config.CARD_BG,
                        fg=config.TEXT_PRIMARY,
                        font=("Segoe UI", config.scaled_font(11), "bold"),
                    ),
                    layout="grid",
                    layout_options={
                        "row": 0,
                        "column": 0,
                        "columnspan": 5,
                        "sticky": "w",
                        "pady": (0, config.scaled_px(12)),
                    },
                ),
                *self._palette_swatch_nodes(palette),
            ],
        )

    # Create one swatch node per fixed accent color.
    def _palette_swatch_nodes(self, palette: tk.Toplevel) -> list[UINode]:
        return [
            self._palette_swatch_node(index, color, palette)
            for index, color in enumerate(config.ACCENT_COLORS)
        ]

    # Build a single clickable color swatch node.
    def _palette_swatch_node(
        self,
        index: int,
        color: str,
        palette: tk.Toplevel,
    ) -> UINode:
        swatch_size = config.scaled_px(34)
        return UINode(
            create=lambda parent: tk.Canvas(
                parent,
                width=swatch_size,
                height=swatch_size,
                bg=config.CARD_BG,
                bd=0,
                highlightthickness=0,
            ),
            layout="grid",
            layout_options={
                "row": 1 + index // 5,
                "column": index % 5,
                "padx": config.scaled_px(5),
                "pady": config.scaled_px(5),
            },
            after_create=lambda widget, swatch_color=color: self._configure_palette_swatch(
                widget,
                palette,
                swatch_color,
            ),
        )

    # Draw the rounded swatch and bind its click handler.
    def _configure_palette_swatch(
        self,
        widget: tk.Widget,
        palette: tk.Toplevel,
        color: str,
    ) -> None:
        if not isinstance(widget, tk.Canvas):
            return

        swatch_size = config.scaled_px(34)
        outline = config.TEXT_PRIMARY if color == self.state.accent_color else config.CARD_BG
        draw_rounded_rect(
            widget,
            1,
            1,
            swatch_size - 1,
            swatch_size - 1,
            swatch_size // 2,
            fill=color,
            outline=outline,
        )
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda _event: self._select_palette_color(color, palette))

    # Selecting a swatch updates the whole app then closes the popup.
    def _select_palette_color(self, color: str, palette: tk.Toplevel) -> None:
        self.dispatch(SelectAccentColor(color))

    # Emit a theme-toggle action; the controller decides the next mode.
    def toggle_color_mode(self) -> None:
        self.dispatch(ToggleColorMode())

    # Recolor accent-aware widgets from the current app state.
    def _render_accent_color(self) -> None:
        for widget in self.accent_widgets:
            widget.set_accent(self.state.accent_color)
        if self.agent_listbox is not None:
            self.agent_listbox.configure(
                selectbackground=self.state.accent_color,
                selectforeground=contrast_text_color(self.state.accent_color),
                highlightcolor=self.state.accent_color,
            )
        for field in self.field_widgets:
            field.set_accent(self.state.accent_color)
        if self.launch_button is not None and not self.state.terminals_running:
            self.launch_button.set_accent(self.state.accent_color)
        self._redraw_accent_rule(self.accent_rule.winfo_width())

    # Folder picker writes directly into the field variable it belongs to.
    def choose_folder(self, variable: tk.StringVar) -> None:
        selected = filedialog.askdirectory(initialdir=variable.get() or str(config.ROOT_DIR))
        if selected:
            variable.set(selected)
            self.save_current_paths()

    # Persist the current path fields through the controller.
    def save_current_paths(self) -> None:
        self.dispatch(
            SaveCurrentPaths(
                backend_path=self.backend_path.get(),
                frontend_path=self.frontend_path.get(),
                agent_project_root=self.agent_project_root.get(),
            )
        )

    # Read the selected agent name from the listbox.
    def get_selected_agent_name(self) -> str | None:
        if self.agent_listbox is None:
            return None
        selection = self.agent_listbox.curselection()
        if not selection:
            return None
        agent_name = self.agent_listbox.get(selection[0])
        return agent_name if agent_name in config.AGENT_COMMANDS else None

    # Emit the selected-agent launch intent.
    def launch_selected_agent(self) -> None:
        self.dispatch(
            LaunchSelectedAgent(
                agent_name=self.get_selected_agent_name(),
                project_root=self.agent_project_root.get(),
            )
        )

    # Emit the launch/end intent with a snapshot of current form input.
    def toggle_terminals(self) -> None:
        self.dispatch(
            ToggleTerminals(
                backend_path=self.backend_path.get(),
                frontend_path=self.frontend_path.get(),
                backend_command=self.backend_command.get(),
                frontend_command=self.frontend_command.get(),
            )
        )

    # Render the launch button from the current terminal state.
    def _render_terminal_state(self) -> None:
        if self.launch_button is None:
            return
        self.launch_button.set_text(
            config.END_BUTTON_TEXT if self.state.terminals_running else config.LAUNCH_BUTTON_TEXT
        )
        self.launch_button.set_accent(
            config.END_ACCENT if self.state.terminals_running else self.state.accent_color
        )
