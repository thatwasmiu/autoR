import re
import sys
import os
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog
from tkcalendar import DateEntry
import threading
from collections import defaultdict

from modules import write_daily_report
from daily_invoice import get_data
from weekly_report import create_weekly_report
ignore_folders = {"xml", "__pycache__"}
from tkinter import ttk

# pyinstaller --clean --onefile --noconsole --name eportR --add-data "resources/daily_template.xlsx;resources" --add-data "resources/logo.ico;resources" --icon=resources/logo.ico main.py

GSHEET_CONFIG_KEYS = ["endpoint", "sheetLink", "editMode"]

GSHEET_DEFAULT_CONFIG = {
    "endpoint": "https://script.google.com/macros/s/AKfycbzGX6KIBVbCeULyUvtV-jXXyKJ9vrTffzCoQ_CTX_bZVI_3PwU8CO86elPLdT1tQ5vX/exec",
    "sheetLink": "",
    "editMode": "highlight",
}

def _config_path():
    base = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
    return os.path.join(base, "gsheet_config.json")

def load_gsheet_config():
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_gsheet_config(data):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump({k: data[k] for k in GSHEET_CONFIG_KEYS if k in data}, f, indent=2)
    except Exception as exc:
        print(f"Could not save config: {exc}")
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
            else:
                print(f"Processing ({i}/{len(folders)}): {folder.name}")

            data = get_data(folder)
            method = (data.get("method") or "Khác").strip().lower()
            grouped[method].append(data)

        except Exception as e:
            print(f"❌ Error with folder: {folder}")
            print(e)

    return dict(grouped)


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



def show_gsheet_form(parent, grouped):
    form = tk.Toplevel(parent)
    form.title("Cài đặt Google Sheet")
    form.geometry("520x370")
    form.resizable(False, False)
    form.grab_set()
    form.focus_set()

    cfg = {**GSHEET_DEFAULT_CONFIG, **load_gsheet_config()}

    entries = {}
    for label_text, key in [
        ("Endpoint URL:", "endpoint"),
        ("Link Sheet:", "sheetLink"),
    ]:
        row = tk.Frame(form)
        row.pack(fill="x", padx=20, pady=6)
        tk.Label(row, text=label_text, width=14, anchor="w").pack(side="left")
        entry = tk.Entry(row, width=44)
        entry.insert(0, cfg.get(key, ""))
        entry.pack(side="left")
        entries[key] = entry

    mode_row = tk.Frame(form)
    mode_row.pack(fill="x", padx=20, pady=6)
    tk.Label(mode_row, text="Chế độ:", width=14, anchor="w").pack(side="left")
    edit_mode_var = tk.StringVar(value=cfg.get("editMode", "highlight"))
    ttk.Combobox(mode_row, textvariable=edit_mode_var,
                 values=["normal", "highlight"], state="readonly", width=18).pack(side="left")

    def reset_defaults():
        for key, entry in entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, GSHEET_DEFAULT_CONFIG.get(key, ""))
        edit_mode_var.set(GSHEET_DEFAULT_CONFIG["editMode"])

    status_lbl = tk.Label(form, text="", fg="blue")
    status_lbl.pack(pady=4)

    error_box = tk.Text(form, height=6, width=60, state="disabled", fg="red", relief="flat", bg="#fff8f8")
    error_box.pack(padx=20, pady=4)

    def show_errors(errors):
        error_box.config(state="normal")
        error_box.delete("1.0", tk.END)
        error_box.insert(tk.END, "\n".join(errors))
        error_box.config(state="disabled")

    def on_submit():
        endpoint   = entries["endpoint"].get().strip()
        sheet_link = entries["sheetLink"].get().strip()
        edit_mode  = edit_mode_var.get()

        if not endpoint:
            status_lbl.config(text="Endpoint không được để trống!", fg="red")
            return

        save_gsheet_config({
            "endpoint": endpoint,
            "sheetLink": sheet_link,
            "editMode": edit_mode,
        })

        status_lbl.config(text="Đang gửi…", fg="blue")
        show_errors([])
        form.update_idletasks()

        route_type_map = {"1": "XANH", "2": "VÀNG", "3": "ĐỎ"}

        def _fmt_date(val):
            if not val:
                return val
            try:
                return datetime.strptime(val, "%d/%m/%Y %H:%M:%S").strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                return val

        def send():
            data = {
                method: [
                    {
                        **r,
                        "routeType": route_type_map.get(str(r.get("routeType", "")), r.get("routeType", "")),
                        "date": _fmt_date(r.get("date")),
                    }
                    for r in records
                    if r.get("declareCode")
                ]
                for method, records in grouped.items()
            }
            body = {
                "sheetLink": sheet_link,
                "editMode": edit_mode,
                "data": data,
            }
            # print(body)
            try:
                payload = json.dumps(body).encode("utf-8")
                print(payload)
                req = urllib.request.Request(
                    endpoint, data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req) as resp:
                    raw = resp.read()
                    print(raw)
                    result = json.loads(raw)
                    if result.get("status") == "ok":
                        errors = result.get("errors", [])
                        if errors:
                            status_lbl.config(
                                text=f"Hoàn tất với {len(errors)} lỗi:", fg="orange"
                            )
                            show_errors(errors)
                        else:
                            status_lbl.config(
                                text=f"✅ Đã gửi {sum(len(v) for v in data.values())} bản ghi thành công!", fg="green"
                            )
                    else:
                        status_lbl.config(text=f"Lỗi: {result.get('message')}", fg="red")
            except Exception as exc:
                status_lbl.config(text=f"Gửi thất bại: {exc}", fg="red")

        threading.Thread(target=send, daemon=True).start()

    btn_row = tk.Frame(form)
    btn_row.pack(pady=6)
    tk.Button(btn_row, text="Gửi", width=12, command=on_submit).pack(side="left", padx=8)
    tk.Button(btn_row, text="Mặc định", width=12, command=reset_defaults).pack(side="left", padx=8)


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
    root.geometry("900x350")

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
                print(f"❌ Error exporting excel: {e}")
                status_label.config(text=f"❌ Lỗi xuất file: {e}", fg="red")

        threading.Thread(target=task, daemon=True).start()

    def on_gsheet():
        show_gsheet_form(root, _state["grouped"])

    tk.Button(action_frame, text="Xuất file Excel", width=18, command=on_excel).pack(side="left", padx=8)
    tk.Button(action_frame, text="Gửi lên GGL Sheet", width=18, command=on_gsheet).pack(side="left", padx=8)

    def show_actions(root_path, grouped):
        _state["root_path"] = root_path
        _state["grouped"] = grouped
        action_frame.pack(pady=6)

    def hide_actions():
        action_frame.pack_forget()

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
                        status_label.config(text="✅ Đã xử lý xong. Chọn hành động tiếp theo.")
                        root.after(0, lambda: show_actions(Path(folder_path), grouped))
                    elif selected_type == "weekly":
                        from_date = from_entry.get()
                        to_date = to_entry.get()
                        print(from_date, to_date)
                        if (validate_date(from_date, to_date, status_label, run_button)):
                            create_weekly_report(Path(folder_path), from_date, to_date, status_label)
                except Exception as e:
                    print(f"❌ Error running report: {e}")
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