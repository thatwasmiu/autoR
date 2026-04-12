from openpyxl import load_workbook
import re

import re

def find_values(ws, patterns):
    compiled = {
        k: (kw.lower(), re.compile(p, re.IGNORECASE) if p else None)
        for k, (kw, p) in patterns.items()
    }

    results = {k: None for k in patterns}

    for row in ws.iter_rows():
        for cell in row:
            if not cell.value:
                continue

            text = str(cell.value).lower()

            for key, (keyword, pattern) in compiled.items():
                if results[key] is not None:
                    continue

                if keyword in text:
                    for col in range(cell.column + 1, cell.column + 8):
                        val = ws.cell(row=cell.row, column=col).value
                        if not val:
                            continue

                        if pattern:
                            m = pattern.search(str(val))
                            if m:
                                results[key] = m.group(0).strip()
                                break
                        else:
                            results[key] = str(val).strip()
                            break

        # stop early if all found
        if all(results.values()):
            break

    return results



def get_workbook(file_path):
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active
    return ws