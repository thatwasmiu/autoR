import re
import sys
import os
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
def create_daily_report(root, status_label=None):
    folders = [
        f for f in root.iterdir()
        if f.is_dir() and f.name.lower() not in ignore_folders
    ]
    folders = sorted(folders, key=folder_sort_key)
    
    grouped = defaultdict(list)

    for i, folder in enumerate(folders, start=1):
        try:
            if status_label:
                status_label.config(text=f"Processing ({i}/{len(folders)}): {folder.name}")
                status_label.update_idletasks()
            else:
                print(f"Processing ({i}/{len(folders)}): {folder.name}")

            data = get_data(folder)

            if data.get("declareCode") is None:
                continue
            method = (data.get("method") or "Khác").strip().lower()

            grouped[method].append(data)

        except Exception as e:
            print(f"❌ Error with folder: {folder}")
            print(e)
    timestamp = datetime.now().strftime("%H%M%S")
    output_file = root / f"BC_{root.name}_{timestamp}.xlsx"

    template_path = get_resource_path("resources/daily_template.xlsx")
    status_label.config(text=f"Start printing!!!")
    wb = write_daily_report(template_path, grouped)
    wb.save(output_file)

    if status_label:
        status_label.config(text=f"✅ Done! Saved: {str(output_file)}")
    else:
        print(f"Done! Saved: {output_file}")

    os.startfile(output_file)    

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

    def start_process():
        folder_path = folder_entry.get()
        selected_type = report_type.get()

        if folder_path:
            run_button.config(state="disabled")

            def task():
                if selected_type == "daily":
                    create_daily_report(Path(folder_path), status_label)
                elif selected_type == "weekly":
                    from_date = from_entry.get()
                    to_date = to_entry.get()
                    print(from_date, to_date)
                    if (validate_date(from_date, to_date, status_label, run_button)):
                        create_weekly_report(Path(folder_path), from_date, to_date, status_label)

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