import os
import re

def find_excel_files(folder, pattern=None):
    files = []
    for root, dirs, filenames in os.walk(folder):
        for f in filenames:
            if f.endswith(".xlsx") and not f.startswith("~$"):
                if pattern and not re.search(pattern, f):
                    continue
                files.append(os.path.join(root, f))
    return files

def get_codes(text, invoice):

    pattern = rf"-\s*{re.escape(invoice)}"
    text = re.split(pattern, text, maxsplit=1)[0]
    # remove spaces around "-"
    parts = [p.strip() for p in re.split(r'-', text)]

    # find NVL index
    try:
        i = next(i for i, p in enumerate(parts) if "NVL" in p)
    except StopIteration:
        return None, None

    # first
    if i + 1 >= len(parts):
        return None, None
#     first = f"{parts[i]}-{parts[i+1]}"
    first = f"NVL - {parts[i+1]}"

    # second: aaa or aaa-01
    if i + 2 >= len(parts):
        return first, None

    second = "-".join(parts[i+2:])

    return first, second

# print(get_codes("6. NVL - 9386 - E20260403054 - HPVN20260406006-1 - 6.4.2026 - GC - 5PK - E11- TRUCK  6TK CHUNG XE"))
#  def get_declaration_code(file_name):

#     for text in texts:
#     match = re.search(r'\bNVL\s*-\s*\d+', text)
#     if match:
#         return match.group(0)
#     return None 