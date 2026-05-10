import win32com.client
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import sys
import os
from tkinter import filedialog
import threading
from PyPDF2 import PdfReader
from tkinter import messagebox

def excel_to_pdf_batch(root, status_label=None, tree_insert_callback=None):

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    files = [
        f for f in root.rglob("*.xls*")
        if "合同_发票_箱单" in f.name and not f.name.startswith("~$")
    ]

    results = []  # store (excel_file, pdf_file)

    total = len(files)

    for idx, file in enumerate(files, 1):
        if status_label:
            status_label.config(text=f"Processing ({idx}/{total}): {file.name}")
            status_label.update_idletasks()

        output_pdf = print_pdf(excel, file)
        reader = PdfReader(output_pdf)
        page_count = len(reader.pages)
        status = f"OK Page: {page_count}"
        results.append((str(file), str(output_pdf), status))

        # ✅ update UI table
        if tree_insert_callback:
            tree_insert_callback(str(file), str(output_pdf), status)

    excel.Quit()

    if status_label:
        status_label.config(text="✅ Done")

    return results

def print_pdf(excel, file):

    output_pdf = file.with_name("CIPL.pdf")

    try:
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
        return output_pdf

    except Exception as e:
        status = f"ERROR: {e}" 

def choose_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)

def open_ctu_modal(self):
    root = tk.Toplevel(self.master)
    root.iconbitmap(get_resource_path("resources/ctu.ico"))
    root.title("CTU Printer")
    root.geometry("900x550")
    root.transient(self.master)
    root.grab_set()

    tk.Label(root, text="Selected Folder:").pack(pady=5)

    folder_entry = tk.Entry(root, width=80)
    folder_entry.pack(pady=5)

    tk.Button(root, text="Browse", command=lambda: choose_folder(folder_entry)).pack(pady=5)

    status_label = tk.Label(root, text="Status: Idle", fg="blue")
    status_label.pack(pady=10)

    run_button = tk.Button(root, text="Print CTU")
    run_button.pack(pady=10)

    # ✅ Treeview (ONLY CREATE ONCE)
    tree = ttk.Treeview(root, columns=("excel", "pdf", "status"), show="headings")
    tree.heading("excel", text="Excel File")
    tree.heading("pdf", text="PDF File")
    tree.heading("status", text="Status")

    tree.column("excel", width=250)
    tree.column("pdf", width=300)
    tree.column("status", width=100)

    tree.pack(fill="both", expand=True)

    # store full paths separately
    row_data = {}

    # ✅ Open file on double click
    def open_file(event):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)

        if not item:
            return

        data = row_data.get(item)
        if not data:
            return

        excel_path, pdf_path = data

        # column "#1" = excel, "#2" = pdf
        if column == "#1":
            if os.path.exists(excel_path):
                os.startfile(excel_path)

        elif column == "#2":
            if os.path.exists(pdf_path):
                os.startfile(pdf_path)

    tree.bind("<Double-Button-1>", open_file)

    # ✅ Retry function
    def retry_selected():
        item = tree.selection()
        if not item:
            return

        item_id = item[0]
        excel_path, _ = row_data.get(item_id, (None, None))

        if not excel_path:
            return

        try:

            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False

            try:
                output_pdf = print_pdf(excel, Path(excel_path))
            except PermissionError:
                # 🔥 show popup
                retry = ask_close_pdf()
                if not retry:
                    excel.Quit()
                    tree.item(item_id, values=(os.path.basename(excel_path), pdf_path, "Cancelled"))
                    return

            reader = PdfReader(output_pdf)
            page_count = len(reader.pages)
            status = f"Retry OK Page: {page_count}"
            tree.item(item_id, values=(os.path.basename(excel_path), output_pdf, status))
            row_data[item_id] = (excel_path, output_pdf)
            excel.Quit()

        except Exception as e:
            tree.item(item_id, values=(os.path.basename(excel_path), "", f"ERROR"))
            print(e)
        finally:
            if excel:
                excel.Quit()    

    tk.Button(root, text="Retry Selected", command=retry_selected).pack(pady=5)

    # ✅ Start batch
    def start_process():
        folder_path = folder_entry.get()
        if not folder_path:
            return

        if status_label:
            status_label.config(text=f"Start printing ctu in folder {folder_path}")

        run_button.config(state="disabled")
        tree.delete(*tree.get_children())  # clear UI
        row_data.clear()

        def task():
            def insert_row(excel_path, pdf_path, status):
                item_id = tree.insert(
                    "", "end",
                    values=(os.path.basename(excel_path), pdf_path, status)
                )
                row_data[item_id] = (excel_path, pdf_path)

            excel_to_pdf_batch(
                Path(folder_path),
                status_label=status_label,
                tree_insert_callback=insert_row  # ✅ use callback
            )

            run_button.config(state="normal")

        if status_label:
            status_label.config(text=f"Start worker thread!!!")
        threading.Thread(target=task, daemon=True).start()

    run_button.config(command=start_process)

    root.mainloop()

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)


def ask_close_pdf():
    return messagebox.askretrycancel(
        "PDF is open",
        "The PDF file is currently open.\n\nPlease close it, then click Retry."
    )
