import os
import sys
from openpyxl import load_workbook
from openpyxl.styles import Border, Side
from openpyxl.styles import Font
from datetime import datetime
import re

TEMPLATE_FILE = "resources/template_weekly.xlsx"
OUTPUT_FILE = "output.xlsx"

OUTPUT_COLUMN_MAP = {
    "date": 2,
    "nvlCode": 3,
    "bill": 4,
    "invoice": 5,
    "time": 10, 
    "routeType": 11,
    "method": 13
}

def create_weekly_report(root_folder, all_data, status_label):
    all_data = []

    if not all_data:
        status_label.config(text="⚠️ No data found")
        return

    wb = load_workbook(get_resource_path(TEMPLATE_FILE))
    sheet = wb.active
    now = datetime.today()
    sheet.title = f"T{now.month}.{now.year}"

    # 🔍 find header row
    
    status_label.config(text=f"Start printing!!!")

    header_row = find_header_row(sheet)
    row = header_row + 1

    border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    font_tnr = Font(name="Times New Roman", size=10) 
    for row_dict in all_data:
        for k, col_idx in OUTPUT_COLUMN_MAP.items():
            value = row_dict.get(k)

            cell = sheet.cell(row=row, column=col_idx)

            if k == "date":
                dt = parse_date(value)
                cell.value = dt
                if dt:
                    cell.number_format = "D/M/YYYY"
            if k == "method" and value != None and value.upper() == "TRUCK":      
                cell.value = ""
            else:
                cell.value = value

        for col in range(1, 14):
            cell = sheet.cell(row=row, column=col)
            cell.border = border
            cell.font = font_tnr   # ✅ apply Times New Roman
    now = datetime.now()
    timestamp = f"T{now.isocalendar().week:02d}_{now.strftime('%Y')}"
    output_file = root_folder / f"BC_{timestamp}_{now.strftime('%H%M%S')}.xlsx"
    status_label.config(text=f"✅ Done! Saved: {str(output_file)}")
    wb.save(output_file)
    os.startfile(output_file)

def parse_date(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    # try common formats
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except:
            continue

    return None  # fallback

def find_header_row(sheet, keyword="STT"):
    for row in sheet.iter_rows():
        for cell in row:
            if str(cell.value).strip().upper() == keyword:
                return cell.row
    return None

def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)    