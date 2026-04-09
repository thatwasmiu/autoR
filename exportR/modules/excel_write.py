from openpyxl import load_workbook

def write_daily_report(template, nvlCode, bill, invoice, declareCode, routeType):
    # 1. load template
    wb = load_workbook(template)
    ws = wb.active


    print(nvlCode, bill, invoice, declareCode, routeType)
    last_row = ws.max_row + 1

    ws.cell(row=last_row, column=1, value=nvlCode)
    ws.cell(row=last_row, column=3, value=bill)
    ws.cell(row=last_row, column=4, value=invoice)
    ws.cell(row=last_row, column=5, value=declareCode)
    ws.cell(row=last_row, column=6, value=routeType)
    # ws.append([declareCode, typeCode])

    wb.save("output.xlsx")