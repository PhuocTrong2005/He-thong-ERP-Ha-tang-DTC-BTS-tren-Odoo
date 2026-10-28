# Nhắc nhanh demo BTS — 7–10 phút

> Đây là snapshot đã kiểm chứng ngày 28/10/2026 trên máy ban đầu. ID, mã batch tự sinh, ngày và URL có ID có thể khác trên máy mới. Dùng `Inspect` trong [README](README.md) để lấy mã/ID/URL hiện tại; seed tính ngày tương đối khi tạo lần đầu. Những bộ DIỄN TẬP đã ký trong mô tả là bằng chứng lịch sử local, không được phân phối bằng dump. File mẫu nằm tại `demo/DEMO-document.txt` tính từ thư mục gốc repo; trong hộp chọn file Windows dùng đường dẫn do `Resolve-Path demo/DEMO-document.txt` trả về.

**Odoo:** <http://127.0.0.1:8079/web> · **Mailpit:** <http://127.0.0.1:8025> · **DB:** `bts_contract_demo`
**Mật khẩu:** `demo/.local/credentials.json`, khóa `ksgs` / `bgd` / `infra`. Đổi user qua avatar → **Đăng xuất**; các tab Odoo cùng Chrome dùng chung phiên.
**File F:** `demo/DEMO-document.txt`.

| Phút / đổi user | Mở đúng bản ghi và thao tác | Kết quả cần chỉ ra / ý chính cần nói |
|---|---|---|
| **0–1 · `ksgs.demo`** | **Quản lý dự án BTS → Danh sách dự án → DEMO 01 - Thực hành dự thảo (`DEMO-LIVE`)**. Trạm **DEMO Trạm LIVE** → **Hồ sơ hợp đồng → Chi tiết hợp đồng / Chi tiết BB đàm phán**. Quay dự án → **Hợp đồng trạm**, chỉ nút **Gửi BGĐ ký số**, **không gửi LIVE trong bản ngắn** | `DEMO-LAND-LIVE`, `DEMO-MEMO-LIVE` còn dự thảo. “Bộ này được chuẩn bị và giao sẵn KSGS; hồ sơ ở cấp trạm, batch ở cấp dự án.” |
| **1–4 · `bgd.demo`** | **Quản lý hợp đồng BTS → Ký số hợp đồng → Batch hợp đồng ban đầu → KS-HĐ-0003**, dự án **DEMO 03 - Chờ BGĐ ký**. Mỗi dòng: **Ký số → Gửi mã OTP → Mailpit lấy mã mới gửi `bgd@demo.invalid` → Mã OTP → Xác nhận và ký số**. Lặp cho **cả HĐ và BB** | Từ 0/2 lên 2/2; từng dòng **Đã ký**, OTP **Đã sử dụng**. “Mỗi chứng từ xác nhận riêng, người lập không tự ký.” **Không upload file ở hộp OTP batch.** |
| **4–4:30 · giữ BGĐ** | Bấm **Hoàn thành batch** sau khi 2/2 ký | **Hoàn tất**, trạm chuyển đã ký thuê đất và biên bản. “Ký từng hồ sơ và hoàn tất cả đợt là hai mốc khác nhau.” Batch biến mất khỏi menu chờ là đúng |
| **4:30–5:30 · giữ BGĐ** | Mở **DEMO-LEASE-TESTED**, trạm **DEMO Trạm TESTED**; xem [batch GĐ2 KS-HĐ-0002](http://127.0.0.1:8079/web#id=2&model=bts.contract.signature.batch&view_type=form&action=243) | GĐ2 đã kiểm thử **Hoàn tất**; nghiệm thu **28/10/2026**; HĐ cho thuê trạm hết **11/11/2026**, liên kết đất TESTED hết **12/11/2026**. “Phải có nghiệm thu; thuê đất liên quan phải cùng trạm.” |
| **5:30–7:15 · `infra.demo`** | **Tổng quan**: HĐ `DEMO-LAND-TESTED` còn **15 ngày** tại 28/10. Xem đồng hồ **Hoạt động**/chatter HĐ. **Gia hạn hợp đồng → DEMO-RENEWAL-PRACTICE → Bắt đầu thực hiện**. Ngày ký/hiệu lực mới **28/10/2026**; hết hạn **12/11/2027**; giá **13000000**; upload F vào **File scan gia hạn từ Tổ hạ tầng** → **Gửi BGĐ ký số** | Gia hạn **Chờ BGĐ ký số**, HĐ gốc chưa đổi. “Tổ hạ tầng theo dõi hạn, thương lượng và đề xuất, BGĐ ra quyết định.” |
| **7:15–8:30 · `bgd.demo`** | **Ký số hợp đồng → Hợp đồng gia hạn chờ ký → DEMO-RENEWAL-PRACTICE**. Upload F vào **Hồ sơ gia hạn đã ký số** → **Ký số / xác nhận ký** | **Hoàn thành**, có người/ngày ký. “Gia hạn này xác nhận file, **không có OTP**; không phải chứng thực chữ ký số bên ngoài.” |
| **8:30–9:30 · `infra.demo`** | Mở lại **DEMO-LAND-TESTED** → **Lịch sử gia hạn**, vùng **Hoạt động**, rồi **Tổng quan** | Hạn **12/11/2027**, giá **13000000 USD**; activity cũ đóng, chưa có activity kỳ mới vì chưa vào cửa sổ nhắc. Cho thuê TESTED vẫn hết 11/11/2026, còn cảnh báo. “Kiểm tra tác động lên dữ liệu gốc và công việc, không chỉ trạng thái ký.” |

**Phân vai cần nhớ:** GĐXN tổ chức/phân công ≠ BGĐ hợp đồng ký; KSGS chuẩn bị ban đầu ≠ Tổ hạ tầng gia hạn. `admin.demo` chỉ phục vụ kỹ thuật. Chủ đất/viễn thông là **Đối tác**, không có user thao tác trong demo. Giá hiện có là **USD ($)**, số giả; không gọi là VND.

**Ngoại lệ chọn nhanh:** KSGS gửi **DEMO-EXCEPTION** → thiếu HĐ/BB; KSGS mở **DEMO-LAND-PENDING** → đã khóa; BGĐ từ chối **KS-HĐ-0007 / DEMO TỪ CHỐI** → phải có lý do, trả hồ sơ về dự thảo. **Không dùng KS-HĐ-0003 để thử từ chối.**

**Bản đầy đủ 20–30 phút:** dùng **DEMO-LIVE**: chuẩn bị HĐ+BB → GĐ1/OTP/hoàn tất → nghiệm thu trạm → cho thuê cùng trạm → GĐ2/OTP/hoàn tất → Tổ hạ tầng lập gia hạn → BGĐ xác nhận file → kiểm tra HĐ gốc/nhắc hạn. Giá trị nhập và từng nút nằm trong mục B của tài liệu chi tiết.

**Nếu quên đường mở hoặc gặp lỗi:** [Kịch bản chi tiết, dữ liệu, quyền, thông báo thật và cách xử lý](DEMO_ROLES_AND_SCENARIOS_VI.md).
**Mở ngay:** đăng nhập `ksgs.demo` → [dự án LIVE](http://127.0.0.1:8079/web#id=2&model=project.project&view_type=form&action=223). Ngày kiểm tra **28/10/2026**; dùng lại sau nhiều tuần phải kiểm tra hạn thực tế, không reset hồ sơ đã ký.
