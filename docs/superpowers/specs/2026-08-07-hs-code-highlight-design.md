# HS Code Highlight mode for exportR

## Problem

`exportR` currently has two report modes (Daily, Weekly). We need a third mode: given a root folder, recursively find every Excel file whose name starts with `CARGOES_LIST`, check column E of each sheet against a known list of HS (customs tariff) codes, and highlight any matching cell's background in blue.

## Scope

- New "HS Check" mode in the existing `exportR` Tkinter app (`exportR/main.py`).
- New reference file `exportR/resources/hs_code.json` containing the HS code list.
- New module code to load the HS list, find target files, scan/highlight, and save.
- Out of scope: editing the HS code list from the UI, matching on columns other than E, `.xls` (legacy) support, generating any report/summary file — this mode only mutates the found `CARGOES_LIST` files in place.

## Design

### HS code list

`exportR/resources/hs_code.json`:
```json
{ "hs_codes": ["8471.30.90", "8471.41.90", "..."] }
```
Populated with the ~34 unique codes already extracted from the reference images in this conversation. Loaded via the existing `get_resource_path()` helper (same pattern as `daily_template.xlsx` / `logo.ico`), so it must be added to the PyInstaller `--add-data` args when the app is rebuilt.

`exportR/modules/hs_code.py`:
```python
def load_hs_codes(path) -> set[str]:
    # reads {"hs_codes": [...]}, strips "." from each code, returns a set
```

### File discovery

Reuse `find_excel_files(folder, pattern)` from `exportR/modules/folder.py` (already walks subfolders via `os.walk`, skips `~$` lock files, `.xlsx` only) with `pattern=r"^CARGOES_LIST"` matched against the file's basename (case-sensitive is fine — matches the exact naming convention in use).

### Matching & highlighting

For each matched file:
1. `load_workbook(path)` — **not** `data_only=True`, so any formula cells elsewhere in the file are preserved untouched on save.
2. For every worksheet, iterate all rows, read column E (`column=5`).
3. Normalize each non-empty cell value for comparison: `str(value)`, strip a trailing `.0` if the cell holds a whole-number float, then remove all `.` characters.
4. If the normalized value is in the HS code set (exact match), set `cell.fill = PatternFill("solid", fgColor="ADD8E6")` (light blue).
5. Save the workbook back to its original path (overwrite in place).

One bad file (unreadable, corrupt, locked) is logged via `logger.exception(...)` and skipped, so it doesn't abort the whole run — same pattern already used in `main.py` / `weekly_report.py`.

### UI wiring (`exportR/main.py`)

- Add a third `Radiobutton(frame, text="HS Check", variable=report_type, value="hscheck")`.
- `on_type_change()`: like Daily, hides the Weekly date-range pickers when this mode is selected.
- `start_process()`: new branch `elif selected_type == "hscheck": run_hs_check(Path(folder_path), status_label)`, run on the existing background thread — no results table/export step needed since this mode mutates files directly instead of producing a report.
- `run_hs_check(root_folder, status_label)` lives in a new top-level module `exportR/hs_code_check.py` (mirrors `weekly_report.py` / `daily_invoice.py` as separate top-level modules invoked from `main.py`), and updates `status_label` per file (`"📄 Checking: <file>"`) then with a final summary (`"✅ Done. Checked N file(s), highlighted M cell(s)."`).

## Testing

No automated test suite exists in this project. The user will test manually against a real folder containing `CARGOES_LIST*.xlsx` files.
