# Hướng dẫn test và import dữ liệu demo

> Kiểm tra theo working tree ngày 30/07/2026.

## 1. Mục đích và chuẩn bị

Tài liệu này dùng để chuẩn bị dữ liệu và kiểm tra các luồng đang có trong
source code: Dự án, Kho, Bảo trì và Hợp đồng BTS.

Chuẩn bị:

1. Chạy PostgreSQL và Odoo bằng `docker compose up -d`.
2. Cài hoặc upgrade các module:
   - `dtc_bts_base`
   - `dtc_bts_inventory`
   - `dtc_bts_maintenance`
   - `dtc_bts_contract`
   - `dtc_bts_menu_visibility`
3. Dùng database riêng cho demo và sao lưu trước khi import lại dữ liệu.
4. Dùng System Administrator để import nhằm tránh thiếu ACL giữa chừng.
5. Đăng xuất/đăng nhập lại từng user sau khi upgrade hoặc đổi group.

Source không đặt mật khẩu cố định cho các user demo. System Administrator
phải đặt/reset mật khẩu trước khi test. Không cộng thêm group nghiệp vụ để
“chữa” lỗi quyền.

Thứ tự import khuyến nghị:

`res.partner` → `project.project` → `project.task` → `product.template` →
`bts.contract` → `bts.maintenance.checklist.item`.

Repository hiện không chứa test tự động trong các module. Việc kiểm tra hồi quy
được thực hiện bằng checklist trong tài liệu này và các script tạo dữ liệu có
kiểm soát ở mục 3.8.

## 2. User dùng khi test

| Login | Email | Vai trò chính | Ứng dụng chính |
| --- | --- | --- | --- |
| `vydtt4947@ut.edu.vn` | `vydtt4947@ut.edu.vn` | Kỹ sư giám sát | Quản lý dự án BTS |
| `dthuyvy456@gmail.com` | `dthuyvy456@gmail.com` | Giám đốc Xí nghiệp | Quản lý dự án BTS |
| `tpkh.demo` | `tpkh.dtc.demo@gmail.com` | Trưởng phòng Kế hoạch | Kho |
| `warehouse.demo` | `tk.dtc.demo@gmail.com` | Thủ kho | Kho |
| `infrastructure.demo` | `qltht.dtc.demo@gmail.com` | Tổ quản lý hạ tầng | Bảo trì; Hợp đồng |
| `kiemtien7809@gmail.com` | `kiemtien7809@gmail.com` | Ban Giám đốc hợp đồng | Hợp đồng |
| `dtc.admin.demo` | `admin.dtc.demo@gmail.com` | Quản trị user/group/cấu hình | Settings |
| System Administrator | Theo lúc tạo database | Quản trị kỹ thuật | Toàn bộ ứng dụng |

System Administrator là tài khoản quản trị của database thuộc
`base.group_system`, không phải `dtc.admin.demo`. Tên đăng nhập cụ thể phụ
thuộc lúc tạo database.

## 3. Import dữ liệu demo

### 3.1. Quy ước chung

- Tạo cột `External ID` cho dữ liệu cần được model khác tham chiếu.
- Với quan hệ, ưu tiên cột `.../External ID` thay vì dò theo tên.
- Ngày dùng định dạng `YYYY-MM-DD`, ví dụ `2026-07-01`.
- Số thập phân dùng dấu chấm: `10.567812`, không dùng `10,567812`.
- `project_code`, `station_code`, `contract_code` không được trùng.
- Giá trị Selection nên dùng mã kỹ thuật nêu dưới đây.
- Import thử 1–2 dòng trước, sau đó mới import toàn bộ.
- File hợp đồng/biên bản ký số nên upload trên form. Không có luồng import
  file scan thân thiện cho người dùng hiện tại.

### 3.2. Đối tác — `res.partner`

Mở **Quản lý dự án BTS → Đối tác**.

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có để tham chiếu ổn định |
| `Name` | Bắt buộc |
| `partner_type` | Bắt buộc; mặc định `other` |
| `Company Type` | `company` hoặc `person` nếu cần |
| `Supplier Rank` | Đặt `1` cho nhà cung cấp dùng để tạo PO |

`partner_type` hợp lệ:

- `supplier`
- `landowner`
- `telecom_partner`
- `external_technician`
- `other`

KTV thuê ngoài hiện chỉ là đối tác, chưa có tài khoản portal/internal và
chưa nhập kết quả trực tiếp vào Odoo.

### 3.3. Dự án — `project.project`

