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

def get_codes(text):
    # remove spaces around "-"
    parts = [p.strip() for p in re.split(r'-', text)]

    # find NVL index
    try:
        i = next(i for i, p in enumerate(parts) if "NVL" in p)
    except StopIteration:
        return None, None

    # first
    first = f"NVL - {parts[i+1]}"

    # second
    if i + 2 >= len(parts):
        return first, None
    second = parts[i+2]

    # third
    if i + 3 >= len(parts):
        return first, second

    # special case: second contains split code
    if re.fullmatch(r'\d+', parts[i+3]):
        return first, f"{second}-{parts[i+3]}"

    return first, second

# print(get_codes("6. NVL - 9386 - E20260403054 - HPVN20260406006-1 - 6.4.2026 - GC - 5PK - E11- TRUCK  6TK CHUNG XE"))
#  def get_declaration_code(file_name):

#     for text in texts:
#     match = re.search(r'\bNVL\s*-\s*\d+', text)
#     if match:
#         return match.group(0)
#     return None 