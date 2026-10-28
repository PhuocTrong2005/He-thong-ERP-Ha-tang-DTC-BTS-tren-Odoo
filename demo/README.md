# Demo hợp đồng BTS local

Odoo 17 Community thật, PostgreSQL 15, Mailpit và nginx; chỉ cài hai module custom
`dtc_bts_base`, `dtc_bts_contract` cùng dependency chuẩn. Không sửa source nghiệp vụ,
không cài Kho/Bảo trì. Tất cả lệnh dưới đây chạy từ **thư mục gốc repo**.

- [Vai trò, dữ liệu và hai kịch bản chi tiết](DEMO_ROLES_AND_SCENARIOS_VI.md)
- [Nhắc nhanh khoảng một trang](DEMO_CHEAT_SHEET_VI.md)
- [File TÀI LIỆU DEMO để upload](DEMO-document.txt)

## Dựng trên máy khác, không cần dump

Yêu cầu: Docker Engine/Desktop đang chạy, Docker Compose v2+ và PowerShell
(Windows PowerShell 5.1 hoặc PowerShell 7). Cổng 8079/8025 phải trống.
Trên Linux/macOS dùng `pwsh` thay `powershell -NoProfile -ExecutionPolicy Bypass`.
Clone repo và checkout nhánh `demo/contract-local`, rồi chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File demo/prepare.ps1
docker compose --env-file demo/.local/.env -f demo/compose.yml up -d db mailpit
docker compose --env-file demo/.local/.env -f demo/compose.yml run --rm --no-deps odoo odoo -c /etc/odoo/odoo.conf -d bts_contract_demo -i dtc_bts_contract --without-demo=all --stop-after-init
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Start
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Seed
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Verify
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Finalize
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 BindViews
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Exceptions
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Inspect
```

Chờ từng lệnh hoàn tất thành công trước khi chạy lệnh sau. Đây là bootstrap cho
**database mới**, không phải lệnh reset môi trường đang dùng. Nếu database đã tồn tại,
không chạy lại lệnh `-i`; dùng Status/Inspect và tiếp tục đúng bước còn thiếu.
Verify có thể tốn thời gian lần đầu trong khi Odoo tạo web assets.

`prepare.ps1` sinh mật khẩu ngẫu nhiên vào `demo/.local/credentials.json`, cấu hình
Odoo vào `demo/.local/odoo.conf` và môi trường vào `demo/.local/.env`. Nếu credentials
đã có, script giữ mật khẩu đó. Không xóa credentials khi còn dùng volume cũ.
[.env.example](.env.example) chỉ mô tả biến cần có; không dùng placeholder làm mật khẩu.
Master password được ghi trực tiếp vào `admin_passwd` trong cấu hình sinh ra, không
phụ thuộc `ODOO_MASTER_PASSWORD` chưa được compose gốc của repo truyền vào cấu hình.

## Truy cập, dữ liệu giả và tài khoản

- Odoo: <http://127.0.0.1:8079/web>; database cố định `bts_contract_demo`.
- Mailpit: <http://127.0.0.1:8025>; chỉ nhận email local.
- `ksgs.demo` / `bgd.demo` / `infra.demo`: vai trò nghiệp vụ riêng, không có System Administrator.
- `admin.demo`: tài khoản kỹ thuật; không dùng thay actor nghiệp vụ.
- Xem mật khẩu bằng lệnh Accounts bên dưới; không có mật khẩu cố định trong Git.

Sau bootstrap, LIVE còn dự thảo, TESTED đã qua hai giai đoạn OTP/gia hạn thật,
PENDING có batch GĐ1 chờ BGĐ ký 0/2, PRACTICE là hồ sơ gia hạn đất dự thảo.
Exceptions thêm bộ thiếu hồ sơ EXCEPTION và bộ REJECT chờ từ chối, không reset bộ đã có.
Ngày tính theo giờ Việt Nam khi seed lần đầu; chạy lại không dịch ngày của hồ sơ đã ký.
Không gán trực tiếp trạng thái đã ký: Verify lấy OTP mới từ Mailpit và gọi workflow chuẩn.

Các bộ REHEARSAL/bằng chứng UI đã dùng ở máy ban đầu không được sao chép vào Git;
trên máy khác Verify tái tạo bằng chứng tương đương trên bộ TESTED. Các ID/ngày/mã batch
trong hai tài liệu kịch bản là **snapshot lịch sử**, không được hard-code để seed.
Inspect in mã, trạng thái, ID và URL của database hiện tại, không in mật khẩu/OTP.
File mẫu dùng đường dẫn tương đối `demo/DEMO-document.txt`; trên PowerShell lấy đường
dẫn tuyệt đối để chọn upload bằng `Resolve-Path demo/DEMO-document.txt`.

## Vận hành và kiểm tra an toàn

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Status
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Inspect
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Accounts
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Logs
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Restart
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Stop
powershell -NoProfile -ExecutionPolicy Bypass -File demo/manage.ps1 Start
```