Mở **Quản lý dự án BTS → Danh sách dự án**.

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có |
| `name` | Bắt buộc |
| `project_code` | Bắt buộc, duy nhất; bỏ trống thì sequence có thể sinh |
| `station_type` | `macro` hoặc `cell` |
| `telecom_partner_id/External ID` | Trỏ tới đối tác `telecom_partner` |
| `state` | Nên nhập rõ trạng thái test |
| `planned_start_date`, `planned_end_date` | `YYYY-MM-DD` |
| `acceptance_date` | Ngày nghiệm thu dự án; bắt buộc trước khi tạo hồ sơ bảo trì |
| `province`, `district`, `commune` | Không bắt buộc |

`state` hợp lệ:

`draft`, `survey`, `approved`, `in_progress`, `done`, `cancelled`.

Muốn dùng nút tạo yêu cầu vật tư từ dự án, dự án phải ở `approved`.

### 3.4. Trạm BTS — `project.task`

Mở **Quản lý dự án BTS → Danh sách trạm BTS**.

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có |
| `name` | Bắt buộc |
| `station_code` | Bắt buộc, duy nhất |
| `project_id/External ID` | Bắt buộc trong nghiệp vụ BTS |
| `station_state` | Nên nhập rõ trạng thái test |
| `handover_state` | Mặc định `not_handed` |
| `latitude`, `longitude` | Số decimal |
| `site_address` | Không bắt buộc |
| `acceptance_date` | Ngày nghiệm thu của trạm; cần cho HĐ cho thuê trạm |

Ràng buộc tọa độ:

- Vĩ độ: `-90` đến `90`.
- Kinh độ: `-180` đến `180`.

`station_state` chính:

`survey`, `negotiating`, `contracted`, `construction`, `acceptance`,
`station_lease_signed`, `handover`, `operating`.

`cancelled` chỉ được giữ để tương thích dữ liệu cũ.

### 3.5. Vật tư — `product.template`

Mở **Kho → Danh mục vật tư**.

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có |
| `Name` | Bắt buộc |
| `type` hoặc `detailed_type` | Dùng `product`; import cũng nhận “Hàng hóa” |
| `is_bts_material` | `TRUE` |
| `Category/External ID` | Nên có |
| `Unit of Measure` | Phải tồn tại và cùng category với UoM mua |
| `Purchase Unit of Measure` | Phải tồn tại |
| `Cost`, `Sales Price` | Nhập số, không kèm ký hiệu tiền |

Module có các đơn vị demo như `Cái`, `Bộ`, `Bao`, `Thùng`, `Bịch`, `m2`,
`m3`; nên export một dòng mẫu để lấy đúng tên cột theo ngôn ngữ database.

### 3.6. Hợp đồng — `bts.contract`

Không có menu import hợp đồng độc lập cho KSGS. Với functional demo, mở
từng trạm, vào tab **Hồ sơ hợp đồng**, tải scan rồi dùng **Chi tiết hợp
đồng** để nhập nội dung. Action này cho phép KSGS tạo/sửa hồ sơ `draft` bằng
tree/form riêng và không hiển thị nút workflow hợp đồng lẻ.

Bảng dưới cũng dùng cho technical import trực tiếp model `bts.contract`
dưới quyền System Administrator:

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có |
| `contract_code` | Bắt buộc, duy nhất |
| `contract_type` | `land_lease` hoặc `infrastructure_lease` |
| `station_id/External ID` | Bắt buộc |
| `partner_id/External ID` | Bắt buộc trước khi gửi batch |
| `state` | Nên import là `draft` |
| `effective_date`, `expiration_date` | Bắt buộc trước khi gửi batch; `YYYY-MM-DD` |
| `term_years` | Bắt buộc trước khi gửi batch; số nguyên dương |
| `sign_date` | Ngày ký trên bản giấy nếu có |
| `rental_price`, `payment_cycle` | Nhập nếu có |
| `initial_document` | File scan bắt buộc trước khi gửi batch |
| `related_land_contract_id/External ID` | Cần cho HĐ cho thuê trạm |

Quy tắc đối tác:

- `land_lease` dùng đối tác `landowner`.
- `infrastructure_lease` dùng đối tác `telecom_partner`.

Nên import HĐ thuê đất trước, sau đó HĐ cho thuê trạm. Không import thẳng
trạng thái `active` để bỏ qua ký số. Upload hồ sơ ban đầu và chạy workflow
trên giao diện mới là cách test đúng.

