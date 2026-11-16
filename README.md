# WWM Code Manager

Auto add gift codes for Where Winds Meet.

Ung dung Tkinter tu dong nhap code, quan ly lich su theo tai khoan va luu toa do tren may.

## Chay ung dung

1. Cai Python 3 tren Windows va chon tuy chon them Python vao `PATH`.
2. Mo `Chay_Tool.bat`.
3. Lan dau chay, neu thieu thu vien, ung dung se hoi co cai dat khong. Chon `Y` de cai tu `requirements.txt`; neu khong muon cai, chon `N`.
4. Sau khi kiem tra/cai dat thanh cong, file `.dependencies_installed` duoc tao de bo qua buoc kiem tra thu vien o cac lan chay sau. Dấu xác nhận có phiên bản để yêu cầu kiểm tra lại sau khi thay đổi danh sách thư viện.

Neu muon kiem tra hoac cai lai thu vien, xoa `.dependencies_installed` roi mo lai `Chay_Tool.bat`.

## Du lieu va chuc nang hien co

- `wwm_database.json` tu dong duoc tao ben canh cac file Python de luu toa do, thoi gian cho, danh sach URL, kho code va lich su tung tai khoan.
- Dung `Quản lý URL` de them/xoa cac trang HTTP/HTTPS; `Quét Code` truy cap lan luot trong luong nen, gop ma trung va luu domain nguon.
- URL bai viet Fandom dang `/wiki/Ten_trang` se duoc chuyen sang MediaWiki API cong khai (`/api.php?action=parse&prop=text&format=json`) tu dong. Cung co the nhap URL MediaWiki `api.php` neu URL co tham so `page=...`.
- Cac API rieng cua website khac khong co mot chuan chung de tu dong nhan dien; hay dung URL bai viet HTML hoac can bo sung adapter rieng theo tai lieu API cua trang do.
- Kho code co cac trang thai `new` (chua xac nhan), `valid` (da co lan nhap thanh cong) va `dead` (duoc nguoi dung danh dau het han trong `Xem kho code`). Mot lan nhap that bai chi duoc ghi nhan cho tai khoan do, khong tu dong danh dau code la het han tren moi tai khoan.
- Cua so `Kho code` co the tim kiem, loc theo trang thai/nguon/tai khoan; bam tieu de cot de sap xep. Chon nhieu dong bang Ctrl/Shift de danh dau het han hoac khoi phuc.
- Cac ma quet duoc la ma tiem nang. Parser co the nhan nham hoac bo sot ma neu trang thay doi cau truc; hay kiem tra danh sach trong `Xem kho code` va xac nhan trong game.
- Du lieu cu dung `all_codes` se duoc chuyen sang `code_pool` khi mo lan dau sau cap nhat; lich su tai khoan duoc giu lai.
- Thu muc `origin` chua ban script cu, khong phai diem vao chay chinh. Ung dung hien tai duoc khoi dong bang `main.py`.

Neu `wwm_database.json` bi hong, ung dung se bao loi thay vi tu dong ghi de bang du lieu mac dinh. Hay sua hoac khoi phuc file tu ban sao luu.
