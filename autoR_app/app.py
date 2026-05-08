from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import csv
import re
import threading

from .db import DeclareForm, connect, init_db, get_active_folder, get_declare_forms, save_cell, save_declare_forms, sync_data_folder
from .sync_data import open_sync_modal
from .sheet_ui import DeclareFormSheet
from typing import List
from dataclasses import asdict

APP_NAME = "autoR"

MAP_LABELS = {
    "id": "id",
    "folder_id": "folder_id",
    "nvl_code": "NVL",
    "bill": "Bill",
    "invoice": "Invoice",
    "type_code": "Loại hình",
    "progress": "Tiến độ",
    
    "date": "Ngày",
    "declare_code": "Số TK",
    "route_type": "Luồng",
    "form_code": "Loại TK",
    "term": "TERM",
    "tms": "TMS",

    "mail_time": "Giờ nhận Mail",
    "tms_time": "Giờ TMS",
    "draft_time": "Giờ gửi nháp",
    "tk_time": "Giờ xác nhận TK",
    "official_time": "Giờ truyền chính thức",
    "passed_time": "Giờ mail thông quan",
    "method": "Note"
}

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
        init_db(self.con)

        self._build_menu()
        self._build_ui()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        filem = tk.Menu(menubar, tearoff=False)
        # filem.add_command(label="Open DB...", command=self._open_db)
        # filem.add_command(label="New DB...", command=self._new_db)
        filem.add_separator()
        filem.add_command(label="Export CSV...", command=self._export_csv)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=filem)
        self.master.config(menu=menubar)

    def _build_ui(self) -> None:
        self._filter = {}
        self._records = []
        self._folder_map = None
        self._selected_folder = None

        self.pack(fill="both", expand=True)

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Button(top, text="Export", command=self._export_csv).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="Sync", command=self._open_sync_modal).pack(side="left", padx=(0, 14))

        ttk.Label(top, text="DB:").pack(side="left")
        self._db_label = ttk.Label(top, text=str(self.db_path))
        self._db_label.pack(side="left", padx=(6, 12))

        # Load folders
        self._selected_folder = tk.StringVar()
        self._folder_combobox = ttk.Combobox(
            top,
            textvariable=self._selected_folder,
            # values=list(self._folder_map.keys()),
            state="readonly",
            width=25
        )
        self._folder_combobox.pack(side="left", padx=(0, 6))
        # Trigger when selection changes
        self._folder_combobox.bind("<<ComboboxSelected>>", self._on_folder_selected)

        # Search / Load button
        ttk.Button(
            top,
            text="Search",
            command=self._filter_data
        ).pack(side="left", padx=(0, 10))

        self._sheet = DeclareFormSheet(
            self,
            list(MAP_LABELS.values()),
            records=self._records,
            metadata_headers=["id", "folder_id"],
            on_edit_callback=self._save_cell
            )
        self._sheet.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.master.bind("<Control-s>", self._save_sheet)
        self.master.bind("<Control-S>", self._save_sheet)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        self.set_folders()

    def _on_close(self, event=None):
        if not self._sheet.is_modified:
            self.master.destroy()
            return

        result = messagebox.askyesnocancel(
            "Unsaved changes",
            "You have unsaved changes. Save before exiting?"
        )

        if result is None:
            # Cancel close
            return

        if result:
            self._save_sheet()
            # optionally re-check if save failed
        self.master.destroy()

    def _save_sheet(self):
        if self._sheet.is_modified:
            data = self._sheet.get_sheet_data()
            save_declare_forms(self.con, data, list(MAP_LABELS.keys()))
            self._sheet.modified_data_idx = []
            self._sheet.is_modified = False

    def set_folders(self):
        # Folder selector
        # Build lookup: folder name -> id
        self._active_folders = get_active_folder(self.con)
        self._folder_map = {
            folder["name"]: folder["id"]
            for folder in self._active_folders
        }

        if not self._active_folders:
            self._open_folder_selection_modal()
            self._active_folders = get_active_folder(self.con)
        
        self._get_active_folder_data(self.con)

    def reload(self):
        self._active_folders = get_active_folder(self.con)
        self._folder_map = {
            folder["name"]: folder["id"]
            for folder in self._active_folders
        }
        self._get_active_folder_data(self.con)    

    def _get_active_folder_data(self, con):
        if self._active_folders:
            self._selected_folder = self._active_folders[0]["id"]
            self._records = get_declare_forms(con, self._selected_folder) 
            self._sheet.set_sheet_data(self._records)
            self._folder_combobox.config(values=list(self._folder_map.keys()))    
            self._folder_combobox.current(0)  

    def _on_folder_selected(self, event=None):
        selected_name = self._selected_folder.get()
        folder_id = self._folder_map.get(selected_name)

        if folder_id is not None:
            self._filter["folder_id"] = folder_id

    def _save_cell(self, row, column, value, headers, records):
        column_name = headers[column]
        # Get original database row ID
        record_id = records[row]["id"]
        save_cell(self.con, column_name, record_id, value)
        print(f"Saved row {record_id}, column {column_name} = {value}")   

    def _open_folder_selection_modal(self) -> None:
        messagebox.showinfo(
            "No active folder",
            "No active folder found in the database. Please select a folder to sync data from."
        )
        self._open_sync_modal()

    def _row_action(self, action: str, row_idx: int) -> None:
        if action == "save":
            self._save()
        elif action == "resync":
            self._resync()

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        return

    def _save_form_call_back(self, form_data: dict) -> None:
        save_declare_forms(self.con, self._active_folder["id"], [form_data])

    def _filter_data(self) -> None:
        # self._filter.update(kwargs)
        self._records = get_declare_forms(self.con, self._filter.get("folder_id"))
        self._sheet.set_sheet_data(self._records)

    def sync_folder(self, folder_path, list_data: List[DeclareForm]):
        print("Call sync_folder with path:", folder_path)
        con = connect(default_db_path())
        try:
            sync_data_folder(con, list_data, folder_path)
        except Exception as e:
            print("❌ EXECUTEMANY ERROR:", e)
            raise
        con.close()

    def _open_sync_modal(self) -> None:
        open_sync_modal(self)


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

