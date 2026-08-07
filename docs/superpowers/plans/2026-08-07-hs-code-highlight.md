# HS Code Highlight mode for exportR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third "HS Check" mode to the exportR Tkinter app that recursively finds `CARGOES_LIST*.xlsx` files under a chosen folder and highlights column-E cells whose value matches a known HS code list.

**Architecture:** A new `exportR/modules/hs_code.py` loads/normalizes the HS code list from `exportR/resources/hs_code.json`. A new top-level `exportR/hs_code_check.py` (sibling to `weekly_report.py`/`daily_invoice.py`) discovers files via the existing `find_excel_files()`, scans column E of every sheet, applies a light-blue `PatternFill` to matches, and saves the workbook in place. `exportR/main.py` gets a third radio button wired to this orchestrator, following the exact pattern already used for the Daily/Weekly branches in `start_process()`.

**Tech Stack:** Python, `openpyxl` (already a project dependency), `tkinter` (existing GUI).

## Global Constraints

- Windows-only project; no code changes should assume a non-Windows environment.
- No pytest/test-framework infra exists in this repo — verification steps use ad hoc `python -c` / temp-script checks that print `PASS`, matching the project's existing convention (e.g. `ctu/test.py`).
- `.xlsx` only (no `.xls` support) — `find_excel_files()` already enforces this.
- Match rule: exact match after stripping `.` characters from both the HS code list and the cell value (spec: 2026-08-07-hs-code-highlight-design.md).
- Highlight fill: solid `ADD8E6` (light blue).
- Overwrite the found `CARGOES_LIST` file in place — no separate output file.
- Follow existing logger convention: `logger = logging.getLogger("exportR." + __name__)`.
- Follow existing `get_resource_path()` duplication pattern (each top-level module defines its own copy, as `weekly_report.py` and `main.py` already do) rather than introducing a new shared utils module.

---

### Task 1: HS code resource file + loader module

**Files:**
- Create: `exportR/resources/hs_code.json`
- Create: `exportR/modules/hs_code.py`
- Modify: `exportR/modules/__init__.py`

**Interfaces:**
- Consumes: nothing (new leaf module).
- Produces: `normalize_code(value) -> str` and `load_hs_codes(path: str) -> set[str]`, both exported from `modules/__init__.py`. Task 2 imports `load_hs_codes` from `modules`.

- [ ] **Step 1: Create the resource file**

Create `exportR/resources/hs_code.json`:

```json
{
  "hs_codes": [
    "8471.30.90",
    "8471.41.90",
    "8471.49.90",
    "8471.80.90",
    "8523.51.11",
    "8523.51.21",
    "8523.51.99",
    "8523.52.00",
    "8542.32.00",
    "8517.62.42",
    "8517.62.43",
    "8517.62.49",
    "8517.62.51",
    "8517.62.53",
    "8517.62.59",
    "8517.62.61",
    "8517.62.69",
    "8517.62.91",
    "8517.62.92",
    "8517.62.99",
    "8517.11.00",
    "8517.13.00",
    "8517.14.00",
    "8517.18.00",
    "8525.50.00",
    "8525.60.00",
    "8526.91.10",
    "8526.91.90",
    "8526.92.00",
    "8443.31.31",
    "8443.31.39",
    "8443.31.91",
    "8443.31.99",
    "8443.32.40"
  ]
}
```

- [ ] **Step 2: Verify the module doesn't exist yet (expected failure)**

Run (from the `exportR/` directory):
```bash
cd exportR && python -c "from modules.hs_code import normalize_code, load_hs_codes"
```
Expected: `ModuleNotFoundError: No module named 'modules.hs_code'`

- [ ] **Step 3: Implement the loader module**

Create `exportR/modules/hs_code.py`:

```python
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
```

- [ ] **Step 4: Export from the modules package**

Modify `exportR/modules/__init__.py` — add the import line so it reads:

```python
from .excel import get_workbook, find_values
from .folder import find_excel_files, get_codes
from .excel_write import write_daily_report
from .hs_code import load_hs_codes, normalize_code
```

- [ ] **Step 5: Verify it passes**