### 3.7. Checklist bảo trì — `bts.maintenance.checklist.item`

Mở **Quản lý bảo trì trạm BTS → Checklist mẫu**.

| Cột | Yêu cầu |
| --- | --- |
| `External ID` | Nên có |
| `name` | Bắt buộc |
| `category_id/External ID` | Bắt buộc |
| `frequency_months` | Chỉ nhận `1`, `3` hoặc `6` |
| `is_external_required` | `TRUE`/`FALSE` |
| `sequence` | Số nguyên, mặc định `10` |
| `active` | `TRUE` nếu muốn sinh vào phiếu |

Category có sẵn:

- `dtc_bts_maintenance.category_bts_macro`
- `dtc_bts_maintenance.category_bts_cell`

### 3.8. Bộ dữ liệu phân tích tự động trong `scripts/`

Các script Python dưới đây chạy trong `odoo shell`, dùng khóa nghiệp vụ ổn định
`ANL-*` và có thể chạy lại mà không chủ ý tạo trùng dữ liệu:

| Script | Mục đích | Điều kiện |
| --- | --- | --- |
| `import_analytics_demo_data.py` | Tạo 30 dự án cùng dữ liệu dashboard dự án, bảo trì và hợp đồng | Chạy đầu tiên |
| `import_inventory_demo_data.py` | Bổ sung yêu cầu, PO, receipt và delivery cho dashboard cung ứng | Chạy sau script analytics |
| `import_cancellation_workflow_demo_data.py` | Tạo dữ liệu tại các bước xem xét hủy trạm/dự án | Chạy sau script analytics; cần ít nhất 6 dự án `ANL-*` chưa hủy |
| `rebalance_project_dashboard_demo.py` | Phân bố lại trạng thái và deadline dashboard dự án | Cần đúng 30 dự án `ANL-DA-*` |

Ví dụ chạy script analytics từ thư mục gốc repository:

```bash
docker cp scripts/import_analytics_demo_data.py mis_odoo_web:/tmp/import_analytics_demo_data.py
docker compose exec -T odoo sh -lc 'odoo shell -c /etc/odoo/odoo.conf -d "$ODOO_DB_NAME" --no-http < /tmp/import_analytics_demo_data.py'
```

Thay tên file ở cả hai vị trí để chạy script tiếp theo. Không truyền nội dung
file UTF-8 qua `Get-Content` của Windows PowerShell vì có thể làm sai dấu tiếng Việt.

Các tiện ích vận hành khác:

- `repair_failed_mail_queue.py` sửa cấu hình SMTP Gmail mục tiêu, đưa toàn bộ
  mail `exception` về hàng đợi và lùi lịch gửi 26 giờ. Chỉ chạy khi đã xác nhận
  đúng mail server và chấp nhận tác động lên toàn bộ mail lỗi.
- `reset_business_data.sql` xóa dữ liệu giao dịch/demo nhưng giữ cấu hình và
  master data được liệt kê trong chính script. Đây là thao tác phá hủy dữ liệu;
  phải sao lưu database và đọc toàn bộ script trước khi chạy.
- `backup.sh` và `restore.sh` dùng các biến container/thư mục trong `.env` để
  sao lưu hoặc phục hồi database cùng filestore.

## 4. Checklist test luồng Dự án

Đăng nhập `enterprise.director.demo`:

- [ ] Chỉ thấy app **Quản lý dự án BTS**, kể cả khi bật developer mode.
- [ ] Tạo dự án, kiểm tra `enterprise_director_id` tự là GĐXN đang đăng
      nhập và `project_code` không trùng.
- [ ] Phân công `ksgs.demo`; kiểm tra KSGS nhận đúng một Activity.
- [ ] Nhập thông tin, đưa dự án về `approved`.
- [ ] Không xóa được dự án/trạm hoặc chuyển dự án sang GĐXN khác.

Đăng nhập `ksgs.demo`:

- [ ] Chỉ thấy dự án vừa được phân công.
- [ ] Không tạo, sửa hoặc xóa được dự án; trường GĐXN/KSGS chỉ đọc.
- [ ] Tạo ít nhất một trạm, nhập `station_code`, dự án và tọa độ.
- [ ] Sửa được trạm thuộc dự án nhưng không xóa được trạm.
- [ ] Bấm **Tạo yêu cầu vật tư**, thêm dòng vật tư và gửi yêu cầu.
- [ ] Sau khi kho đưa yêu cầu về `ready`, kiểm tra dashboard dự án có
      thông báo “Vật tư sẵn sàng cấp phát”.
