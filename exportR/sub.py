import sys
import os
from pathlib import Path
from datetime import datetime
import threading
import win32com.client

sys.path.insert(0, os.path.dirname(__file__))
from modules import get_data, write_daily_report

ignore_folders = {"xml", "__pycache__"}


def create_report(root, status_label=None):
    folders = [
        f for f in root.iterdir()
        if f.is_dir() and f.name.lower() not in ignore_folders
    ]
    folders = sorted(
        folders,
        key=lambda f: int(f.name.split(".",1)[0])
    )

    data_list = []

    for i, folder in enumerate(folders, start=1):
        try:
            if status_label:
                status_label.config(text=f"Processing ({i}/{len(folders)}): {folder.name}")
                status_label.update_idletasks()
            else:
                print(f"Processing ({i}/{len(folders)}): {folder.name}")

            data = get_data(str(folder))
            data_list.append(data)

        except Exception as e:
            print(f"Error with folder: {folder}")
            print(e)

    print(data_list)
    return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = root / f"report_{root.name}_{timestamp}.xlsx"

    template_path = get_resource_path("daily_template.xlsx")
    wb = write_daily_report(template_path, data_list)
    wb.save(output_file)

    if status_label:
        status_label.config(text=f"✅ Done! Saved: {str(output_file)}")
    else:
        print(f"Done! Saved: {output_file}")

    os.startfile(output_file)  


def choose_folder():
    shell = win32com.client.Dispatch("Shell.Application")
    folder = shell.BrowseForFolder(0, "Chọn thư mục ngày vd: 06.04", 0, 0)
    if folder:
        return folder.Self.Path
    return None

if __name__ == "__main__":
    # folder = choose_folder()

    # if folder:
        create_report(Path(r"C:\Users\datnt4\works\autoR\06.04"))
    # else:
        # print("No folder selected.")