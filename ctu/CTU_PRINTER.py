import win32com.client
from pathlib import Path
# import tkinter as tk
# from tkinter import filedialog
# from tkinter import messagebox

def excel_to_pdf_batch(root):
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    shell = win32com.client.Dispatch("WScript.Shell")

    files = [
        f for f in root.rglob("*.xls*")
        if "合同_发票_箱单" in f.name and not f.name.startswith("~$")
    ]
    total = len(files)

    for idx, file in enumerate(files, 1):
        # show progress
        shell.Popup(
            f"Tìm thấy file {idx}/{total}\n{file.name}",
            1,
            "CTU PRINTER",
            64
        )

        output_pdf = file.with_name("CIPL.pdf")

        print("Printing:", file)
        print("Kết quả in:", output_pdf)

        wb = excel.Workbooks.Open(str(file))

        all_sheets = [sheet.Name for sheet in wb.Worksheets]

        ordered = []
        if "INVForm" in all_sheets:
            ordered.append("INVForm")
        if "PackingList" in all_sheets:
            ordered.append("PackingList")

        for name in all_sheets:
            if name not in ordered:
                ordered.append(name)

        for name in ordered:
            sheet = wb.Worksheets(name)
            sheet.PageSetup.Orientation = 1
            sheet.PageSetup.Zoom = False
            sheet.PageSetup.FitToPagesWide = 1
            sheet.PageSetup.FitToPagesTall = 1

        for i, name in enumerate(ordered):
            wb.Worksheets(name).Move(Before=wb.Worksheets(i + 1))

        wb.Worksheets.Select()
        wb.ActiveSheet.ExportAsFixedFormat(
            Type=0,
            Filename=str(output_pdf),
            Quality=0,
            IncludeDocProperties=True,
            IgnorePrintAreas=False,
            OpenAfterPublish=False
        )

        wb.Close(False)

    excel.Quit()

    shell.Popup("Đã print xong toàn bộ file!", 2, "CTU PRINTER", 64)
    # messagebox.showinfo("Done", "All files converted.")


# --- GUI folder picker ---
# def choose_folder():
#     root = tk.Tk()
#     root.withdraw()  # hide main window
#     folder = filedialog.askdirectory(title="Select root folder")
#     return folder

def choose_folder():
    shell = win32com.client.Dispatch("Shell.Application")
    folder = shell.BrowseForFolder(0, "Chọn thư mục gốc cần in ctu", 0, 0)
    if folder:
        return folder.Self.Path
    return None

def show_status(text):
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.Popup(text, 1, "CTU PRINTER", 64)

if __name__ == "__main__":
    folder = choose_folder()

    if folder:
        excel_to_pdf_batch(Path(folder))
    else:
        print("No folder selected.")