- [ ] Bấm **Đã xem** và xác nhận thông báo không còn là chưa đọc.
- [ ] Đưa tất cả trạm về `handover` hoặc `cancelled`.
- [ ] Bấm **Bàn giao sang bảo trì**; dự án chuyển
      `maintenance_handover_state = pending`.

Nếu dự án chưa `approved`, chưa có trạm, hoặc còn trạm ngoài
`handover`/`cancelled`, hệ thống phải chặn đúng bước tương ứng.

## 5. Checklist test luồng Kho

### Trưởng phòng Kế hoạch — `tpkh.demo`

- [ ] Mở yêu cầu `requested`.
- [ ] Nhập số lượng duyệt và bấm duyệt:
      `requested` → `waiting_purchase`.
- [ ] Chọn đối tác có `partner_type = supplier`.
- [ ] Tạo PO cho toàn bộ số lượng duyệt và xác nhận theo luồng Purchase chuẩn;
      yêu cầu chuyển `purchasing`.
- [ ] Thấy menu Nhập kho/Xuất kho để theo dõi nhưng không có nút tạo phiếu.

### Thủ kho — `warehouse.demo`

- [ ] Thấy menu **Yêu cầu cấp phát**, **Đơn mua hàng**, **Nhập kho**,
      **Xuất kho**, **Danh mục vật tư**.
- [ ] Mở được Đơn mua hàng nhưng không có quyền tạo/sửa/xóa.
- [ ] Mở được Danh mục vật tư nhưng không có quyền tạo/sửa/xóa/import.
- [ ] Mở phiếu nhập liên kết dự án/yêu cầu và Validate.
- [ ] Khi tồn khả dụng đủ, kiểm tra yêu cầu chuyển `ready`.
- [ ] Từ yêu cầu, tạo phiếu xuất.
- [ ] Kiểm tra sản phẩm, đơn vị tính và lượng duyệt còn lại được tự điền;
      phiếu đã được xác nhận/giữ hàng và không còn bước **Đánh dấu việc cần làm**.
- [ ] Không cho xuất vượt số lượng được duyệt còn lại hoặc tồn khả dụng.
- [ ] Sửa lượng thực xuất vượt phần duyệt còn lại rồi Validate; backend
      phải chặn kể cả dòng phiếu ban đầu được tạo đúng.
- [ ] Validate xuất một phần: `partially_delivered`.
- [ ] Validate đủ: `issued`.
- [ ] Không được duyệt yêu cầu hoặc tạo PO.

Chuỗi trạng thái thường gặp:

`draft` → `requested` → `waiting_purchase` → `purchasing` → `ready` →
`partially_delivered` → `issued`.

Từ `requested`, PKH cũng có thể chuyển yêu cầu sang `postponed` hoặc `rejected`;
`approved` chỉ được giữ để tương thích dữ liệu cũ, không còn là bước của luồng mới.

## 6. Checklist test luồng Bảo trì

Đăng nhập `infrastructure.demo`:

- [ ] Thấy app **Quản lý bảo trì trạm BTS**.
- [ ] Tại **Tiếp nhận bàn giao**, tiếp nhận dự án `pending`.
- [ ] Kiểm tra trạng thái bàn giao thành `accepted`, trạng thái dự án thành
      `handed_over` và trạm `handover` thành `operating`.
- [ ] Bảo đảm dự án có `acceptance_date`; nếu thiếu, thao tác tạo hồ sơ
      bảo trì phải bị chặn.
- [ ] Tạo đồng loạt hồ sơ `maintenance.equipment`.
- [ ] Kiểm tra `effective_date` bằng ngày nghiệm thu dự án và ngày bảo trì
      đầu tiên bằng mốc này cộng tần suất checklist nhỏ nhất, không dùng
      ngày bàn giao/tiếp nhận bảo trì.
- [ ] Tạo `bts.maintenance.batch` từ **Danh sách dự án**.
- [ ] Bấm sinh danh sách trạm/checklist:
      `draft` → `generated`.
- [ ] Bắt đầu từng trạm; batch chuyển `in_progress`.
- [ ] Nhập kết quả checklist: `stable`, `need_repair` hoặc
      `need_replacement`.
- [ ] Hoàn tất trạm; trạm lỗi có `station_page_state = failed`.
- [ ] Gửi batch: `submitted`; xác nhận kết quả: `reviewed`.
- [ ] Tạo `bts.repair.proposal` từ lỗi checklist.
- [ ] Xác nhận đề xuất:
      - không cần vật tư → `ready_to_repair`;
      - có vật tư → `confirmed`.
