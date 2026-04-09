import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

from modules import (
    get_workbook,
    find_value,
    find_excel_files,
    get_codes,
    get_data,
    write_daily_report
)


folder = r"C:\Users\datnt4\Documents\06.04\1. NVL - 9365 - E20260403058  - LENOVOVN20260406003 - 6.4.2026 - GC - 2PK - E11- TRUCK"

nvlCode, bill, invoice, declareCode, routeType = get_data(folder)
write_daily_report("daily_template.xlsx", nvlCode, bill, invoice, declareCode, routeType)


