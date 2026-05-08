import re
from collections import Counter
from datetime import datetime
from modules import (
    get_workbook,
    find_values,
    find_excel_files,
    get_codes
)

switch = {
    '1': "AIR",
    '2': "SEA",
    '3': "SEA",
    '4': "TRUCK"
}

patterns = {
    "declareCode": {
        "kw": "Số tờ khai",
        "regex": None,
        "files": [r"ToKhai.*_\d+"],
        "sheets": None
    },
    "typeCode": {
        "kw": "Mã loại hình",
        # "regex": r"[A-Z0-9]+",
        "regex": None,
        "files": [r"ToKhai.*_\d+"],
        "sheets": None
    },
    "routeType": {
        "kw": "Mã phân loại kiểm tra",
        "regex": r"\d",
        "files": [r"ToKhai.*_\d+"],
        "sheets": None
    },
    "term": {
        "kw": "Tổng trị giá hóa đơn",
        "regex": None,
        "files": [r"ToKhai.*_\d+"],
        "sheets": None
    },
    "date": {
        "kw": "Ngày đăng ký",
        "regex": None,
        "files": [r"ToKhai.*_\d+"],
        "sheets": None
    },
    "invoice": {
        "kw": "NO.",
        "regex": None,
        "files": [r"合同_发票_箱单.*"],
        "sheets": ['INVForm']
    },
    "method": {
        "kw": "Ship By:",
        "regex": r"(?i)(air|truck|sea)",
        "files": [r"合同_发票_箱单.*"],
        "sheets": None
    },
}

def get_data(daily_invoice_folder):
    # folder = r"C:\Users\datnt4\Documents\06.04\1. NVL - 9365 - E20260403058  - LENOVOVN20260406003 - 6.4.2026 - GC - 2PK - E11- TRUCK"
    folder = str(daily_invoice_folder)

    fromCode = get_form_code(daily_invoice_folder.name)
    # print(nvlCode, bill, invoice)
    # return

    files = find_excel_files(folder)

    declare_codes = []
    type_codes = []
    route_types = []
    terms = []
    dates = []
    tmses = []
    invoices = []
    methods = []

    for f in files:
        try:
            values = find_values(f, patterns)
        except:
            print(f"Error with file: {f}")
            continue
            
        if values["declareCode"]:
            declare_codes.append(values["declareCode"].strip())
        if values["typeCode"]:
            type_codes.append(values["typeCode"].strip())
        if values["routeType"]:
            route_types.append(values["routeType"].strip())
        if values["term"]:
            terms.append(values["term"].strip())
        if values["date"]:
            dates.append(values["date"].strip())
        if values["invoice"]:
            invoices.append(values["invoice"].strip())
        if values["method"]:
            methods.append(values["method"].strip().upper())

        if "合同_发票_箱单" in f:
            tms = get_tms_code(f)
            if tms:
                tmses.append(tms)   

    declareCode = pick_value(declare_codes, folder, r"[A-Za-z0-9]+")
    typeCode = pick_value(type_codes, folder, r"[A-Za-z0-9]+")
    routeType = pick_value(route_types, folder, r"[A-Za-z0-9]+")
    term = pick_value(terms, folder, r'^\s*[^-]+\s*-\s*([^-]+)\s*-', 1)
    date = pick_value(dates, folder, r'\b(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4} ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\b')
    tms = pick_value(tmses)
    invoice = pick_value(invoices, folder)
    method = pick_value(type_codes, folder, r'(\d+)\s*(?=\[)', 1)
    method_str = pick_value(methods, folder)

    nvlCode, bill = get_codes(daily_invoice_folder.name, invoice)
    month = None
    if date:
        try:
            month = datetime.strptime(date, "%d/%m/%Y %H:%M:%S").month
        except (ValueError, TypeError):
            print("Error date: ", date)

    print("method ", method, method_str)
    if method:
        method = switch.get(method.strip(), method_str)  # map to AIR/SEA/TRUCK or keep original if not in switch

    print(method)
    return {
        "nvlCode": nvlCode,
        "bill": bill,
        "invoice": invoice,
        "declareCode": declareCode,
        "typeCode": typeCode,
        "routeType": routeType,
        "term": term,
        "date": date,
        "month": month,
        "tms": tms,
        "formCode": fromCode,
        "method": method
    }

def get_form_code(folder_name): 
    parts = [p.strip() for p in folder_name.split("-")]

    for p in parts:
        if p == "GC" or p == "CX":
            return p
    return "GC"

def get_tms_code(file_name):
    m = re.search(r'(?<=合同_发票_箱单_)I\d+', file_name)

    if m:
        return m.group(0).strip()
    return None

def pick_value(values, folder=None, format_regex=None, group_index=0):
    if not values:
        return None

    # NEW: transform values using regex group(0)
    if format_regex:
        pattern = re.compile(format_regex)
        new_values = []

        for v in values:
            m = pattern.search(str(v))
            if m:
                new_values.append(m.group(group_index))

        values = new_values

    if not values:
        return None

    # keep only normal values
    # values = [v for v in values if is_normal(v)]

    counter = Counter(values)
    most_common = counter.most_common()

    # if top count > 1 → return most frequent
    if most_common[0][1] > 1:
        return most_common[0][0]

    # Find all values that appear in 
    if folder:
        matched = [v for v in values if v in folder]
        if matched:
            return ";".join(matched)

    # fallback → join all
    return ";".join(values)

# Filter out special characters (keep letters, numbers, maybe _)
def is_normal(v):
    return re.fullmatch(r"[A-Za-z0-9]+", v) is not None    