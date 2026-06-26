from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field

from .ui_widgets import RoundedPanel


@dataclass
class UINode:
    """Declarative node used to build Tk widgets as a small UI tree."""

    create: Callable[[tk.Widget], tk.Widget]
    layout: str | None = None
    layout_options: dict[str, object] = field(default_factory=dict)
    column_weights: dict[int, int] = field(default_factory=dict)
    row_weights: dict[int, int] = field(default_factory=dict)
    children: list["UINode"] = field(default_factory=list)
    child_parent: Callable[[tk.Widget], tk.Widget] | None = None
    after_create: Callable[[tk.Widget], None] | None = None


# Build one UI node, apply its layout, then mount its children.
def mount_ui_tree(parent: tk.Widget, node: UINode) -> tk.Widget:
    widget = node.create(parent)

    if node.layout == "pack":
        widget.pack(**node.layout_options)
    elif node.layout == "grid":
        widget.grid(**node.layout_options)
    elif node.layout is not None:
        raise ValueError(f"Unsupported UI layout: {node.layout}")

    for column, weight in node.column_weights.items():
        widget.columnconfigure(column, weight=weight)
    for row, weight in node.row_weights.items():
        widget.rowconfigure(row, weight=weight)

    if node.after_create is not None:
        node.after_create(widget)

    child_parent = node.child_parent(widget) if node.child_parent is not None else widget
    for child in node.children:
        mount_ui_tree(child_parent, child)

    return widget


# Return the content frame inside a rounded panel node.
def rounded_panel_content(widget: tk.Widget) -> tk.Widget:
    if not isinstance(widget, RoundedPanel):
        raise TypeError("RoundedPanel content can only be read from RoundedPanel widgets.")
    return widget.content
