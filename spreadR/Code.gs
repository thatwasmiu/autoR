function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const { sheetLink, editMode, data } = body;

    const ss = sheetLink
      ? SpreadsheetApp.openByUrl(sheetLink)
      : SpreadsheetApp.getActiveSpreadsheet();

    const mode = editMode || "normal";
    const errors = [];

    for (const method of Object.keys(data)) {
      const records = data[method];
      if (!records || records.length === 0) continue;

      const sheet = ss.getSheets().find(
        (s) => s.getName().toLowerCase().includes(method.toLowerCase())
      );
      if (!sheet) {
        errors.push(`Không tìm thấy sheet cho phương thức: ${method}`);
        continue;
      }

      let nvlColIndex = null;
      let stkColIndex = null;
      let ngayColIndex = null;
      let luongColIndex = null;
      if (mode === "normal" || mode === "highlight") {
        const headers = sheet.getRange(2, 1, 1, sheet.getLastColumn()).getValues()[0];
        const findCol = (label) => headers.findIndex((h) => String(h).includes(label));
        nvlColIndex   = findCol("NVL");
        stkColIndex   = findCol("报关单号");
        ngayColIndex  = findCol("申报日期");
        luongColIndex = findCol("线");
        const missing = [["NVL", nvlColIndex], ["报关单号", stkColIndex], ["申报日期", ngayColIndex], ["线", luongColIndex]]
          .filter(([, i]) => i === -1).map(([n]) => n);
        if (missing.length) {
          errors.push(`Sheet "${sheet.getName()}" thiếu cột: ${missing.join(", ")}`);
          continue;
        }
      }

      const nvlCol = nvlColIndex !== null
        ? sheet.getRange(3, nvlColIndex + 1, sheet.getLastRow() - 2, 1).getValues().flat().map((v) => String(v).replace(/\s+/g, ""))
        : null;

      for (const record of records) {
        try {
          const {
            nvlCode, bill, invoice, declareCode, typeCode,
            routeType, term, date, month, tms, formCode, isDone,
          } = record;

          if (mode === "normal" || mode === "highlight") {
            const rowIndex = nvlCol.findIndex((v) => v === String(nvlCode).replace(/\s+/g, ""));
            if (rowIndex === -1) throw new Error("Không tìm thấy mã NVL: " + nvlCode);

            const r = rowIndex + 3;

            function fmtDate(v) {
              if (!v || !(v instanceof Date)) return String(v).trim();
              const d = String(v.getDate()).padStart(2, "0");
              const m = String(v.getMonth() + 1).padStart(2, "0");
              return `${d}/${m}/${v.getFullYear()}`;
            }

            function applyCell(cell, value, label, fmt) {
              if (value === null || value === undefined || value === "") return;
              const raw = cell.getValue();
              const existing = fmt ? fmt(raw) : String(raw).trim();
              if (!raw) {
                cell.setValue(value);
                if (mode === "highlight") cell.setBackground("#4a90d9");
              } else if (mode === "highlight") {
                if (existing.toUpperCase() !== String(value).trim().toUpperCase()) {
                  cell.setBackground("#e74c3c");
                  errors.push(`[${nvlCode}] ${label}: đã có "${existing}" - truyền vào "${value}"`);
                }
              }
            }

            applyCell(sheet.getRange(r, ngayColIndex + 1), date, "Ngày", fmtDate);
            applyCell(sheet.getRange(r, stkColIndex + 1), declareCode, "STK");
            applyCell(sheet.getRange(r, luongColIndex + 1), routeType ? String(routeType).toUpperCase() : routeType, "Luồng");
          } else {
            sheet.appendRow([
              nvlCode, bill, invoice, declareCode, typeCode,
              routeType, term, date, month, tms, formCode, method, isDone,
            ]);
          }
        } catch (rowErr) {
          errors.push(`[${record.nvlCode || "?"}] ${rowErr.message}`);
        }
      }
    }

    return ContentService.createTextOutput(
      JSON.stringify({ status: "ok", errors })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "error", message: "Lỗi hệ thống: " + err.message })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