- [ ] Nhánh có vật tư: tạo `bts.material.request`, trạng thái đề xuất
      `waiting_material`; sau khi request `issued`, đề xuất thành
      `ready_to_repair`.
- [ ] Bắt đầu sửa: `repairing`.
- [ ] Nhập `repair_result`, hoàn tất đề xuất: `done`.
- [ ] Hoàn tất batch bảo trì: `done`.

Không thể hoàn tất batch nếu lỗi chưa có đề xuất hoặc đề xuất chưa
`done`/`cancelled`.

### Nhắc lịch bảo trì

Chuẩn bị một hồ sơ thiết bị có **Người phụ trách bảo trì**:

- [ ] Đặt **Ngày bảo trì tiếp theo** sau ngày hiện tại 4 ngày; kiểm tra
      chưa có activity **Bảo trì trạm BTS sắp đến hạn**.
- [ ] Đổi ngày bảo trì tiếp theo thành sau ngày hiện tại 3 ngày; kiểm tra
      tạo đúng một activity cho người phụ trách, deadline là ngày hiện
      tại.
- [ ] Chạy scheduled action **Bảo trì BTS: nhắc lịch trước 3 ngày** nhiều
      lần; kiểm tra không tạo activity trùng.
- [ ] Bỏ người phụ trách và chạy lại cron; kiểm tra activity được giao
      cho người dùng đang hoạt động thuộc Tổ hạ tầng.
- [ ] Chuyển hồ sơ sang **Ngừng quản lý**; kiểm tra activity nhắc hạn bị
      xóa và dự án không bị tính đến hạn bởi hồ sơ này.
- [ ] Chuyển lại **Đang quản lý** với ngày hạn bằng ngày hiện tại; kiểm
      tra activity được tạo lại và dự án xuất hiện trong KPI/danh sách
      đến hạn.
- [ ] Kiểm tra phiếu bảo trì mới không sinh dòng cho hồ sơ **Ngừng quản
      lý**.

Dashboard chỉ báo dự án khi đã đến ngày bảo trì. Cảnh báo từ trước 3 ngày
nằm trong `mail.activity`.

KTV thuê ngoài hiện chưa có tài khoản Odoo. Tổ hạ tầng nhập/xác nhận kết
quả từ biểu mẫu ngoài hệ thống.

## 7. Checklist test luồng Hợp đồng mới

### Hồ sơ ban đầu và batch ký số

Đăng nhập `ksgs.demo`:

- [ ] Mở từng trạm, tab **Hồ sơ hợp đồng**.
- [ ] Upload Scan HĐ thuê đất và Scan BB đàm phán cho trạm.
- [ ] Kiểm tra hệ thống sinh `bts.contract` loại `land_lease` và
      `bts.negotiation.minutes` ở `draft`.
- [ ] Bấm **Chi tiết hợp đồng**; form mở ra không có **Trình duyệt**, **Ký
      duyệt**, **Từ chối**, **Thanh lý**, **Gia hạn** hoặc statusbar ký
      duyệt phức tạp.
- [ ] Nhập đối tác, ngày hiệu lực, ngày hết hạn, thời hạn, giá/chu kỳ nếu
      có, file scan và ghi chú; lưu lại được khi HĐ còn `draft`.
- [ ] Bấm **Chi tiết BB đàm phán**; nhập đối tác, ngày/nội dung đàm phán
      và file scan.
- [ ] Khi còn thiếu dữ liệu ở bất kỳ trạm nào, bấm **Gửi BGĐ ký số** phải
      báo `Chưa đủ HĐ thuê đất/BB đàm phán cho tất cả trạm.` kèm chi tiết.
- [ ] Nhập đủ HĐ thuê đất và BB đàm phán cho mọi trạm rồi gửi; batch giai
      đoạn 1 được tạo ở `submitted`.
- [ ] Kiểm tra HĐ chuyển `submitted`, BB chuyển `pending_approval` và KSGS
      không sửa được hồ sơ đã gửi.
- [ ] Sau khi trạm có `acceptance_date`, upload Scan HĐ cho thuê trạm.
- [ ] Kiểm tra sinh `bts.contract` loại `infrastructure_lease`, tự liên
      kết HĐ thuê đất cùng trạm.
