from openpyxl import load_workbook

def write_daily_report(template, data_list):
    wb = load_workbook(template)
    ws = wb.active

    # Start index based on existing rows (excluding header)
    start_index = ws.max_row  # assumes row 1 is header

    for i, data in enumerate(data_list, start=1):
        print(data)
        ws.append([
            start_index + i,   # Column A: index
            None,              # Column B (skip if unused)
            data.get("nvlCode"),
            None,
            None,
            data.get("bill"),
            data.get("invoice"),
            data.get("declareCode"),
            data.get("routeType"),
        ])

    return wb