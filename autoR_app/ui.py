from __future__ import annotations

import string
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .db import GridSize

GRID_INDEX_LABELS: list[str] = [
    "STT",
    "NVL",
    "bill",
    "Invoice",
]

GRID_LABELS: list[str] = [
    "Loại hàng",
    "Tiến độ",
    "Phân loại",
    "Ngày",
    "Số TK",
    "Luồng",
    "Loại TK",
    "TERM",
    "TMS",
    "Giờ nhận Mail",
    "Giờ TMS",
    "Giờ gửi nháp",
    "Giờ xác nhận TK",
    "Giờ truyền chính thức",
    "Giờ mail thông quan",
]

# Default pinned (frozen) columns, in the order they should appear.
GRID_FROZEN_LABELS: list[str] = GRID_INDEX_LABELS.copy()

# Full logical column order in the grid.
GRID_ALL_LABELS: list[str] = GRID_INDEX_LABELS + GRID_LABELS


def col_name(idx: int) -> str:
    # 0 -> A, 25 -> Z, 26 -> AA ...
    letters = string.ascii_uppercase
    n = idx
    out = ""
    while True:
        n, rem = divmod(n, 26)
        out = letters[rem] + out
        if n == 0:
            break
        n -= 1
    return out


class GridFrame(ttk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        size: GridSize,
        get_value: Callable[[int, int], str],
        set_value: Callable[[int, int, str], None],
        on_row_action: Callable[[str, int], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._size = size
        self._get_value = get_value
        self._set_value = set_value
        self._on_row_action = on_row_action
        self._actions_key = "__actions__"

        self._time_col_start = self._find_time_col_start()
        self._time_col_vars: list[tk.BooleanVar] = []
        self._col_vis_vars: list[tk.BooleanVar] = []

        self._columns = [self._actions_key] + [col_name(c) for c in range(size.cols)]
        self._progress_col_idx = self._find_col_idx("Tiến độ")
        self._frozen_data_idxs = [i for i in (self._find_col_idx(l) for l in GRID_FROZEN_LABELS) if i >= 0]
        self._nvl_idx = self._find_col_idx("NVL")

        topbar = ttk.Frame(self)
        topbar.pack(side="top", fill="x")

        self._cols_btn = ttk.Menubutton(topbar, text="Columns")
        self._cols_btn.pack(side="left", padx=6, pady=4)
        self._cols_menu = tk.Menu(self._cols_btn, tearoff=False)
        self._cols_btn.configure(menu=self._cols_menu)

        table = ttk.Frame(self)
        table.pack(side="top", fill="both", expand=True)

        style = ttk.Style(self)
        style.configure("Grid.Treeview", borderwidth=1, relief="solid", rowheight=22)
        style.configure("Grid.Treeview.Heading", borderwidth=1, relief="raised")

        # Frozen-left tree: actions + chosen business columns (sticky when horizontal scrolling).
        self._frozen_columns = [self._actions_key]
        for idx in self._frozen_data_idxs:
            col_id = self._columns[idx + 1]
            if col_id not in self._frozen_columns:
                self._frozen_columns.append(col_id)
        self._main_columns = [c for c in self._columns if c not in set(self._frozen_columns)]

        frozen_wrap = ttk.Frame(table)
        frozen_wrap.grid(row=0, column=0, sticky="nsew")
        main_wrap = ttk.Frame(table)
        main_wrap.grid(row=0, column=1, sticky="nsew")

        self._tree_frozen = ttk.Treeview(
            frozen_wrap,
            columns=self._frozen_columns,
            show="headings",
            selectmode="browse",
            style="Grid.Treeview",
        )
        self._tree_frozen.bind("<ButtonRelease-1>", self._copy_cell)
        self._tree_main = ttk.Treeview(
            main_wrap,
            columns=self._main_columns,
            show="headings",
            selectmode="browse",
            style="Grid.Treeview",
        )
        self._tree_main.bind("<ButtonRelease-1>", self._copy_cell)
        self._tree_frozen.grid(row=0, column=0, sticky="nsew")
        self._tree_main.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(table, orient="vertical", command=self._yview_both)
        hsb = ttk.Scrollbar(table, orient="horizontal", command=self._tree_main.xview)
        self._tree_frozen.configure(yscrollcommand=vsb.set)
        self._tree_main.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.grid(row=0, column=2, sticky="ns")
        hsb.grid(row=1, column=1, sticky="ew")

        # Windows and macOS scrolled by mouse wheel without Ctrl, Linux usually requires Shift for horizontal scroll and no modifier for vertical scroll.
        self._tree_main.bind("<MouseWheel>", self._on_mousewheel)
        self._tree_frozen.bind("<MouseWheel>", self._on_mousewheel)

        # Linux scroll events
        self._tree_main.bind("<Button-4>", self._on_mousewheel)
        self._tree_main.bind("<Button-5>", self._on_mousewheel)
        self._tree_frozen.bind("<Button-4>", self._on_mousewheel)
        self._tree_frozen.bind("<Button-5>", self._on_mousewheel)

        frozen_wrap.rowconfigure(0, weight=1)
        frozen_wrap.columnconfigure(0, weight=1)
        main_wrap.rowconfigure(0, weight=1)
        main_wrap.columnconfigure(0, weight=1)

        table.rowconfigure(0, weight=1)
        table.columnconfigure(0, weight=0)
        table.columnconfigure(1, weight=1)

        # ttk.Treeview doesn't support true gridlines; use alternating row colors
        # to visually separate rows.
        for t in (self._tree_frozen, self._tree_main):
            t.tag_configure("even", background="#ffffff")
            t.tag_configure("odd", background="#f6f6f6")
            t.bind("<Double-1>", self._on_double_click)
            t.bind("<Return>", self._on_enter)
            t.bind("<F2>", self._on_enter)
            t.bind("<Button-1>", self._on_click)
            t.bind("<<TreeviewSelect>>", self._on_select)

        self._editor: tk.Entry | None = None
        self._combo_editor: ttk.Combobox | None = None
        self._editor_info: tuple[str, str, int, int] | None = None  # (item, col_id, r, c)

        self._init_columns()
        self._init_column_menu()
        self._init_rows()
        self._syncing_selection = False  # guard flag

    def _yview_both(self, *args):
        # args examples:
        # ("scroll", 1, "units")
        # ("scroll", -3, "units")
        # ("moveto", "0.42")

        if args[0] == "scroll":
            count = int(args[1])
            what = args[2]

            # convert unit scroll to pixel scroll
            if what == "units":
                self._tree_main.yview_scroll(count, "pixels")
                self._tree_frozen.yview_scroll(count, "pixels")
            else:
                # pages or anything else
                self._tree_main.yview_scroll(count, what)
                self._tree_frozen.yview_scroll(count, what)

        elif args[0] == "moveto":
            fraction = args[1]
            self._tree_main.yview_moveto(fraction)
            self._tree_frozen.yview_moveto(fraction)

    def _on_select(self, evt: tk.Event) -> None:
        if self._syncing_selection:
            return  # ignore recursive calls

        tree = evt.widget
        if tree not in (self._tree_frozen, self._tree_main):
            return
        other = self._tree_main if tree is self._tree_frozen else self._tree_frozen
        sel = tree.selection()
        try:
            self._syncing_selection = True  # start guard

            # Only update if different (avoids unnecessary events)
            if other.selection() != sel:
                other.selection_set(sel)

            if sel:
                other.focus(sel[0])

        finally:
            self._syncing_selection = False  # always release

    def _find_time_col_start(self) -> int:
        try:
            return GRID_ALL_LABELS.index("Giờ nhận Mail")
        except ValueError:
            return -1

    def _find_col_idx(self, label: str) -> int:
        try:
            return GRID_ALL_LABELS.index(label)
        except ValueError:
            return -1

    def _init_columns(self) -> None:
        self._tree_frozen.heading(self._actions_key, text="⋯")
        self._tree_frozen.column(self._actions_key, width=44, minwidth=44, stretch=False, anchor="center")

        for idx in self._frozen_data_idxs:
            col_id = self._columns[idx + 1]
            label = GRID_ALL_LABELS[idx] if idx < len(GRID_ALL_LABELS) else col_id
            self._tree_frozen.heading(col_id, text=label)
            if label == "STT":
                self._tree_frozen.column(col_id, width=60, minwidth=50, stretch=False, anchor="center")
            elif label == "NVL":
                self._tree_frozen.column(col_id, width=180, minwidth=120, stretch=False, anchor="w")
            else:
                self._tree_frozen.column(col_id, width=120, minwidth=80, stretch=False, anchor="w")

        for c in range(self._size.cols):
            col_id = self._columns[c + 1]
            if col_id in self._frozen_columns:
                continue
            label = GRID_ALL_LABELS[c] if c < len(GRID_ALL_LABELS) else col_id
            self._tree_main.heading(col_id, text=label)
            self._tree_main.column(col_id, width=120, minwidth=60, stretch=True, anchor="w")

    def _init_column_menu(self) -> None:
        self._cols_menu.delete(0, "end")
        self._time_col_vars.clear()
        self._col_vis_vars.clear()

        # Global show/hide (NVL is always visible)
        self._cols_menu.add_command(label="Show all columns", command=self._show_all_columns)
        self._cols_menu.add_command(label="Hide all (except NVL)", command=self._hide_all_except_nvl)
        self._cols_menu.add_separator()

        nvl_entry_index: int | None = None
        for c in range(self._size.cols):
            label = GRID_ALL_LABELS[c] if c < len(GRID_ALL_LABELS) else self._columns[c + 1]
            is_nvl = c == self._nvl_idx
            var = tk.BooleanVar(value=True)
            self._col_vis_vars.append(var)
            self._cols_menu.add_checkbutton(
                label=f"Show: {label}",
                variable=var,
                command=self._apply_column_visibility,
            )
            if is_nvl:
                nvl_entry_index = self._cols_menu.index("end")

        if nvl_entry_index is not None:
            # NVL must stay visible
            self._col_vis_vars[self._nvl_idx].set(True)
            self._cols_menu.entryconfigure(nvl_entry_index, state="disabled")

        self._cols_menu.add_separator()

        if self._time_col_start < 0 or self._time_col_start >= self._size.cols:
            self._cols_btn.state(["disabled"])
            self._apply_column_visibility()
            return

        self._cols_btn.state(["!disabled"])
        self._cols_menu.add_command(label="Show all time columns", command=self._show_all_time_columns)
        self._cols_menu.add_command(label="Hide all time columns", command=self._hide_all_time_columns)
        self._cols_menu.add_separator()

        for c in range(self._time_col_start, self._size.cols):
            col_id = self._columns[c + 1]
            label = GRID_ALL_LABELS[c] if c < len(GRID_ALL_LABELS) else col_id
            var = tk.BooleanVar(value=True)
            self._time_col_vars.append(var)
            self._cols_menu.add_checkbutton(
                label=label,
                variable=var,
                command=self._apply_column_visibility,
            )

        self._apply_column_visibility()

    def _show_all_columns(self) -> None:
        for i, v in enumerate(self._col_vis_vars):
            if i == self._nvl_idx:
                v.set(True)
            else:
                v.set(True)
        self._apply_column_visibility()

    def _hide_all_except_nvl(self) -> None:
        for i, v in enumerate(self._col_vis_vars):
            v.set(i == self._nvl_idx)
        self._apply_column_visibility()

    def _apply_column_visibility(self) -> None:
        # Frozen tree (pinned columns) visibility
        frozen_display: list[str] = [self._actions_key]
        for idx in self._frozen_data_idxs:
            if 0 <= idx < len(self._col_vis_vars) and self._col_vis_vars[idx].get():
                frozen_display.append(self._columns[idx + 1])
        self._tree_frozen.configure(displaycolumns=frozen_display)

        # Main (scrollable) tree visibility
        display: list[str] = []
        for c in range(self._size.cols):
            col_id = self._columns[c + 1]
            if col_id in self._frozen_columns:
                continue
            if 0 <= c < len(self._col_vis_vars) and not self._col_vis_vars[c].get():
                continue
            if c < self._time_col_start:
                display.append(col_id)
                continue
            idx = c - self._time_col_start
            if 0 <= idx < len(self._time_col_vars) and self._time_col_vars[idx].get():
                display.append(col_id)
        self._tree_main.configure(displaycolumns=display)

    def _show_all_time_columns(self) -> None:
        for v in self._time_col_vars:
            v.set(True)
        self._apply_column_visibility()

    def _hide_all_time_columns(self) -> None:
        for v in self._time_col_vars:
            v.set(False)
        self._apply_column_visibility()

    def _init_rows(self) -> None:
        for r in range(self._size.rows):
            tag = "even" if (r % 2) == 0 else "odd"
            frozen_vals = ["⋯"] + [self._get_value(r, c) for c in self._frozen_data_idxs]

            main_vals: list[str] = []
            for c in range(self._size.cols):
                col_id = self._columns[c + 1]
                if col_id in self._frozen_columns:
                    continue
                main_vals.append(self._get_value(r, c))

            self._tree_frozen.insert("", "end", iid=str(r), values=frozen_vals, tags=(tag,))
            self._tree_main.insert("", "end", iid=str(r), values=main_vals, tags=(tag,))

    def refresh_all(self) -> None:
        for r in range(self._size.rows):
            tag = "even" if (r % 2) == 0 else "odd"
            frozen_vals = ["⋯"] + [self._get_value(r, c) for c in self._frozen_data_idxs]

            main_vals: list[str] = []
            for c in range(self._size.cols):
                col_id = self._columns[c + 1]
                if col_id in self._frozen_columns:
                    continue
                main_vals.append(self._get_value(r, c))

            self._tree_frozen.item(str(r), values=frozen_vals, tags=(tag,))
            self._tree_main.item(str(r), values=main_vals, tags=(tag,))

    def rebuild(self, size: GridSize) -> None:
        self._end_edit(commit=True)
        cols_changed = size.cols != self._size.cols
        self._size = size
        if cols_changed:
            self._columns = [self._actions_key] + [col_name(c) for c in range(size.cols)]
            # self._progress_col_idx = self._find_col_idx("Tiến độ")
            self._frozen_data_idxs = [i for i in (self._find_col_idx(l) for l in GRID_FROZEN_LABELS) if i >= 0]
            self._frozen_columns = [self._actions_key]
            for idx in self._frozen_data_idxs:
                col_id = self._columns[idx + 1]
                if col_id not in self._frozen_columns:
                    self._frozen_columns.append(col_id)
            self._main_columns = [c for c in self._columns if c not in set(self._frozen_columns)]

            self._tree_frozen.configure(columns=self._frozen_columns)
            self._tree_main.configure(columns=self._main_columns)
            self._init_columns()
            self._init_column_menu()
        for child in self._tree_frozen.get_children():
            self._tree_frozen.delete(child)
        for child in self._tree_main.get_children():
            self._tree_main.delete(child)
        self._init_rows()

    def _on_enter(self, _evt: tk.Event) -> None:
        self._begin_edit_at_focus()

    def _on_click(self, evt: tk.Event) -> None:
        tree = evt.widget
        if tree not in (self._tree_frozen, self._tree_main):
            return
        region = tree.identify("region", evt.x, evt.y)
        if region != "cell":
            return
        item = tree.identify_row(evt.y)
        col_id = tree.identify_column(evt.x)
        if not item or not col_id:
            return
        if tree is self._tree_frozen and col_id == "#1":
            self._show_actions(evt.x_root, evt.y_root, int(item))

    def _show_actions(self, x_root: int, y_root: int, row_idx: int) -> None:
        if not self._on_row_action:
            return
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Save", command=lambda: self._on_row_action("save", row_idx))
        menu.add_command(label="Resync", command=lambda: self._on_row_action("resync", row_idx))
        menu.add_separator()
        menu.add_command(label="Add row above", command=lambda: self._on_row_action("add_above", row_idx))
        menu.add_command(label="Add row below", command=lambda: self._on_row_action("add_below", row_idx))
        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def _on_double_click(self, evt: tk.Event) -> None:
        tree = evt.widget
        if tree not in (self._tree_frozen, self._tree_main):
            return
        region = tree.identify("region", evt.x, evt.y)
        if region != "cell":
            return
        self._begin_edit(tree, evt.x, evt.y)

    def _begin_edit_at_focus(self) -> None:
        tree = self._tree_main
        item = tree.focus() or self._tree_frozen.focus()
        if not item:
            return
        col_id = tree.identify_column(tree.winfo_width() // 2)
        if not col_id:
            col_id = "#1"
        bbox = tree.bbox(item, col_id)
        if not bbox:
            col_id = "#1"
            bbox = tree.bbox(item, col_id)
        if not bbox:
            return
        x, y, w, h = bbox
        self._begin_edit(tree, x + 2, y + 2)

    def _begin_edit(self, tree: ttk.Treeview, x: int, y: int) -> None:
        item = tree.identify_row(y)
        col_id = tree.identify_column(x)
        if not item or not col_id:
            return
        bbox = tree.bbox(item, col_id)
        if not bbox:
            return

        r = int(item)
        c = self._data_col_index(tree, col_id)
        if c < 0 or c >= self._size.cols:
            return

        self._end_edit(commit=True)

        x0, y0, w, h = bbox
        value = self._get_value(r, c)

        if c == self._progress_col_idx:
            self._combo_editor = ttk.Combobox(tree, state="readonly", values=["Pending", "Done"])
            self._combo_editor.place(x=x0, y=y0, width=w, height=h)
            self._combo_editor.set(value if value in ("Pending", "Done") else "Pending")
            self._combo_editor.focus_set()
            self._editor_info = (item, col_id, r, c)
            self._combo_editor.bind("<Return>", lambda _e: self._end_edit(commit=True))
            self._combo_editor.bind("<Escape>", lambda _e: self._end_edit(commit=False))
            self._combo_editor.bind("<<ComboboxSelected>>", lambda _e: self._end_edit(commit=True))
            self._combo_editor.bind("<FocusOut>", lambda _e: self._end_edit(commit=True))
            return

        self._editor = tk.Entry(tree)
        self._editor.place(x=x0, y=y0, width=w, height=h)
        self._editor.insert(0, value)
        self._editor.select_range(0, tk.END)
        self._editor.focus_set()
        self._editor_info = (item, col_id, r, c)

        self._editor.bind("<Return>", lambda _e: self._end_edit(commit=True))
        self._editor.bind("<Escape>", lambda _e: self._end_edit(commit=False))
        self._editor.bind("<FocusOut>", lambda _e: self._end_edit(commit=True))

    def _data_col_index(self, tree: ttk.Treeview, col_id: str) -> int:
        if tree is self._tree_frozen:
            # "#1" is actions; "#2" maps to first frozen data col, etc.
            if col_id == "#1":
                return -1
            try:
                pos = int(col_id.lstrip("#")) - 2
            except Exception:
                return -1
            if 0 <= pos < len(self._frozen_data_idxs):
                return self._frozen_data_idxs[pos]
            return -1
        try:
            idx = int(col_id.lstrip("#")) - 1
        except Exception:
            return -1
        display_cols = list(tree.cget("displaycolumns"))
        # Tk returns "#all" when all columns are displayed.
        if not display_cols or display_cols == ["#all"]:
            display_cols = list(tree.cget("columns"))
        if idx < 0 or idx >= len(display_cols):
            return -1
        internal = display_cols[idx]
        try:
            return self._columns.index(internal) - 1
        except ValueError:
            return -1

    def _end_edit(self, commit: bool) -> None:
        if (not self._editor and not self._combo_editor) or not self._editor_info:
            return
        item, col_id, r, c = self._editor_info
        if self._combo_editor:
            new_val = self._combo_editor.get()
            self._combo_editor.destroy()
            self._combo_editor = None
        else:
            assert self._editor is not None
            new_val = self._editor.get()
            self._editor.destroy()
            self._editor = None
        self._editor_info = None

        if commit:
            self._set_value(r, c, new_val)
            if c in self._frozen_data_idxs:
                try:
                    pos = self._frozen_data_idxs.index(c)
                    frozen_col_id = self._frozen_columns[pos + 1]  # +1 skip actions
                    self._tree_frozen.set(item, frozen_col_id, new_val)
                except ValueError:
                    pass

            internal = self._columns[c + 1]
            if internal in self._main_columns:
                # Update by column id (independent of displaycolumns order/hidden cols)
                self._tree_main.set(item, internal, new_val)

    def _copy_cell(self, event):
        tree = event.widget

        if tree not in (self._tree_frozen, self._tree_main):
            return

        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)

        if not row_id or not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1

        # Get values depending on which tree was clicked
        if tree is self._tree_frozen:
            values = self._tree_frozen.item(row_id, "values")
            value = values[col_index] if col_index < len(values) else ""
        else:
            values = self._tree_main.item(row_id, "values")
            value = values[col_index] if col_index < len(values) else ""

        # Copy to clipboard
        tree.clipboard_clear()
        tree.clipboard_append(value)
        tree.update()


    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -20   # tweak for speed
        elif event.num == 5:
            delta = 20
        else:
            delta = int(-event.delta / 120) * 20  # pixel step


        self._tree_main.yview_scroll(delta, "units")
        self._tree_frozen.yview_scroll(delta, "units")
        # self._tree_main.yview_scroll(delta, "pixels")
        # self._tree_frozen.yview_scroll(delta, "pixels")

        return "break"  # prevent default scrolling