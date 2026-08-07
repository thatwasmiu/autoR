import win32com.client
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import sys
import os
import tempfile
import logging
from logging.handlers import RotatingFileHandler
from tkinter import filedialog
import threading
from PyPDF2 import PdfReader
from tkinter import messagebox

# pyinstaller --clean --onefile --noconsole --name "CTU Printer" --add-data "resources/logo.ico;resources" --icon=resources/logo.ico main.py

def _log_file_path():
    # %TEMP% when frozen (built exe), next to the script when run from source.
    if getattr(sys, "frozen", False):
        base_dir = tempfile.gettempdir()
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "ctu_printer.log")


def _setup_logging():
    logger = logging.getLogger("ctu_printer")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        _log_file_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)

    # Also echo to console when run from source (no console when frozen w/ --noconsole).
    if not getattr(sys, "frozen", False):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(handler.formatter)
        logger.addHandler(stream_handler)

    return logger


log = _setup_logging()

def excel_to_pdf_batch(root, status_label=None, tree_insert_callback=None):
    import os
    import win32com.client

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    files = [
        f for f in root.rglob("*.xls*")
        if f.name.startswith("合同_发票_箱单")
    ]

    results = []  # store (excel_file, pdf_file)

    total = len(files)
    log.info(f"Batch start: {total} file(s) found under {root}")

    for idx, file in enumerate(files, 1):
        if status_label:
            status_label.config(text=f"Processing ({idx}/{total}): {file.name}")
            status_label.update_idletasks()

        try:
            output_pdf = print_pdf(excel, file)
            reader = PdfReader(output_pdf)
            page_count = len(reader.pages)
            status = f"OK Page: {page_count}"
            log.info(f"[{idx}/{total}] {file.name}: OK ({page_count} pages)")
        except Exception as e:
            output_pdf = ""
            status = f"ERROR: {e}"
            log.exception(f"[{idx}/{total}] {file.name}: failed")

        results.append((str(file), str(output_pdf), status))
        # ✅ update UI table
        if tree_insert_callback:
            tree_insert_callback(str(file), str(output_pdf), status)


    excel.Quit()

    ok_count = sum(1 for _, _, status in results if status.startswith("OK"))
    log.info(f"Batch done: {ok_count}/{total} succeeded")

    if status_label:
        status_label.config(text="✅ Done")

    return results

def print_pdf(excel, file):

    output_pdf = file.with_name("CIPL.pdf")

    wb = excel.Workbooks.Open(str(file))
    try:
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

        # xlSheetVisible == -1; hidden sheets raise a COM error if included in Select()
        visible = [name for name in ordered if wb.Worksheets(name).Visible == -1]
        if not visible:
            visible = ordered
        if len(visible) < len(ordered):
            log.info(f"{file.name}: skipping hidden sheet(s) for export: "
                      f"{[n for n in ordered if n not in visible]}")
        wb.Worksheets(visible).Select()
        wb.ActiveSheet.ExportAsFixedFormat(
            Type=0,
            Filename=str(output_pdf),
            Quality=0,
            IncludeDocProperties=True,
            IgnorePrintAreas=False,
            OpenAfterPublish=False
        )

        return output_pdf
    finally:
        try:
            wb.Close(False)
        except Exception:
            log.warning(f"Could not close workbook for {file.name}", exc_info=True)

def choose_folder(entry):
    folder = filedialog.askdirectory()
    if folder:
        entry.delete(0, tk.END)
        entry.insert(0, folder)

def run_app():
    log.info("CTU Printer started")
    root = tk.Tk()
    root.iconbitmap(get_resource_path("resources/logo.ico"))
    root.title("CTU Printer")
    root.geometry("900x550")

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

            log.info(f"Retry start: {excel_path}")

            try:
                output_pdf = print_pdf(excel, Path(excel_path))
            except PermissionError:
                # 🔥 show popup
                retry = ask_close_pdf()
                if not retry:
                    excel.Quit()
                    tree.item(item_id, values=(os.path.basename(excel_path), pdf_path, "Cancelled"))
                    log.info(f"Retry cancelled by user: {excel_path}")
                    return
                output_pdf = print_pdf(excel, Path(excel_path))

            try:
                reader = PdfReader(output_pdf)
                page_count = len(reader.pages)
                status = f"Retry OK Page: {page_count}"
                tree.item(item_id, values=(os.path.basename(excel_path), output_pdf, status))
                row_data[item_id] = (excel_path, output_pdf)
                excel.Quit()
                log.info(f"Retry OK: {excel_path} ({page_count} pages)")
            except Exception as e:
                status = f"ERROR: {e}"
                tree.item(item_id, values=(os.path.basename(excel_path), "", status))
                log.exception(f"Retry failed reading PDF for {excel_path}")

        except Exception as e:
            tree.item(item_id, values=(os.path.basename(excel_path), "", f"ERROR"))
            log.exception(f"Retry failed for {excel_path}")
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

            try:
                excel_to_pdf_batch(
                    Path(folder_path),
                    status_label=status_label,
                    tree_insert_callback=insert_row  # ✅ use callback
                )
            except Exception:
                log.exception(f"Worker thread crashed for folder {folder_path}")
                if status_label:
                    status_label.config(text="❌ Error — see ctu_printer.log")
            finally:
                run_button.config(state="normal")

        log.info(f"Starting worker thread for folder: {folder_path}")
        if status_label:
            status_label.config(text=f"Start worker thread!!!")
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

def ask_close_pdf():
    return messagebox.askretrycancel(
        "PDF is open",
        "The PDF file is currently open.\n\nPlease close it, then click Retry."
    )


# --- GUI folder picker ---
# def choose_folder():
#     root = tk.Tk()
#     root.withdraw()  # hide main window
#     folder = filedialog.askdirectory(title="Select root folder")
#     return folder

# def choose_folder():
#     shell = win32com.client.Dispatch("Shell.Application")
#     folder = shell.BrowseForFolder(0, "Chọn thư mục gốc cần in ctu", 0, 0)
#     if folder:
#         return folder.Self.Path
#     return None

# def show_status(text):
#     shell = win32com.client.Dispatch("WScript.Shell")
#     shell.Popup(text, 1, "CTU PRINTER", 64)

# if __name__ == "__main__":
#     folder = choose_folder()

#     if folder:
#         excel_to_pdf_batch(Path(folder))
#     else:
#         print("No folder selected.")
