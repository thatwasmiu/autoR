# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Windows-only automation toolkit with two independent projects:

- **`autokhai/`** — UI automation scripts that drive Windows desktop apps via `pywinauto`
- **`ctu/`** — CTU Printer, a Tkinter GUI app that batch-converts Excel files to PDF via Excel COM automation (`win32com.client`)
- **`checkUI/check.py`** — standalone UI inspector: connects to a running app by title and dumps its control tree

## Running scripts

```powershell
# Run any script directly
python autokhai/autokhai.py
python checkUI/check.py
python ctu/main.py
```

Scripts require the target application to already be running (pywinauto connects to existing windows by title regex).

## Building executables (PyInstaller)

**autokhai HTA launcher** (two-step — internal exe must be built first):
```powershell
cd autokhai/hta
pyinstaller --onefile autokhai_internal.py
pyinstaller --onefile --add-binary ".\dist\autokhai_internal.exe;." autokhai_launcher.py
```

**CTU Printer** (from `ctu/`):
```powershell
cd ctu
pyinstaller --clean --onefile --noconsole --name "CTU Printer" --add-data "resources/logo.ico;resources" --icon=resources/logo.ico main.py
```

Alternatively, use the `.spec` files:
```powershell
pyinstaller autokhai_internal.spec
pyinstaller CTU_PRINTER.spec
```

## Architecture

### autokhai — layered delivery approaches

The `autokhai/` folder contains several prototype approaches for delivering a UI automation action to end-users who don't have Python:

| Subfolder | Approach |
|---|---|
| `hta/` | **Production pattern**: `autokhai_launcher.exe` writes a `.hta` file to `%TEMP%` and opens it via `mshta.exe`. The HTA button runs `autokhai_internal.exe` (bundled inside the launcher). Gives a native-looking Windows button without Python. |
| `ctypes/` | Uses `ctypes.windll.user32.MessageBoxW` for a confirm dialog before running automation. |
| `tkinter/` | Tkinter multi-button dialog helper (`ask_four_options`). |
| `main/` | Reference/scratchpad version. |

All automation uses `pywinauto` with `backend="uia"` and connects to windows by `title_re` regex.

### ctu/main.py — CTU Printer flow

1. User picks a root folder via GUI
2. Worker thread (daemon) recursively finds all `*.xls*` files whose name starts with `合同_发票_箱单`
3. For each file: opens via Excel COM, reorders sheets (`INVForm` first, then `PackingList`, then rest), sets each sheet to fit-to-1-page portrait, exports all sheets as a single `CIPL.pdf` alongside the source file
4. Results shown in a `ttk.Treeview`; double-click opens the Excel or PDF; "Retry Selected" re-processes a failed row
5. `get_resource_path()` handles PyInstaller's `_MEIPASS` temp path for bundled resources (icon)

### checkUI/check.py — UI Inspector

Tkinter app that calls `dlg.print_control_identifiers()` on a connected window and streams the output to a scrolled text widget (via `sys.stdout` redirect). Used to discover `auto_id` / `control_type` values needed when writing new pywinauto scripts.

## Dependencies

- `pywinauto` — Windows UI automation (UIA backend)
- `pywin32` (`win32com.client`) — Excel COM automation
- `PyPDF2` — read PDF page counts after export
- `tkinter` — bundled with CPython; run `ctu/test.py` to verify it's available
- `pyinstaller` — packaging to `.exe`
