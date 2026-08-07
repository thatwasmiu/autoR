import re
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, time
import tkinter as tk
from tkinter import filedialog, ttk
from tkcalendar import DateEntry
import threading
from collections import defaultdict

from modules import write_daily_report
from daily_invoice import get_data
from weekly_report import create_weekly_report
from log_config import setup_logging

logger = setup_logging()
ignore_folders = {"xml", "__pycache__"}

ROUTE_LABELS = {'1': "Xanh", '2': "Vàng", '3': "Đỏ"}


def format_route_type(route_code, date_str):
    label = ROUTE_LABELS.get(route_code, route_code or "")
    if route_code in ("1", "2") and date_str:
        try:
            date_val = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            if date_val.time() > time(17, 0):
                label = f"{label} OT"
        except (ValueError, TypeError):
            pass
    return label


def format_date_only(date_str):
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str

# pyinstaller --clean --onefile --noconsole --name eportR --add-data "resources/daily_template.xlsx;resources" --add-data "resources/logo.ico;resources" --icon=resources/logo.ico main.py

def collect_daily_data(root, status_label=None):
    folders = [
        f for f in root.iterdir()
        if f.is_dir() and f.name.lower() not in ignore_folders
    ]
    folders = sorted(folders, key=folder_sort_key)
    folders = re_index_folder(folders)
    grouped = defaultdict(list)

    for i, folder in enumerate(folders, start=1):
        try:
            if status_label:
                status_label.config(text=f"Đang xử lý ({i}/{len(folders)}): {folder.name}")
                status_label.update_idletasks()
            logger.info(f"Processing folder ({i}/{len(folders)}): {folder.name}")

            data = get_data(folder)
            method = (data.get("method") or "Khác").strip().lower()
            if method in ("air", "sea"):
                method = "air - sea"
            grouped[method].append(data)
            logger.debug(f"Folder '{folder.name}' -> method={method!r}, nvlCode={data.get('nvlCode')!r}, declareCode={data.get('declareCode')!r}")

        except Exception:
            logger.exception(f"Failed to process folder: {folder.name}")

    result = {
        method: sorted(items, key=nvl_code_number)
        for method, items in sorted(grouped.items())
    }
    logger.info("Grouped folders: " + ", ".join(f"{m} x{len(v)}" for m, v in result.items()))
    return result


def nvl_code_number(data):
    nvlCode = data.get("nvlCode") or ""
    match = re.search(r'\d+', nvlCode)
    return int(match.group()) if match else float('inf')


def export_excel(root, grouped, status_label=None):
    timestamp = datetime.now().strftime("%H%M%S")
    output_file = root / f"BC_{root.name}_{timestamp}.xlsx"
    template_path = get_resource_path("resources/daily_template.xlsx")
    if status_label:
        status_label.config(text="Đang xuất file Excel…")
        status_label.update_idletasks()
    wb = write_daily_report(template_path, grouped)
    wb.save(output_file)
    if status_label:
        status_label.config(text=f"✅ Đã lưu: {str(output_file)}")
    os.startfile(output_file)



def re_index_folder(folders):
    updated = []

    for i, folder in enumerate(folders, start=1):
        base_name = re.sub(r'^\d+\.\s*', '', folder.name)
        new_folder = folder.parent / f"{i}.{base_name}"

        if folder != new_folder:
            folder = folder.rename(new_folder)

        updated.append(folder)

    return updated

def folder_sort_key(f):
    match = re.match(r"\d+", f.name)
    if match:
        return int(match.group())
    return float('inf')

def choose_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)


