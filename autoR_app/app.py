from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import csv
import re
import threading

from .db import GridSize, clear_cells, connect, delete_row, get_cells, get_grid_size, init_db, insert_row, set_cell
from .ui import GRID_LABELS, GridFrame


APP_NAME = "autoR"


def default_db_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path.home() / "AppData" / "Local" / APP_NAME
    else:
        base = Path.cwd() / ".data"
    return base / "grid.sqlite3"


class App(ttk.Frame):
    def __init__(self, master: tk.Tk, db_path: Path) -> None:
        super().__init__(master)
        self.master = master
        self.db_path = db_path

        self.con = connect(db_path)
        init_db(self.con, GridSize(rows=50, cols=len(GRID_LABELS)))

        self.size = get_grid_size(self.con)
        self._cells = get_cells(self.con)

        self._build_menu()
        self._build_ui()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        filem = tk.Menu(menubar, tearoff=False)
        filem.add_command(label="Open DB...", command=self._open_db)
        filem.add_command(label="New DB...", command=self._new_db)
        filem.add_separator()
        filem.add_command(label="Export CSV...", command=self._export_csv)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=filem)
        self.master.config(menu=menubar)

    def _build_ui(self) -> None:
        self.pack(fill="both", expand=True)

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Button(top, text="Export", command=self._export_csv).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Sync", command=self._open_sync_modal).pack(side="left", padx=(0, 14))

        ttk.Label(top, text="DB:").pack(side="left")
        self._db_label = ttk.Label(top, text=str(self.db_path))
        self._db_label.pack(side="left", padx=(6, 12))

        ttk.Button(top, text="Save", command=self._save).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Delete row", command=self._delete_selected_row).pack(side="left", padx=(0, 12))

        ttk.Button(top, text="Resync", command=self._resync).pack(side="left", padx=(0, 12))
        ttk.Button(top, text="Add row above", command=lambda: self._add_row(relative="above")).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Add row below", command=lambda: self._add_row(relative="below")).pack(side="left", padx=(0, 12))

        ttk.Button(top, text="Open DB", command=self._open_db).pack(side="left")
        ttk.Button(top, text="New DB", command=self._new_db).pack(side="left", padx=(6, 0))

        self._grid = GridFrame(
            self,
            size=self.size,
            get_value=self._get_value,
            set_value=self._set_value,
            on_row_action=self._row_action,
        )
        self._grid.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _get_value(self, r: int, c: int) -> str:
        return self._cells.get((r, c), "")

    def _set_value(self, r: int, c: int, v: str) -> None:
        self._cells[(r, c)] = v
        set_cell(self.con, r, c, v)

    def _open_db(self) -> None:
        path = filedialog.askopenfilename(
            title="Open SQLite DB",
            filetypes=[("SQLite DB", "*.sqlite3 *.db *.sqlite"), ("All files", "*.*")],
        )
        if not path:
            return
        self._switch_db(Path(path))

    def _new_db(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Create SQLite DB",
            defaultextension=".sqlite3",
            filetypes=[("SQLite DB", "*.sqlite3"), ("All files", "*.*")],
        )
        if not path:
            return
        p = Path(path)
        try:
            con = connect(p)
            init_db(con, GridSize(rows=50, cols=len(GRID_LABELS)))
            con.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._switch_db(p)

    def _switch_db(self, new_path: Path) -> None:
        try:
            self.con.close()
        except Exception:
            pass

        self.db_path = new_path
        self.con = connect(new_path)
        init_db(self.con, GridSize(rows=self.size.rows, cols=self.size.cols))
        self._cells = get_cells(self.con)

        self._db_label.config(text=str(self.db_path))
        self._grid.rebuild(self.size)

    def _save(self) -> None:
        self.con.commit()

    def _resync(self) -> None:
        self._cells = get_cells(self.con)
        self._grid.refresh_all()

    def _selected_row(self) -> int:
        sel = self._grid._tree.selection()
        if sel:
            try:
                return int(sel[0])
            except Exception:
                pass
        focus = self._grid._tree.focus()
        if focus:
            try:
                return int(focus)
            except Exception:
                pass
        return 0

    def _add_row(self, relative: str) -> None:
        row = self._selected_row()
        at = row if relative == "above" else row + 1
        insert_row(self.con, at)
        self.size = get_grid_size(self.con)
        self._cells = get_cells(self.con)
        self._grid.rebuild(self.size)

    def _delete_selected_row(self) -> None:
        row = self._selected_row()
        delete_row(self.con, row)
        self.size = get_grid_size(self.con)
        self._cells = get_cells(self.con)
        self._grid.rebuild(self.size)

    def _row_action(self, action: str, row_idx: int) -> None:
        if action == "save":
            self._save()
        elif action == "resync":
            self._resync()
        elif action == "add_above":
            insert_row(self.con, row_idx)
            self.size = get_grid_size(self.con)
            self._cells = get_cells(self.con)
            self._grid.rebuild(self.size)
        elif action == "add_below":
            insert_row(self.con, row_idx + 1)
            self.size = get_grid_size(self.con)
            self._cells = get_cells(self.con)
            self._grid.rebuild(self.size)

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            header: list[str] = []
            for i in range(self.size.cols):
                if i < len(GRID_LABELS):
                    header.append(GRID_LABELS[i])
                else:
                    header.append(chr(ord("A") + (i % 26)))
            w.writerow(header)
            for r in range(self.size.rows):
                w.writerow([self._get_value(r, c) for c in range(self.size.cols)])

    def _open_sync_modal(self) -> None:
        modal = tk.Toplevel(self.master)
        modal.title("Sync from folder")
        modal.geometry("900x260")
        modal.transient(self.master)
        modal.grab_set()

        tk.Label(modal, text="Selected Folder:").pack(pady=6)

        folder_entry = tk.Entry(modal, width=90)
        folder_entry.pack(pady=5)

        def choose_folder() -> None:
            folder = filedialog.askdirectory(parent=modal)
            if folder:
                folder_entry.delete(0, tk.END)
                folder_entry.insert(0, folder)

        tk.Button(modal, text="Browse", command=choose_folder).pack(pady=5)

        status_label = tk.Label(modal, text="Status: Idle", fg="blue")
        status_label.pack(pady=10)

        run_button = tk.Button(modal, text="Sync")
        run_button.pack(pady=10)

        ignore_folders = {"xml", "__pycache__"}

        def folder_sort_key(name: str) -> int:
            m = re.match(r"\d+", name)
            return int(m.group(0)) if m else 10**9

        def task(folder_path: str) -> None:
            try:
                root = Path(folder_path)
                if not root.exists():
                    status_label.config(text="Folder not found", fg="red")
                    return

                folders = [p for p in root.iterdir() if p.is_dir() and p.name.lower() not in ignore_folders]
                folders = sorted(folders, key=lambda p: folder_sort_key(p.name))

                status_label.config(text=f"Found {len(folders)} folders", fg="blue")
                status_label.update_idletasks()

                clear_cells(self.con)
                self._cells = {}

                max_rows_needed = max(self.size.rows, len(folders))
                if max_rows_needed != self.size.rows:
                    init_db(self.con, GridSize(rows=max_rows_needed, cols=self.size.cols))
                    self.size = get_grid_size(self.con)

                for i, folder in enumerate(folders):
                    status_label.config(text=f"Processing ({i+1}/{len(folders)}): {folder.name}", fg="blue")
                    status_label.update_idletasks()

                    excel_count = len([f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in (".xlsx", ".xlsm")])
                    self._set_value(i, 0, folder.name)
                    if self.size.cols > 1:
                        self._set_value(i, 1, str(excel_count))
                    if self.size.cols > 2:
                        self._set_value(i, 2, str(folder))

                status_label.config(text="✅ Sync done", fg="green")
            except Exception as e:
                status_label.config(text=str(e), fg="red")
            finally:
                self._resync()
                run_button.config(state="normal")

        def start_sync() -> None:
            folder_path = folder_entry.get().strip()
            if not folder_path:
                status_label.config(text="Please select a folder!", fg="red")
                return
            run_button.config(state="disabled")
            threading.Thread(target=lambda: task(folder_path), daemon=True).start()

        run_button.config(command=start_sync)


def run() -> None:
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1100x650")
    try:
        root.state("zoomed")
    except Exception:
        pass

    ttk.Style().theme_use("clam")
    App(root, default_db_path())
    root.mainloop()

