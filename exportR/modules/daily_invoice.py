import re
from collections import Counter
from modules import (
    get_workbook,
    find_value,
    find_excel_files,
    get_codes
)

def get_data(daily_invoice_folder):
    # folder = r"C:\Users\datnt4\Documents\06.04\1. NVL - 9365 - E20260403058  - LENOVOVN20260406003 - 6.4.2026 - GC - 2PK - E11- TRUCK"
    folder = daily_invoice_folder

    nvlCode, bill, invoice = get_codes(folder)

    files = find_excel_files(folder)

    declare_codes = []
    type_codes = []
    route_types = []

    for f in files:
        ws = get_workbook(f)
        declareCode = find_value(ws, "Số tờ khai")
        typeCode = find_value(ws, "Mã loại hình", r"[A-Z0-9]+")
        routeType = find_value(ws, "Mã phân loại kiểm tra", r"\d")

        if declareCode:
            declare_codes.append(str(declareCode))
        if typeCode:
            type_codes.append(str(typeCode))
        if routeType:
            route_types.append(str(routeType))    

    declareCode = pick_value(declare_codes, folder)
    typeCode = pick_value(type_codes, folder)
    routeType = pick_value(route_types, folder)

    return nvlCode, bill, invoice, declareCode, routeType

def pick_value(values, folder):
    if not values:
        return None

    values = [v for v in values if is_normal(v)]    

    counter = Counter(values)
    most_common = counter.most_common()

    # if top count > 1 → return most frequent
    if most_common[0][1] > 1:
        return most_common[0][0]

    # Find all values that appear in folder and are normal
    matched = [v for v in values if v in folder] 

    if matched:
        # join all matched values if multiple
        return ";".join(matched)

    # fallback → join all
    return ";".join(values)

# Filter out special characters (keep letters, numbers, maybe _)
def is_normal(v):
    return re.fullmatch(r"[A-Za-z0-9]+", v) is not None    