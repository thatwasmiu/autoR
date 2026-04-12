from openpyxl import load_workbook
from datetime import datetime, time
from openpyxl.styles import Border, Side

switch = {
    '1': "Xanh",
    '2': "Đỏ",
    '3': "Vàng"
}

def write_daily_report(template, data_list):
    wb = load_workbook(template)
    ws = wb.active

    border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    # Start index based on existing rows (excluding header)
    # start_index = 1 # assumes row 1 is header

    for i, data in enumerate(data_list, start=1):
        date_val = datetime.strptime(data.get("date"), "%d/%m/%Y") if data.get("date") else None

        ws.append([
            i + 1,   # A
            None,              # B
            data.get("nvlCode"),
            None,
            data.get("formCode"),              # GC
            date_val,          # F
            data.get("bill"),
            "HQ TELECOM",      # HQ
            data.get("declareCode"),
            switch.get(data.get("routeType"), ""),
            data.get("typeCode"),      # E11
            data.get("term"),
            data.get("invoice"),
            data.get("tms"),
        ])

        row = ws.max_row

        # Excel date format d/m/yyyy
        if date_val:
            ws.cell(row=row, column=6).number_format = "D/M/YYYY"

        # apply border A -> N
        for col in range(1, 15):
            ws.cell(row=row, column=col).border = border

    return wb