Run (from the `exportR/` directory):
```bash
cd exportR && python -c "
from modules.hs_code import normalize_code, load_hs_codes
assert normalize_code('8471.30.90') == '84713090'
assert normalize_code(84713090.0) == '84713090'
assert normalize_code(84713090) == '84713090'
assert normalize_code(None) == ''
codes = load_hs_codes('resources/hs_code.json')
assert '84713090' in codes
assert '85235111' in codes
assert len(codes) == 34
print('PASS')
"
```
Expected: `PASS`

- [ ] **Step 6: Commit**

```bash
git add exportR/resources/hs_code.json exportR/modules/hs_code.py exportR/modules/__init__.py
git commit -m "Add HS code resource list and loader module"
```

---

### Task 2: Scan-and-highlight orchestrator

**Files:**
- Create: `exportR/hs_code_check.py`

**Interfaces:**
- Consumes: `load_hs_codes(path) -> set[str]` and `normalize_code(value) -> str` from `modules` (Task 1); `find_excel_files(folder, pattern=None) -> list[str]` from `modules` (already exists — confirmed in `exportR/modules/folder.py`, exported via `modules/__init__.py`).
- Produces: `highlight_cargoes_file(file_path, hs_codes) -> int` (returns count of cells highlighted, saves in place), `run_hs_check(root_folder, status_label=None) -> None`. Task 3 imports `run_hs_check` from `hs_code_check`.

