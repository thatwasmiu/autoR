# ggl — Apps Script web app cho HS CODE

Trả về danh sách HS code từ sheet `HS CODE` theo đúng định dạng của
`exportR/resources/hs_code.json`.

## Triển khai

1. Mở Google Sheet chứa sheet tên `HS CODE` → **Extensions ▸ Apps Script**
   (hoặc tạo script độc lập tại https://script.google.com).
2. Dán nội dung `Code.gs`. Nếu bật "Show appsscript.json", dán luôn `appsscript.json`.
   Sửa dòng đầu file cho trỏ đúng Sheet:

   ```js
   const SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/<ID>/edit";
   ```

   Điền cả link đầy đủ hoặc chỉ `<ID>` đều được. Để trống `""` nếu script
   được gắn trực tiếp vào chính file Sheet đó.
3. **Deploy ▸ New deployment ▸ Web app**
   - Execute as: **Me**
   - Who has access: **Anyone** (hoặc Anyone with Google account nếu cần hạn chế)
4. Copy URL `https://script.google.com/macros/s/<ID>/exec`.

## Gọi

```
GET <exec-url>
GET <exec-url>?sheet=HS%20CODE
GET <exec-url>?sheetLink=<url-spreadsheet-khac>   # ghi đè SPREADSHEET_URL
```

Kết quả:

```json
{ "hs_codes": ["8471.30.90", "8471.41.90", "8523.51.11"] }
```

Lỗi trả về HTTP 200 kèm `{"hs_codes": [], "error": "..."}`.

## Quy tắc đọc

- Chỉ đọc **cột đầu tiên (cột A)** của sheet, từ dòng 1 đến dòng cuối.
  Các cột khác (mô tả, ghi chú...) được bỏ qua hoàn toàn.
- Ô là HS code khi có 4–12 chữ số, cho phép dấu chấm/phẩy/khoảng trắng.
  Ô chữ (kể cả dòng tiêu đề) tự động bị bỏ qua — không cần đặt tên tiêu đề.
- Giữ thứ tự xuất hiện, tự loại trùng.
- Ô không có dấu chấm (`84713090`) được chấm lại theo nhóm 4-2-2 → `8471.30.90`.

## Dùng trong Python

`exportR/modules/hs_code.py` đọc key `hs_codes`, nên có thể thay
`load_hs_codes(path)` bằng nội dung tải từ URL này:

```python
import json, urllib.request
from modules import normalize_code

with urllib.request.urlopen(EXEC_URL) as r:
    data = json.load(r)
hs_codes = {normalize_code(c) for c in data.get("hs_codes", [])}
```
