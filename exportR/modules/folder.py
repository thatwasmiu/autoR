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
        return None, None, None

    # first
    first = f"NVL - {parts[i+1]}"

    # second
    if i + 2 >= len(parts):
        return first, None, None
    second = parts[i+2]

    # third
    if i + 3 >= len(parts):
        return first, second, None

    third = parts[i+3]

    # stop if date
    if re.match(r'\d{1,2}\.\d{1,2}\.\d{4}', third):
        return first, second, None

    # if third is numeric → belongs to previous
    if re.fullmatch(r'\d+', third):
        return first, second, f"{parts[i+2]}-{third}"

    # special case: second contains split code
    if re.fullmatch(r'\d+', parts[i+3]):
        return first, f"{second}-{parts[i+3]}", parts[i+4] if i+4 < len(parts) else None

    return first, second, third


#  def get_declaration_code(file_name):

#     for text in texts:
#     match = re.search(r'\bNVL\s*-\s*\d+', text)
#     if match:
#         return match.group(0)
#     return None 