import os
import re

def find_excel_files(folder):
    files = []
    for root, dirs, filenames in os.walk(folder) :
        for f in filenames:
            if f.endswith(".xlsx") and not f.startswith("~$"):
                files.append(os.path.join(root, f))
    return files



def get_codes(text):
    m = re.search(r'(\bNVL\s*-\s*\d+)\s*-\s*([^-]+)\s*-\s*([^-]+)', text)
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    return None   


#  def get_declaration_code(file_name):

#     for text in texts:
#     match = re.search(r'\bNVL\s*-\s*\d+', text)
#     if match:
#         return match.group(0)
#     return None 