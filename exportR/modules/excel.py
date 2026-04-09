from openpyxl import load_workbook
import re

def find_value(ws, keyword, match=None):
    pattern = re.compile(match, re.IGNORECASE) if match else None

    for row in ws.iter_rows():
        for cell in row:
            if cell.value and keyword.lower() in str(cell.value).lower():
                for col in range(cell.column + 1, cell.column + 8):
                    val = ws.cell(row=cell.row, column=col).value
                    if val:
                        # if keyword in "Mã phân loại kiểm tra":
                        #     print(val)
                        if pattern:
                            m = pattern.search(str(val))
                            # if keyword in "Mã phân loại kiểm tra":
                            #     print(m.group(0))
                            if m:
                                return m.group(0).strip()
                        else:
                            return str(val).strip()
    return None



def get_workbook(file_path):
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active
    return ws