- [ ] Thử chọn HĐ thuê đất loại khác hoặc của trạm khác; lưu hồ sơ phải bị
      chặn ngay cả khi HĐ cho thuê trạm còn `draft`.

Đăng nhập `bgd.contract.demo`:

- [ ] Mở **Ký số hợp đồng**.
- [ ] Thấy batch giai đoạn 1 do KSGS vừa gửi.
- [ ] Upload file đã ký cho từng dòng và bấm **Ký số / xác nhận ký**.
- [ ] Chọn email, bấm **Gửi mã OTP** và kiểm tra email của chính user BGĐ.
- [ ] Nhập OTP hợp lệ trong 5 phút; kiểm tra dòng lưu user, thời điểm và mã
      băm chữ ký, đồng thời không cho dùng lại OTP.
- [ ] Với một mã mới, nhập sai 5 lần và xác nhận mã chuyển sang `locked`.
- [ ] Với một mã khác, để quá 5 phút/chạy cron và xác nhận mã chuyển sang
      `expired`.
- [ ] Hợp đồng thành `active`; biên bản thành `confirmed`.
- [ ] Khi ký đủ, bấm **Hoàn thành batch**; batch thành `done`.
- [ ] Giai đoạn 1 đưa trạm về `contracted`.

Quay lại `ksgs.demo`:

- [ ] Kiểm tra dashboard dự án có thông báo batch giai đoạn 1 hoàn tất.
- [ ] Nhập đủ HĐ cho thuê trạm cho mọi trạm đã nghiệm thu.
- [ ] Nếu còn trạm thiếu điều kiện/hồ sơ, gửi phải báo
      `Chưa đủ HĐ cho thuê trạm cho tất cả trạm.`
- [ ] Gửi batch giai đoạn 2.

Quay lại `bgd.contract.demo`:

- [ ] Ký đủ và hoàn thành batch giai đoạn 2; mọi trạm chuyển
      `station_lease_signed`.

Kiểm tra nhánh từ chối trên một batch `submitted` chưa ký dòng nào:

- [ ] BGĐ nhập lý do và bấm **Từ chối batch**.
- [ ] Batch thành `rejected`; HĐ/BB chưa ký trở về `draft`.
- [ ] KSGS sửa được hồ sơ bị trả lại và có thể gửi batch mới.

Batch giai đoạn 2 chỉ tạo được khi giai đoạn 1 đã `done`, trạm có
`acceptance_date` và có HĐ cho thuê trạm.

### Danh sách dự án đến hạn

Đăng nhập `infrastructure.demo`, `tpkh.demo` hoặc `bgd.contract.demo`:

- [ ] Mở **Hợp đồng → Danh sách dự án**.
- [ ] Tạo dữ liệu test có HĐ `active`/`renewal_agreed`:
      một quá hạn, một còn 0–30 ngày và một còn hạn lâu.
- [ ] Kiểm tra thứ tự: quá hạn → sắp hết hạn → còn hạn.
- [ ] Kiểm tra ngày hết hạn gần nhất, số ngày còn lại và cột cần xử lý.
- [ ] HĐ thuê đất sắp/quá hạn phải hiện “Gia hạn HĐ thuê đất trước”.
- [ ] HĐ cho thuê trạm sắp hết hạn:
      - đất đủ hạn kỳ mới → “Gia hạn HĐ cho thuê trạm”;
      - thiếu/không đủ hạn → “Gia hạn HĐ thuê đất trước”.
- [ ] Mở một dự án: form chỉ có thông tin tổng hợp hợp đồng và tab **Trạm
      có hợp đồng đến hạn**; không có statusbar/trường bàn giao bảo trì.
- [ ] Bấm **Xem hợp đồng** trên dòng trạm để mở đúng hợp đồng liên quan.

Chỉ `active` và `renewal_agreed` được tính trong tổng hợp đến hạn. Job
`Hợp đồng BTS: cập nhật tổng hợp đến hạn` làm mới số ngày hằng ngày.

### Nhắc hạn và cron hợp đồng

Đăng nhập System Administrator hoặc dùng dữ liệu được chuẩn bị bởi đúng
vai trò:

- [ ] Tạo hợp đồng `active` hết hạn sau 10 ngày, đặt **Nhắc trước = 7**;
      kiểm tra activity có deadline sau 3 ngày.
- [ ] Đổi **Nhắc trước = 5**; kiểm tra vẫn chỉ có một activity và deadline
      được cập nhật thành sau 5 ngày.