- [ ] **Step 1: Write the verification script (will fail — module doesn't exist)**

Create a temp script `exportR/_verify_hs_check.py`:

```python
import os
from openpyxl import Workbook, load_workbook
from modules import normalize_code
from hs_code_check import highlight_cargoes_file

wb = Workbook()
ws = wb.active
ws.cell(row=1, column=5, value="HS Code")       # header -> no match
ws.cell(row=2, column=5, value="8471.30.90")    # match (dotted string)
ws.cell(row=3, column=5, value="9999.99.99")    # no match
ws.cell(row=4, column=5, value=84713090)        # match (numeric, no dots)

tmp_path = os.path.abspath("_tmp_cargoes_test.xlsx")
wb.save(tmp_path)

hs_codes = {"84713090"}
highlighted = highlight_cargoes_file(tmp_path, hs_codes)
assert highlighted == 2, f"expected 2, got {highlighted}"

wb2 = load_workbook(tmp_path)
ws2 = wb2.active

def fill_hex(cell):
    return (cell.fill.fgColor.rgb or "").upper()

assert ws2.cell(row=2, column=5).fill.fill_type == "solid"
assert "ADD8E6" in fill_hex(ws2.cell(row=2, column=5))
assert "ADD8E6" in fill_hex(ws2.cell(row=4, column=5))
assert ws2.cell(row=3, column=5).fill.fill_type != "solid"

os.remove(tmp_path)
print("PASS")
```

Run:
```bash
cd exportR && python _verify_hs_check.py
```
Expected: `ModuleNotFoundError: No module named 'hs_code_check'`

- [ ] **Step 2: Implement the orchestrator**

Create `exportR/hs_code_check.py`:

```python
import os
import sys
import logging
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

from modules import find_excel_files, load_hs_codes, normalize_code

logger = logging.getLogger("exportR." + __name__)

HS_CODE_FILE = "resources/hs_code.json"
HIGHLIGHT_FILL = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")


def highlight_cargoes_file(file_path, hs_codes):
    wb = load_workbook(file_path)
    highlighted = 0

    for ws in wb.worksheets:
        for row in ws.iter_rows(min_col=5, max_col=5):
            cell = row[0]
            if cell.value is None:
                continue
            if normalize_code(cell.value) in hs_codes:
                cell.fill = HIGHLIGHT_FILL
                highlighted += 1

    if highlighted:
        wb.save(file_path)

    return highlighted


def run_hs_check(root_folder, status_label=None):
    hs_codes = load_hs_codes(get_resource_path(HS_CODE_FILE))
    files = find_excel_files(str(root_folder), pattern=r"^CARGOES_LIST")

    processed = 0
    total_highlighted = 0

    for f in files:
        if status_label:
            status_label.config(text=f"📄 Checking: {f}")
            status_label.update_idletasks()
        try:
            highlighted = highlight_cargoes_file(f, hs_codes)
            total_highlighted += highlighted
            processed += 1
            logger.info(f"Checked '{f}': highlighted {highlighted} cell(s)")
        except Exception:
            logger.exception(f"Failed to process file: {f}")

    summary = f"✅ Done. Checked {processed} file(s), highlighted {total_highlighted} cell(s)."
    if status_label:
        status_label.config(text=summary)
    logger.info(summary)


def get_resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)
```

- [ ] **Step 3: Run the verification script again**

```bash
cd exportR && python _verify_hs_check.py
```
Expected: `PASS`

- [ ] **Step 4: Delete the temp verification script**

```bash
rm exportR/_verify_hs_check.py
```
(It's a throwaway check, not a committed test — this project has no test directory convention to place it in.)

- [ ] **Step 5: Commit**

```bash
git add exportR/hs_code_check.py
git commit -m "Add CARGOES_LIST scan-and-highlight orchestrator"
```

---

### Task 3: Wire the "HS Check" mode into the UI

**Files:**
- Modify: `exportR/main.py`

**Interfaces:**
- Consumes: `run_hs_check(root_folder, status_label=None)` from `hs_code_check` (Task 2).
- Produces: nothing further downstream — this is the final integration task.

- [ ] **Step 1: Import the orchestrator**

In `exportR/main.py`, modify the import block (currently lines 12-14):

```python
from modules import write_daily_report
from daily_invoice import get_data
from weekly_report import create_weekly_report
from hs_code_check import run_hs_check
from log_config import setup_logging
```

- [ ] **Step 2: Add the third radio button**

In `exportR/main.py`, modify the radio button block (currently lines 179-183):

```python
    tk.Radiobutton(frame, text="Daily", variable=report_type, value="daily",
                   command=on_type_change).pack(side="left", padx=10)

    tk.Radiobutton(frame, text="Weekly", variable=report_type, value="weekly",
                   command=on_type_change).pack(side="left", padx=10)

    tk.Radiobutton(frame, text="HS Check", variable=report_type, value="hscheck",
                   command=on_type_change).pack(side="left", padx=10)
```

No change is needed to `on_type_change()` itself — its `else` branch (anything other than `"weekly"`) already hides `week_frame`, which is what "hscheck" needs too.

- [ ] **Step 3: Add the run branch**

In `exportR/main.py`, modify `start_process()`'s inner `task()` function (currently lines 291-306) to add an `elif` branch after the `weekly` branch:

```python
            def task():
                try:
                    if selected_type == "daily":
                        grouped = collect_daily_data(Path(folder_path), status_label)
                        status_label.config(text="✅ Đã xử lý xong. Chọn hành động tiếp theo.")
                        root.after(0, lambda: show_actions(Path(folder_path), grouped))
                    elif selected_type == "weekly":
                        from_date = from_entry.get()
                        to_date = to_entry.get()
                        logger.debug(f"Weekly report range: {from_date} -> {to_date}")
                        if (validate_date(from_date, to_date, status_label, run_button)):
                            create_weekly_report(Path(folder_path), from_date, to_date, status_label)
                    elif selected_type == "hscheck":
                        status_label.config(text="🔍 Đang quét file CARGOES_LIST…")
                        run_hs_check(Path(folder_path), status_label)
                except Exception as e:
                    logger.exception("Failed to run report")
                    status_label.config(text=f"❌ Lỗi: {e}", fg="red")
                finally:
                    run_button.config(state="normal")
```

- [ ] **Step 4: Verify imports and syntax are valid**

Run (from the `exportR/` directory — this imports `main.py` without calling `run_app()`, since it's guarded by `if __name__ == "__main__":`):

```bash
cd exportR && python -c "import main; print('PASS')"
```
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add exportR/main.py
git commit -m "Add HS Check mode to exportR UI"
```

- [ ] **Step 6: Manual end-to-end check (you)**

Not automated — per your request, you'll run `python exportR/main.py`, pick a folder containing a `CARGOES_LIST*.xlsx` file, select "HS Check", click Run, and confirm the expected column-E cells turn light blue and the file still opens correctly afterward.

---

## Packaging note (not a task — surface at build time)

When this app is next rebuilt with PyInstaller, `resources/hs_code.json` must be added to the `--add-data` args (or the `.spec` file's `datas`), same as `daily_template.xlsx` and `logo.ico` already are — otherwise the bundled `.exe` won't find it via `get_resource_path()`.
