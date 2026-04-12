import sys
import os
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import threading
from collections import defaultdict

from modules import write_daily_report
from daily_invoice import get_data
ignore_folders = {"xml", "__pycache__"}

# pyinstaller --clean --onefile --noconsole --name eportR --add-data "resources/daily_template.xlsx;resources" --add-data "resources/logo.ico;resources" --icon=resources/logo.ico main.py
def create_report(root, status_label=None):
    folders = [
        f for f in root.iterdir()
        if f.is_dir() and f.name.lower() not in ignore_folders
    ]
    folders = sorted(
        folders,
        key=lambda f: int(f.name.split(".",1)[0])
    )
    
    grouped = defaultdict(list)

    for i, folder in enumerate(folders, start=1):
        # try:
        if status_label:
            status_label.config(text=f"Processing ({i}/{len(folders)}): {folder.name}")
            status_label.update_idletasks()
        else:
            print(f"Processing ({i}/{len(folders)}): {folder.name}")

        data = get_data(folder)
        method = (data.get("method") or "Khác").strip().lower()
        grouped[method].append(data)

        # except Exception as e:
        #     print(f"Error with folder: {folder}")
        #     print(e)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = root / f"report_{root.name}_{timestamp}.xlsx"

    template_path = get_resource_path("resources/daily_template.xlsx")
    status_label.config(text=f"Start printing!!!")
    wb = write_daily_report(template_path, grouped)
    wb.save(output_file)

    if status_label:
        status_label.config(text=f"✅ Done! Saved: {str(output_file)}")
    else:
        print(f"Done! Saved: {output_file}")

    os.startfile(output_file)    


def choose_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)


def run_app():
    root = tk.Tk()
    root.iconbitmap(get_resource_path("resources/logo.ico"))
    root.title("Daily Report Tool")
    root.geometry("900x250")

    tk.Label(root, text="Selected Folder:").pack(pady=5)

    folder_entry = tk.Entry(root, width=80)
    folder_entry.pack(pady=5)

    tk.Button(root, text="Browse", command=lambda: choose_folder(folder_entry)).pack(pady=5)

    status_label = tk.Label(root, text="Status: Idle", fg="blue")
    status_label.pack(pady=10)

    run_button = tk.Button(root, text="Run Report")
    run_button.pack(pady=10)

    def start_process():
        folder_path = folder_entry.get()
        if folder_path:
            run_button.config(state="disabled")

            def task():
                create_report(Path(folder_path), status_label)
                run_button.config(state="normal")

            threading.Thread(target=task, daemon=True).start()

    run_button.config(command=start_process)

    root.mainloop()


def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        create_report(Path(folder), status_label=None)
    else:
        run_app()