- [ ] Đổi ngày hết hạn; kiểm tra activity được tính lại theo ngày mới.
- [ ] Chạy scheduled action **Hợp đồng BTS: nhắc hạn và cập nhật hết
      hạn** nhiều lần; kiểm tra không tạo activity trùng.
- [ ] Tạo hợp đồng `active` có ngày hết hạn trước ngày hiện tại, chạy job;
      kiểm tra hợp đồng chuyển sang `expired`.
- [ ] Ký một hồ sơ gia hạn; kiểm tra activity theo hạn cũ bị xóa và
      activity mới dùng ngày hết hạn cùng **Nhắc trước (ngày)** hiện tại.
- [ ] Xác nhận job **Hợp đồng BTS: cập nhật tổng hợp đến hạn** vẫn hoạt
      động riêng để làm mới tổng hợp dự án/trạm.

Dashboard/Danh sách dự án vẫn phân loại sắp hết hạn theo 0–30 ngày.
**Nhắc trước (ngày)** chỉ cấu hình deadline activity của từng hợp đồng.

Đăng nhập `ksgs.demo`, mở **Quản lý dự án BTS → Danh sách dự án**:

- [ ] Form dự án không có tab **Theo dõi hợp đồng/trạm**.
- [ ] Tab **Hợp đồng trạm** trên dự án chỉ tổng hợp/gửi ký; phần nhập hồ sơ
      nằm trên form trạm và không có dữ liệu theo dõi đến hạn hoặc gia hạn.

### Gia hạn

Đăng nhập `infrastructure.demo`:

- [ ] Từ hợp đồng phù hợp, tạo bản ghi `bts.contract.renewal`.
- [ ] Mở menu **Gia hạn hợp đồng** và bấm **Bắt đầu thực hiện**:
      `draft` → `in_progress`.
- [ ] Nhập ngày ký mới, ngày hiệu lực mới, ngày hết hạn mới và giá thuê
      mới nếu có.
- [ ] Upload file scan gia hạn.
- [ ] Bấm **Gửi BGĐ ký số**: `pending_signature`.

Đăng nhập `bgd.contract.demo`:

- [ ] Mở bản ghi tại **Gia hạn hợp đồng**.
- [ ] Upload hồ sơ đã ký số.
- [ ] Bấm **Ký số / xác nhận ký**.
- [ ] Kiểm tra renewal thành `completed`; hợp đồng gốc về `active` và
      nhận ngày/giá mới.

Với HĐ cho thuê trạm, HĐ thuê đất liên kết phải ở
`active`/`renewal_agreed` và hết hạn không sớm hơn ngày hết hạn mới.

## 8. Test phân quyền và menu

| User | Phải thấy | Không được thấy/thực hiện |
| --- | --- | --- |
| `ksgs.demo` | Dự án | Kho, Bảo trì, Hợp đồng |
| `tpkh.demo` | Kho | Dự án, Bảo trì, Hợp đồng; nhập/xuất kho |
| `warehouse.demo` | Kho; yêu cầu; PO chỉ đọc; nhập/xuất; vật tư chỉ đọc | Dự án, Bảo trì, Hợp đồng; duyệt/tạo/sửa PO; tạo/sửa/xóa vật tư |
| `infrastructure.demo` | Bảo trì; Hợp đồng: Tổng quan, Danh sách dự án, Gia hạn | Kho; Ký số hợp đồng |
| `bgd.contract.demo` | Hợp đồng và Ký số hợp đồng | Dự án, Kho, Bảo trì |
| `dtc.admin.demo` | Settings | Toàn bộ app nghiệp vụ DTC |
| System Administrator | Toàn bộ app DTC và app Odoo gốc | Không áp dụng |

Ngoài kiểm tra menu, cần thử gọi nút sai vai trò. Guard Python phải chặn:

- Thủ kho duyệt yêu cầu hoặc tạo PO.
- Thủ kho sửa PO hoặc tạo/sửa/xóa vật tư.
- PKH Validate phiếu kho.
- PKH/Tổ hạ tầng ký hợp đồng.
- KSGS gọi trực tiếp `action_submit`/`action_activate` trên từng HĐ hoặc
  action submit/confirm trên từng BB.
- BGĐ bắt đầu thương lượng gia hạn.
- DTC Admin chạy action nghiệp vụ.

## 9. Lỗi thường gặp

