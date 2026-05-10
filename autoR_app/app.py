from __future__ import annotations

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil

import csv
import re
import threading

from autoR_app.filter_modal import FilterModal

from .db import DeclareForm, connect, init_db, get_active_folder, get_declare_forms, save_cell, save_declare_forms, sync_data_folder, delete_columns, delete_empty_folder, get_folder_by_id, get_declare_forms_by_date_range
from .sync_data import open_sync_modal
from .report_modal import open_modal
from .sheet_ui import DeclareFormSheet
from .ctu_modal import open_ctu_modal
from typing import List

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
        filem.add_separator()
        filem.add_command(label="Xuất báo cáo", command=self._export_modal)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=filem)
        self.master.config(menu=menubar)

    def _build_ui(self) -> None:
        self._filter = {}
        self._records = []
        self._folder_map = None

        self.pack(fill="both", expand=True)

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        
        
        ttk.Button(top, text="Đồng bộ dữ liệu", command=self._open_sync_modal).pack(side="left", padx=(0, 14))
        ttk.Button(top, text="Xuất báo cáo", command=self._export_modal).pack(side="left", padx=(0, 6))
        ttk.Button(top, text="CTU", command=self._open_ctu_modal).pack(side="left", padx=(0, 14))

        ttk.Label(top, text="File giữ liệu:").pack(side="left")
        self._db_label = ttk.Label(
            top,
            text=str(self.db_path),
            foreground="blue",
            cursor="hand2"
        )
        self._db_label.pack(side="left")

        self._db_label.bind(
            "<Button-1>",
            lambda e: open_path(self.db_path)
        )
        self._db_label.configure(font=("Arial", 10, "underline"))

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
        ttk.Button(top, text="Outlook", command=self._open_out_look_modal).pack(side="left", padx=(0, 6))

        self._sheet = DeclareFormSheet(
            self,
            list(MAP_LABELS.values()),
            records=self._records,
            metadata_headers=["id", "folder_id"],
            on_row_action_callback=self._on_row_actions
            )
        self._sheet.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.master.bind("<Control-s>", self._save_sheet)
        self.master.bind("<Control-S>", self._save_sheet)
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._active_folders = get_active_folder(self.con)
        self._folder_map = {
            folder["name"]: folder["id"]
            for folder in self._active_folders
        }

        if not self._active_folders:
            self._open_folder_selection_modal()
            self._active_folders = get_active_folder(self.con)
        else:
            self._get_active_folder_data(self.con)
            self._folder_combobox.config(values=list(self._folder_map.keys()))    
            self._folder_combobox.current(0)

    def _on_close(self, event=None):
        self._save_before_doing()
        self.master.destroy()

    def _save_before_doing(self):
        self.master.focus_set()
        self.master.update_idletasks()
        self.master.update() # ensure all pending events are processed before checking modified state

        if not self._sheet.is_modified:
            return

        result = messagebox.askyesnocancel(
            "Có thay đổi chưa được lưu",
            "Bạn có muốn lưu rồi làm tiếp?"
        )

        if result is None:
            # Cancel close
            return

        if result:
            self._save_sheet()

    def _save_sheet(self, event=None):
        if self._sheet.is_modified:
            data = self._sheet.modified_datas
            save_declare_forms(self.con, data.values(), list(MAP_LABELS.keys()))
            self._sheet.modified_datas = {}
            self._sheet.is_modified = False

    def reload(self):
        self._active_folders = get_active_folder(self.con)
        self._folder_map = {
            folder["name"]: folder["id"]
            for folder in self._active_folders
        }
        if self._active_folders:
            self._get_active_folder_data(self.con)
            self._folder_combobox.config(values=list(self._folder_map.keys()))    
            self._folder_combobox.current(0)      

    def _get_active_folder_data(self, con):
        self._filter["folder_id"] = self._active_folders[0]["id"]
        self._records = get_declare_forms(con, self._filter["folder_id"]) 
        self._sheet.set_sheet_data(self._records)

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
            "Không có dữ liệu trong hệ thống",
            "Không có dữ liệu trong hệ thống. Hãy đồng bộ từ folder."
        )
        self._open_sync_modal()


    def _on_row_actions(self, action, row_datas):
    
        print("Row action:", action, row_datas)
        folderSet = set()
        for data in row_datas:
            if action == "delete":
                delete_columns(self.con, data[0], data[1])
                folderSet.add(data[1])
        for folder_id in folderSet:      
            delete_empty_folder(self.con, folder_id)        
        self._filter_data()        

    def _export_modal(self) -> None:
        self._save_before_doing()
        open_modal(self, get_declare_forms(self.con, self._filter["folder_id"]), get_folder_by_id(self.con, self._filter["folder_id"]), self.on_filter_by_date_range)

    def on_filter_by_date_range(self, start_date, end_date):
        con = connect(default_db_path())
        print("Filtering by date range:", start_date, end_date)
        records = get_declare_forms_by_date_range(con, start_date, end_date)
        con.close()
        return records

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
        self._save_before_doing()
        open_sync_modal(self)

    def _open_ctu_modal(self) -> None:
        open_ctu_modal(self)

    def _open_out_look_modal(self) -> None:
        FilterModal(self)  


def run() -> None:
    root = tk.Tk()
    root.title(APP_NAME)
    root.iconbitmap(get_resource_path(r"resources\rchan.ico"))
    root.geometry("1100x650")
    try:
        root.state("zoomed")
    except Exception:
        pass

    ttk.Style().theme_use("clam")
    App(root, default_db_path())
    root.mainloop()

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)


def open_path(path):
    if not path:
        return

    # If it's a file → get its folder
    if os.path.isfile(path):
        folder = os.path.dirname(path)
        os.startfile(folder)

    # If it's already a folder
    elif os.path.isdir(path):
        os.startfile(path)

    else:
        print("Path not found:", path)


def copy_to_folder(file_path, target_folder):
    if not file_path:
        return

    os.makedirs(target_folder, exist_ok=True)

    filename = os.path.basename(file_path)
    dest_path = os.path.join(target_folder, filename)

    shutil.copy2(file_path, dest_path)

    print("Copied to:", dest_path)
    return dest_path

def import_data(self):
    root = tk.Toplevel(self.master)
    root.title("Import data")
    root.geometry("900x550")
    root.transient(self.master)
    root.grab_set()

    tk.Label(root, text="Chọn file data cần import:").pack(pady=5)

    folder_entry = tk.Entry(root, width=80)
    folder_entry.pack(pady=5)

    tk.Button(root, text="Browse", command=lambda: choose_folder(folder_entry)).pack(pady=5)

    status_label = tk.Label(root, text="Status: Idle", fg="blue")
    status_label.pack(pady=10)

    run_button = tk.Button(root, text="Import")
    run_button.pack(pady=10)
    def start_process(): 
        folder_path = folder_entry.get()
        if not folder_path or not os.path.isfile(folder_path):
            messagebox.showerror("Error", "Please select a valid folder.")
            return

        run_button.config(state="disabled")
        status_label.config(text="Processing...", fg="orange")

        def process():
            copy_to_folder(default_db_path(), folder_path)
            status_label.config(text="Import completed!", fg="green")

        threading.Thread(target=process).start()
    run_button.config(command=start_process)
    

def choose_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)    