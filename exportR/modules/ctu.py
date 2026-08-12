import logging
from pathlib import Path

import win32com.client
from PyPDF2 import PdfReader

logger = logging.getLogger("exportR." + __name__)


def print_pdf(excel, file):
    output_pdf = file.with_name("CIPL.pdf")

    wb = excel.Workbooks.Open(str(file))

    all_sheets = [sheet.Name for sheet in wb.Worksheets if sheet.Visible == -1]

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

    wb.Worksheets(ordered).Select()
    wb.ActiveSheet.ExportAsFixedFormat(
        Type=0,
        Filename=str(output_pdf),
        Quality=0,
        IncludeDocProperties=True,
        IgnorePrintAreas=False,
        OpenAfterPublish=False,
    )

    wb.Close(False)
    return output_pdf


def run_ctu_batch(root_folder, status_label=None, row_callback=None):
    root_folder = Path(root_folder)
    files = [
        f for f in root_folder.rglob("*.xls*")
        if "合同_发票_箱单" in f.name and not f.name.startswith("~$")
    ]

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    processed = 0
    failed = 0

    try:
        for idx, file in enumerate(files, 1):
            if status_label:
                status_label.config(text=f"🖨️ In CTU ({idx}/{len(files)}): {file.name}")
                status_label.update_idletasks()
            try:
                output_pdf = print_pdf(excel, file)
                page_count = len(PdfReader(output_pdf).pages)
                processed += 1
                status = f"OK Page: {page_count}"
                logger.info(f"Printed '{file}' -> '{output_pdf}' ({page_count} pages)")
            except Exception as e:
                output_pdf = ""
                failed += 1
                status = f"ERROR: {e}"
                logger.exception(f"Failed to print CTU file: {file}")

            if row_callback:
                row_callback(str(file), str(output_pdf), status)
    finally:
        excel.Quit()

    if failed:
        summary = f"⚠️ Done. Printed {processed} file(s), {failed} file(s) lỗi — xem log."
        if status_label:
            status_label.config(text=summary, fg="red")
    else:
        summary = f"✅ Done. Printed {processed} file(s)."
        if status_label:
            status_label.config(text=summary)
    logger.info(summary)
    return summary
