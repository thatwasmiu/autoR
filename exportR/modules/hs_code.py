import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# URL web app Apps Script (ggl/Code.gs), dạng https://script.google.com/macros/s/<ID>/exec
# Để trống thì app sẽ hỏi và ghi nhớ khi bấm "Đồng bộ từ Sheet".
DEFAULT_SHEET_URL = "https://script.google.com/macros/s/AKfycbzB-bHXpeZSHxLY3dGdeyTpEnmNCoDvPyvV7oO8tTWIv3BqbacUOewhhTtNlqdOUZjL/exec"
SHEET_TIMEOUT = 20

APP_DIR = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "exportR"
CACHE_FILE = APP_DIR / "hs_code.json"       # bản đồng bộ từ Google Sheet
SETTINGS_FILE = APP_DIR / "settings.json"   # URL đã lưu


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


def bundled_hs_code_path():
    """Đường dẫn file cấu hình đi kèm app (resources/hs_code.json)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "resources" / "hs_code.json"
    return Path(__file__).resolve().parent.parent / "resources" / "hs_code.json"


def load_active_hs_codes():
    """Ưu tiên bản đồng bộ từ Sheet, không có (hoặc hỏng) thì dùng cấu hình trong máy."""
    if CACHE_FILE.exists():
        try:
            return load_hs_codes(CACHE_FILE)
        except (OSError, ValueError):
            pass
    return load_hs_codes(bundled_hs_code_path())


def list_active_hs_codes():
    """Danh sách mã HS đang dùng, giữ nguyên định dạng trong file."""
    paths = [CACHE_FILE, bundled_hs_code_path()] if CACHE_FILE.exists() else [bundled_hs_code_path()]
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        return [str(code).strip() for code in data.get("hs_codes", []) if str(code).strip()]
    return []


def describe_hs_codes():
    """Mô tả nguồn mã HS đang dùng: {source, count, synced_at, url}."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "source": "sheet",
                "count": len(data.get("hs_codes", [])),
                "synced_at": data.get("synced_at", ""),
                "url": data.get("source_url", ""),
            }
        except (OSError, ValueError):
            pass
    try:
        count = len(load_hs_codes(bundled_hs_code_path()))
    except (OSError, ValueError):
        count = 0
    return {"source": "local", "count": count, "synced_at": "", "url": ""}


def get_sheet_url():
    url = os.getenv("EXPORTR_HS_URL")
    if url:
        return url.strip()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return str(json.load(f).get("hs_sheet_url") or DEFAULT_SHEET_URL).strip()
    except (OSError, ValueError):
        return DEFAULT_SHEET_URL


def set_sheet_url(url):
    settings = {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except (OSError, ValueError):
        settings = {}
    settings["hs_sheet_url"] = str(url).strip()
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def sync_hs_codes_from_sheet(url=None):
    """Tải mã HS từ web app Apps Script và lưu vào cache. Trả về danh sách mã."""
    url = (url or get_sheet_url()).strip()
    if not url:
        raise ValueError("Chưa cấu hình URL Google Sheet.")

    request = urllib.request.Request(url, headers={"User-Agent": "exportR"})
    with urllib.request.urlopen(request, timeout=SHEET_TIMEOUT) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("error"):
        raise ValueError(payload["error"])

    codes = [str(c).strip() for c in payload.get("hs_codes") or [] if str(c).strip()]
    if not codes:
        raise ValueError("Sheet không có mã HS nào.")

    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "hs_codes": codes,
                "synced_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "source_url": url,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return codes


def reset_hs_codes():
    """Xoá bản đồng bộ để quay về cấu hình trong máy. True nếu có xoá."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        return True
    return False