| Lỗi | Cách xử lý |
| --- | --- |
| Không thấy menu sau upgrade | Đăng xuất/đăng nhập; kiểm tra đúng group, không cộng group tùy tiện |
| Import không tìm thấy quan hệ | Import model cha trước; dùng `External ID` và cột `.../External ID` |
| Trùng mã dự án/trạm/hợp đồng | Đổi mã; không tái dùng mã của dữ liệu cũ |
| Ngày hoặc tọa độ lỗi | Dùng `YYYY-MM-DD`; decimal dùng dấu chấm và đúng giới hạn |
| Không tạo được yêu cầu từ dự án | Đưa dự án về `approved` |
| Nhà cung cấp không chọn được | Kiểm tra đối tác có `partner_type = supplier` |
| Yêu cầu không về `ready` | Kiểm tra PO gắn đúng yêu cầu đã xác nhận và toàn bộ receipt của PO đã Validate đủ số lượng duyệt; tồn kho chung không tự làm đổi trạng thái |
| Không gửi được batch giai đoạn 1 | Mọi trạm phải có HĐ thuê đất và BB đàm phán `draft`, đủ đối tác/ngày/thời hạn/file scan |
| Không gửi được batch giai đoạn 2 | Giai đoạn 1 phải `done`; mọi trạm đã nghiệm thu và có HĐ cho thuê trạm đủ dữ liệu/file scan |
| Không sửa được HĐ/BB | Hồ sơ đã gửi ký bị khóa; chỉ sửa lại sau khi BGĐ từ chối batch và hồ sơ về `draft` |
| Không upload HĐ cho thuê trạm | Trạm phải có `acceptance_date` |
| Gia hạn HĐ hạ tầng bị chặn | HĐ thuê đất liên kết phải còn đủ đến ngày hết hạn mới |
| Không tạo được hồ sơ bảo trì | Dự án phải được tiếp nhận và có `project.project.acceptance_date`; không dùng ngày bàn giao thay thế |
| Ngày bảo trì vẫn theo mốc cũ | Hồ sơ equipment đã lưu trước khi đổi công thức cần migration/tính lại dữ liệu |
| Không hoàn tất bảo trì | Xử lý toàn bộ checklist lỗi và đề xuất sửa chữa trước |
| DTC Admin không thao tác nghiệp vụ | Đúng thiết kế; dùng đúng user vai trò hoặc System Administrator |

Model `bts.station.handover` vẫn được giữ để tương thích nhưng hiện không
có menu. Luồng bàn giao bảo trì đang dùng các field
`maintenance_handover_*` trên `project.project`.

## 10. Checklist demo nhanh 15–20 phút

Nên chuẩn bị trước một dự án có ngày nghiệm thu, một trạm có ngày nghiệm
thu, một vật tư có tồn, đối tác và các file scan nhỏ.

1. **0–3 phút — KSGS**
   - Mở dự án/trạm đã chuẩn bị.
   - Tạo và gửi yêu cầu vật tư.
   - Upload HĐ thuê đất + BB đàm phán, mở chi tiết nhập đủ nội dung.
   - Minh họa form không có **Trình duyệt**, rồi gửi batch ở cấp dự án.
2. **3–6 phút — PKH**
   - Duyệt yêu cầu; tạo và xác nhận PO cho toàn bộ số lượng đã duyệt.
3. **6–8 phút — Thủ kho**
   - Validate receipt của PO; kiểm tra yêu cầu chuyển `ready`.
   - Tạo phiếu xuất, kiểm tra dòng tự điền và phiếu đã giữ hàng.
   - Validate; kiểm tra request `issued`.
4. **8–11 phút — BGĐ hợp đồng**
   - Ký từng dòng batch, hoàn thành batch; kiểm tra trạm `contracted`.
5. **11–14 phút — KSGS**
   - Kiểm tra thông báo vật tư ready.
   - Với dự án chuẩn bị sẵn trạm `handover`, bàn giao sang bảo trì.
6. **14–18 phút — Tổ hạ tầng**
   - Tiếp nhận, tạo equipment và phiếu bảo trì.
   - Sinh checklist, ghi một kết quả ổn định và hoàn tất luồng ngắn.
7. **18–20 phút — Hợp đồng**
   - Mở **Danh sách dự án**, kiểm tra ưu tiên đến hạn.
   - Mở một hồ sơ gia hạn chuẩn bị sẵn để minh họa Tổ hạ tầng gửi ký và BGĐ ký.

PO/nhập kho đầy đủ, batch ký số giai đoạn 2 và nhánh sửa chữa cần vật tư
nên test ở phiên riêng; khó trình diễn đúng toàn bộ trong 20 phút.