Stop giữ dữ liệu; không dùng `down -v`, prune hoặc script reset. Compose project riêng
`bts-contract-demo`, volumes riêng `bts-contract-demo_db-data`, `web-data`, `mail-data`
(đều có prefix project). Không dùng compose gốc cho các lệnh demo.

Inspect chỉ đọc qua ORM rồi rollback: kiểm tra view binding, SMTP Mailpit, các user
nghiệp vụ không có nhóm System và liệt kê dữ liệu DEMO. **Inspect không phải Verify**:
Verify thực sự chuyển trạng thái bộ TESTED và gửi email OTP. Không chạy Verify để
kiểm tra trạng thái bộ dữ liệu mà bạn muốn giữ nguyên trước phỏng vấn.
Seed/Finalize/Exceptions là lệnh chuẩn bị dữ liệu, không phải kiểm tra chỉ đọc.

Odoo/PostgreSQL/Mailpit chỉ nối mạng Docker `internal`. Chỉ proxy có thêm mạng frontend,
chỉ bind 127.0.0.1:8079 và 127.0.0.1:8025; không công bố PostgreSQL/SMTP.
Odoo chỉ dùng SMTP `mailpit:1025`, không có đường ra Internet. User demo gốc trong module
có thể mang email khác, nhưng mọi thư của môi trường demo vẫn chỉ vào catcher local.

## Tái hiện sửa cấu hình chọn form

Action Danh sách dự án của base không chỉ định form, nên Odoo có thể chọn nhầm form
theo dõi hạn từ module hợp đồng. [bind_project_views.py](bind_project_views.py) gắn rõ
tree/form BTS **đã có sẵn** vào action, không thay đổi ACL/constraint/workflow.

- Chỉ chạy khi database là `bts_contract_demo`, sai tên sẽ dừng.
- Chạy lại không tạo trùng; gặp binding khác với dự kiến sẽ dừng, không ghi đè.
- XML ID cấu hình nằm trong namespace `bts_local_demo.project_action_tree/form`.
- Chạy BindViews rồi Inspect; Inspect phải báo `view_binding: OK`.
- Kiểm tra UI: KSGS → Quản lý dự án BTS → Danh sách dự án → DEMO-LIVE;
  phải có tab **Hợp đồng trạm** và nút **Gửi BGĐ ký số**. Chỉ xem, chưa bấm gửi.

Không cần và không phân phối database dump để tái hiện việc này.

## Kiểm thử và giới hạn

Đã kiểm thử trên máy local: cài riêng base/contract, đăng nhập ba vai trò qua HTTP/Chrome,
ký OTP thật hai giai đoạn, kiểm tra quyền và nghiệp vụ bị chặn, xác nhận gia hạn không
OTP, cập nhật hợp đồng gốc và nhắc hạn. Hồ sơ diễn tập tách khỏi LIVE/PENDING/PRACTICE.
Khi chuẩn bị PR chỉ kiểm tra chỉ đọc trên môi trường người dùng; thử bootstrap/workflow
trên project validation riêng. Không chạy lại workflow trên các bộ đang dành để demo.

Batch dùng OTP 5 phút/5 lần thử theo source; gia hạn tải file và xác nhận, không OTP.
Đây là xác nhận nội bộ, không phải chữ ký số được chứng thực bên ngoài. Chưa kiểm thử
đầy đủ chờ hết hạn OTP, khóa đủ 5 lần, mọi tổ hợp ACL, cron tự chạy và toàn bộ nhánh hủy.
Tiền tệ mặc định USD; số tiền là dữ liệu giả, không phải đơn giá thực/VND.
Không cài menu visibility nên vẫn có một số ứng dụng Odoo chuẩn.

Tùy chọn kiểm tra Chrome trên host (cần Python, Chrome, WebDriver tương thích):

```powershell
python -m pip install -r demo/requirements-browser.txt
python demo/browser_check.py
python demo/open_demo.py
```

Ảnh, báo cáo và hồ sơ Chrome chỉ lưu trong `demo/.local/`. Browser check dùng dữ liệu
đang có và cần bộ PENDING/PRACTICE còn sẵn; không phải phép thử tổng quát sau khi bạn đã
dùng hết bộ phỏng vấn. Compose không yêu cầu các gói Python trên host để chạy Odoo.

## Những gì không nằm trong Git

Mật khẩu, `.env` thật, cấu hình có password, OTP, email Mailpit, database/filestore,
ảnh/báo cáo kiểm thử, hồ sơ Chrome và dữ liệu runtime chỉ nằm trong `.local/` hoặc
Docker volumes. Git chỉ chứa source, mẫu môi trường, tài liệu và script sinh dữ liệu giả.
`schema_odoo.sql` là dump đã có trên main từ trước, không được thêm/sửa trong thay đổi demo
và không được dùng để bootstrap. Không copy dump hay `.local/` vào commit.
