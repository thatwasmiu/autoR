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
    terms = []
    dates = []

    for f in files:
        ws = get_workbook(f)
        declareCode = find_value(ws, "Số tờ khai")
        typeCode = find_value(ws, "Mã loại hình", r"[A-Z0-9]+")
        routeType = find_value(ws, "Mã phân loại kiểm tra", r"\d")
        term = find_value(ws, "Tổng trị giá hóa đơn")
        date = find_value(ws, "Ngày đăng ký")

        if declareCode:
            declare_codes.append(str(declareCode))
        if typeCode:
            type_codes.append(str(typeCode))
        if routeType:
            route_types.append(str(routeType))   
        if term:
            terms.append(str(term))  
        if date: 
            dates.append(str(date))    

    declareCode = pick_value(declare_codes, folder)
    typeCode = pick_value(type_codes, folder)
    routeType = pick_value(route_types, folder)
    # print(terms)
    # print(dates)
    term = pick_value(terms, folder)
    # date = pick_value(dates, folder)

    # print(route_types)
    return {
        "nvlCode": nvlCode,
        "bill": bill,
        "invoice": invoice,
        "declareCode": declareCode,
        "routeType": routeType,
        "term": term,
        "date": date
    }

def pick_value(values, folder, format_regex=None):
    if not values:
        return None

    # keep only normal values
    values = [v for v in values if is_normal(v)]

    # NEW: transform values using regex group(0)
    if format_regex:
        pattern = re.compile(format_regex)
        new_values = []

        for v in values:
            m = pattern.search(str(v))
            if m:
                new_values.append(m.group(0))

        values = new_values

    if not values:
        return None

    counter = Counter(values)
    most_common = counter.most_common()

    # if top count > 1 → return most frequent
    if most_common[0][1] > 1:
        return most_common[0][0]

    # Find all values that appear in folder
    matched = [v for v in values if v in folder]

    if matched:
        return ";".join(matched)

    # fallback → join all
    return ";".join(values)

# Filter out special characters (keep letters, numbers, maybe _)
def is_normal(v):
    return re.fullmatch(r"[A-Za-z0-9]+", v) is not None    