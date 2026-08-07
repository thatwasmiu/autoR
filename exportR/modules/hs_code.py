import json


def normalize_code(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip().replace(".", "")


def load_hs_codes(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {normalize_code(code) for code in data.get("hs_codes", [])}