def run_app():
    root = tk.Tk()
    root.iconbitmap(get_resource_path("resources/logo.ico"))
    root.title("Daily Report Tool")
    root.geometry("1000x650")

    tk.Label(root, text="Selected Folder:").pack(pady=5)

    folder_entry = tk.Entry(root, width=80)
    folder_entry.pack(pady=5)

    tk.Button(root, text="Browse", command=lambda: choose_folder(folder_entry)).pack(pady=5)

    # ✅ Report type selection
    report_type = tk.StringVar(value="daily")

    tk.Label(root, text="Select Report Type:").pack(pady=5)

    frame = tk.Frame(root)
    frame.pack()

    # ✅ Get current week range (Mon → Sun)
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())   # Monday
    end_of_week = start_of_week + timedelta(days=6)           # Sunday


    # ✅ Week selector (placed BEFORE Run button)
    week_frame = tk.Frame(root)

    from_frame = tk.Frame(week_frame)
    from_frame.pack(side="left", padx=10)

    tk.Label(from_frame, text="From Date:").pack()
    from_entry = DateEntry(from_frame, width=18, date_pattern="dd/mm/yyyy")
    from_entry.set_date(start_of_week)
    from_entry.pack(pady=2)

    to_frame = tk.Frame(week_frame)
    to_frame.pack(side="left", padx=10)

    tk.Label(to_frame, text="To Date:").pack()
    to_entry = DateEntry(to_frame, width=18, date_pattern="dd/mm/yyyy")
    to_entry.set_date(end_of_week) 
    to_entry.pack(pady=2)

    def on_type_change():
        if report_type.get() == "weekly":
            week_frame.pack(before=status_label, pady=5)  # ✅ force position above button
        else:
            week_frame.pack_forget()
            
    tk.Radiobutton(frame, text="Daily", variable=report_type, value="daily",
                   command=on_type_change).pack(side="left", padx=10)

    tk.Radiobutton(frame, text="Weekly", variable=report_type, value="weekly",
                   command=on_type_change).pack(side="left", padx=10)

    status_label = tk.Label(root, text="Status: Idle", fg="blue")
    status_label.pack(pady=10)

    run_button = tk.Button(root, text="Run Report")
    run_button.pack(pady=10)

    # Action buttons — hidden until data is ready
    action_frame = tk.Frame(root)
    _state = {"grouped": None, "root_path": None}

    def on_excel():
        def task():
            try:
                export_excel(_state["root_path"], _state["grouped"], status_label)
            except Exception as e:
                logger.exception("Failed to export Excel report")
                status_label.config(text=f"❌ Lỗi xuất file: {e}", fg="red")

        threading.Thread(target=task, daemon=True).start()

    tk.Button(action_frame, text="Xuất file Excel", width=18, command=on_excel).pack(side="left", padx=8)

    # Copyable results table — hidden until data is ready
    table_columns = ["method", "nvlCode", "declareCode", "date", "routeType", "internalCode"]
    table_headers = {
        "method": "Loại hàng",
        "nvlCode": "NVL",
        "declareCode": "Số TK",
        "date": "Ngày",
        "routeType": "Luồng",
        "internalCode": "Số QL nội bộ",
    }

    table_frame = tk.Frame(root)

    tree = ttk.Treeview(table_frame, columns=table_columns, show="headings", height=12)
    for col in table_columns:
        tree.heading(col, text=table_headers[col])
        tree.column(col, width=90, anchor="w")

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    def on_cell_click(event):
        if tree.identify_region(event.x, event.y) != "cell":
            return
        row_id = tree.identify_row(event.y)
        col_id = tree.identify_column(event.x)
        if not row_id or not col_id:
            return
        tree.selection_set(row_id)
        tree.focus(row_id)

        col_index = int(col_id.replace("#", "")) - 1
        if not (0 <= col_index < len(table_columns)):
            return
        value = tree.set(row_id, table_columns[col_index])
        root.clipboard_clear()
        root.clipboard_append(str(value))
        status_label.config(text=f"📋 Đã copy: {value}", fg="blue")

    tree.bind("<Button-1>", on_cell_click)

    def populate_table(grouped):
        tree.delete(*tree.get_children())
        for method, items in grouped.items():
            for data in items:
                if data.get("declareCode") is None:
                    continue
                row = [
                    method.upper(),
                    data.get("nvlCode", ""),
                    data.get("declareCode", ""),
                    format_date_only(data.get("date")),
                    format_route_type(data.get("routeType"), data.get("date")),
                    data.get("internalCode", ""),
                ]
                tree.insert("", "end", values=row)

    def show_actions(root_path, grouped):
        _state["root_path"] = root_path
        _state["grouped"] = grouped
        action_frame.pack(pady=6)
        populate_table(grouped)
        table_frame.pack(pady=6, padx=10, fill="both", expand=True)

    def hide_actions():
        action_frame.pack_forget()
        table_frame.pack_forget()
        tree.delete(*tree.get_children())

    def start_process():
        folder_path = folder_entry.get()
        selected_type = report_type.get()

        if folder_path:
            hide_actions()
            run_button.config(state="disabled")

            def task():
                try:
                    if selected_type == "daily":
                        grouped = collect_daily_data(Path(folder_path), status_label)
                        # print(grouped)
                        status_label.config(text="✅ Đã xử lý xong. Chọn hành động tiếp theo.")
                        root.after(0, lambda: show_actions(Path(folder_path), grouped))
                    elif selected_type == "weekly":
                        from_date = from_entry.get()
                        to_date = to_entry.get()
                        logger.debug(f"Weekly report range: {from_date} -> {to_date}")
                        if (validate_date(from_date, to_date, status_label, run_button)):
                            create_weekly_report(Path(folder_path), from_date, to_date, status_label)
                except Exception as e:
                    logger.exception("Failed to run report")
                    status_label.config(text=f"❌ Lỗi: {e}", fg="red")
                finally:
                    run_button.config(state="normal")

            threading.Thread(target=task, daemon=True).start()
        else:
            status_label.config(text="Please select a folder!", fg="red")    

    run_button.config(command=start_process)  

    def close_picker(picker):
        try:
            if picker._top_cal.winfo_ismapped():
                picker._top_cal.withdraw()
        except:
            pass

    def on_click(event):
        if event.widget not in (from_entry, to_entry):
            close_picker(from_entry)
            close_picker(to_entry)

    root.bind_all("<Button-1>", on_click)

    root.mainloop()

def validate_date(from_date, to_date, status_label, run_button): 
        if not from_date or not to_date:
            status_label.config(text="Please select both From and To dates!", fg="red")
            run_button.config(state="normal")
            return False

        # parse & validate order
        try:
            from_dt = datetime.strptime(from_date, "%d/%m/%Y")
            to_dt = datetime.strptime(to_date, "%d/%m/%Y")

            if from_dt > to_dt:
                status_label.config(text="From Date must be <= To Date!", fg="red")
                run_button.config(state="normal")
                return False
        except ValueError:
            status_label.config(text="Invalid date format! Use dd/mm/yyyy", fg="red")
            run_button.config(state="normal")
            return False
        
        return True  

def get_weeks_of_year():
    today = datetime.now()
    year_start = datetime(today.year, 1, 1)

    weeks = []
    current = year_start

    while current.year == today.year:
        week_num = current.isocalendar()[1]
        month_text = current.strftime("%b")
        label = f"W {week_num}/{month_text}"

        if label not in weeks:  # avoid duplicates
            weeks.append(label)

        current += timedelta(days=7)

    return weeks

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

if __name__ == "__main__":
    run_app()