/**
 * Web app: trả về danh sách HS CODE từ sheet "HS CODE" dưới dạng JSON,
 * cùng định dạng với exportR/resources/hs_code.json:
 *
 *   { "hs_codes": ["8471.30.90", "8471.41.90", ...] }
 *
 * Nguồn dữ liệu: đặt SPREADSHEET_URL bên dưới (hoặc để trống nếu script
 * gắn sẵn vào file Sheet).
 *
 * Query params (đều không bắt buộc):
 *   sheetLink : URL/ID spreadsheet khác, ghi đè SPREADSHEET_URL
 *   sheet     : tên sheet (mặc định: "HS CODE")
 *   callback  : tên hàm JSONP
 */

// ▼▼ Dán link (hoặc ID) Google Sheet chứa sheet "HS CODE" vào đây ▼▼
// vd: "https://docs.google.com/spreadsheets/d/1AbC.../edit"  hoặc  "1AbC..."
// Để trống nếu script được gắn trực tiếp vào file Sheet (Extensions ▸ Apps Script).
const SPREADSHEET_URL = "";

const DEFAULT_SHEET_NAME = "HS CODE";

function doGet(e) {
  const params = (e && e.parameter) || {};
  const callback = params.callback;

  try {
    const ss = openSpreadsheet(params.sheetLink);

    const sheetName = params.sheet || DEFAULT_SHEET_NAME;
    const sheet = findSheet(ss, sheetName);
    if (!sheet) throw new Error('Không tìm thấy sheet: "' + sheetName + '"');

    return respond({ hs_codes: readHsCodes(sheet) }, callback);
  } catch (err) {
    return respond({ hs_codes: [], error: String(err.message || err) }, callback);
  }
}

/**
 * Mở spreadsheet: ưu tiên tham số sheetLink, rồi tới SPREADSHEET_URL,
 * cuối cùng là file đang gắn script.
 */
function openSpreadsheet(sheetLink) {
  const target = String(sheetLink || SPREADSHEET_URL || "").trim();
  if (target) {
    return target.indexOf("/") !== -1
      ? SpreadsheetApp.openByUrl(target)
      : SpreadsheetApp.openById(target);
  }
  const active = SpreadsheetApp.getActiveSpreadsheet();
  if (!active) {
    throw new Error('Chưa cấu hình SPREADSHEET_URL trong Code.gs');
  }
  return active;
}

/** Tìm sheet theo tên, không phân biệt hoa thường và khoảng trắng. */
function findSheet(ss, name) {
  const wanted = normalizeName(name);
  return ss.getSheets().find((s) => normalizeName(s.getName()) === wanted) || null;
}

function normalizeName(value) {
  return String(value).replace(/[\s_-]+/g, "").toLowerCase();
}

/** Đọc cột đầu tiên (cột A) của sheet, giữ thứ tự và bỏ trùng. */
function readHsCodes(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 1) return [];

  const values = sheet.getRange(1, 1, lastRow, 1).getDisplayValues();
  const seen = {};
  const codes = [];

  for (const row of values) {
    const code = normalizeCode(row[0]);
    if (!code || seen[code]) continue;
    seen[code] = true;
    codes.push(code);
  }
  return codes;
}

/**
 * Chuẩn hoá 1 ô về dạng HS code, trả về "" nếu ô không phải HS code.
 * Chấp nhận "8471.30.90", "8471 30 90", "84713090"; bỏ tiêu đề và mô tả.
 */
function normalizeCode(value) {
  const raw = String(value == null ? "" : value).trim();
  if (!raw) return "";

  // Bỏ dấu phân cách: khoảng trắng, chấm, phẩy, nháy (Sheets có thể hiển thị 84,713,090)
  const cleaned = raw.replace(/[\s.,'’]+/g, "");
  if (!/^\d{4,12}$/.test(cleaned)) return "";

  // Giữ nguyên cách chấm của ô nếu ô đã có dấu chấm, ngược lại chấm theo nhóm 4-2-2-...
  if (raw.indexOf(".") !== -1 && raw.indexOf(",") === -1) return raw.replace(/\s+/g, "");

  const parts = [cleaned.slice(0, 4)];
  for (let i = 4; i < cleaned.length; i += 2) parts.push(cleaned.slice(i, i + 2));
  return parts.join(".");
}

function respond(payload, callback) {
  const json = JSON.stringify(payload);
  if (callback) {
    return ContentService
      .createTextOutput(callback + "(" + json + ");")
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return ContentService
    .createTextOutput(json)
    .setMimeType(ContentService.MimeType.JSON);
}
