# Phân hệ dự án và trạm BTS (`dtc_bts_base`)

> Kiểm tra theo working tree ngày 30/07/2026.

## Mục đích

Đây là module nền, mở rộng Project và Contacts để quản lý dự án, trạm BTS,
đối tác và cung cấp dữ liệu dùng chung cho kho, hợp đồng và bảo trì.

## Model và trường chính

### `project.project`

- `project_code`: mã dự án bắt buộc, duy nhất, sinh từ sequence.
- `telecom_partner_id`: đối tác viễn thông.
- `station_type`: `macro` hoặc `cell`.
- `province`, `district`, `commune`: địa bàn.
- `planned_start_date`, `planned_end_date`, `acceptance_date`: các mốc dự
  án; `acceptance_date` là mốc tính lịch bảo trì đầu tiên.
- `enterprise_director_id`: Giám đốc Xí nghiệp sở hữu phạm vi dự án.
- `project_manager_id`: KSGS được GĐXN phân công phụ trách.
- `station_count`: số trạm trong dự án.
- `state`: trạng thái dự án.

Trạng thái dự án:

`draft` → `survey` → `approved` → `in_progress` → `done`.

`cancelled` dùng khi dự án bị hủy. Code hiện chỉ khai báo trạng thái và ràng
buộc dữ liệu; chưa có action Python ép một sơ đồ chuyển trạng thái riêng.

### `project.task`

- `station_code`: mã trạm bắt buộc, duy nhất, sinh từ sequence.
- `latitude`, `longitude`, `site_address`: vị trí trạm.
- `assigned_user_id`: KSGS phụ trách, đồng bộ vào người được giao task.
- `acceptance_date`: ngày nghiệm thu/bàn giao của riêng trạm, được hiển thị
  trên form trạm và trong tab **Hợp đồng trạm**; mốc này mở quyền tải HĐ
  cho thuê trạm, không dùng làm mốc lịch bảo trì dự án.
- `handover_state`: trạng thái bàn giao.
- `station_state`: trạng thái nghiệp vụ của trạm.
- Các field related lưu mã dự án, loại trạm, địa bàn và đối tác viễn thông.

Luồng trạng thái trạm chính:

`survey` → `negotiating` → `contracted` → `construction` → `acceptance` →
`station_lease_signed` → `handover` → `operating`.

Trạng thái dự án được tổng hợp khi tất cả trạm có cùng trạng thái. Khi thêm
trạm mới, dự án chuyển sang `survey`; khi tất cả trạm đạt `contracted`, dự án
chuyển sang `approved` để KSGS tạo yêu cầu vật tư.

Giá trị `cancelled` được giữ để tương thích dữ liệu cũ.

Trạng thái bàn giao:

- `not_handed`: chưa bàn giao.
- `ready_to_handover`: sẵn sàng bàn giao.
- `handed`: đã bàn giao.
- `accepted`: đã tiếp nhận.

### `res.partner`

Field `partner_type` có các giá trị:

- `supplier`: nhà cung cấp.
- `landowner`: chủ đất.
- `telecom_partner`: đối tác viễn thông.
- `external_technician`: kỹ thuật viên thuê ngoài.
- `other`: khác.

## Kiểm tra dữ liệu

- Mã dự án và mã trạm không được trùng.
- Ngày kết thúc dự kiến không được trước ngày bắt đầu.
- Vĩ độ phải từ -90 đến 90; kinh độ từ -180 đến 180.
- Đối tác được chọn ở field đối tác viễn thông phải đúng `partner_type`.

## Dashboard dự án

Dashboard hiển thị:

- tổng dự án và tổng trạm;
- số trạm Macro/Cell;
- số dự án có trạm đã bàn giao;
- số trạm theo các giai đoạn khảo sát, đàm phán, thi công, nghiệm thu và
  bàn giao;
- bảng tổng hợp từng dự án;
- thông báo vật tư `ready` chưa đọc của chính người yêu cầu.

Thông báo vật tư có liên kết mở yêu cầu và thao tác “Đã xem”.

## Menu

Ứng dụng `Quản lý dự án BTS` gồm:

- Bảng tổng hợp
- Danh sách dự án
- Danh sách trạm BTS
- Đối tác

Ứng dụng này hiển thị cho GĐXN, KSGS và System Administrator. Role GĐXN bị
giới hạn runtime để chỉ thấy cây app này. PKH, Thủ kho, Tổ hạ tầng, BGĐ hợp
đồng và DTC Admin không thấy root menu dự án.

Quyền dữ liệu chính:

- GĐXN tạo/sửa dự án trong phạm vi của mình, phân công KSGS và tạo/sửa
  trạm; không xóa dự án/trạm hoặc chuyển dự án sang GĐXN khác.
- KSGS chỉ đọc dự án được phân công, không tạo/sửa/xóa dự án.
- KSGS tạo/sửa trạm thuộc dự án được phân công nhưng không xóa trạm.
- KSGS vẫn dùng các action riêng để tạo yêu cầu vật tư, gửi batch hợp đồng
  và bàn giao dự án sang bảo trì; các action này không cấp quyền sửa tùy ý
  bản ghi dự án.

PKH, Thủ kho, Tổ hạ tầng và BGĐ hợp đồng chỉ có quyền đọc dự án/trạm để
hiển thị field tham chiếu trong chứng từ của phân hệ mình; record rule chặn
việc sửa, tạo hoặc xóa trạm.

Form dự án trong app này không hiển thị tab theo dõi hợp đồng đến hạn/gia
hạn. Tab **Hợp đồng trạm** chỉ tổng hợp trạng thái và cho KSGS gửi batch ký
số ở cấp dự án. KSGS nhập ngày nghiệm thu, tải scan và mở chi tiết hồ sơ tại
tab **Hồ sơ hợp đồng** trên form từng trạm. Màn hình theo dõi đến hạn nằm
trong app Hợp đồng và dùng một form `project.project` độc lập.

## Liên kết

- Kho dùng dự án làm nguồn yêu cầu vật tư, PO và phiếu kho.
- Hợp đồng liên kết trực tiếp với trạm và suy ra dự án.
- Bảo trì mở rộng dự án bằng trạng thái bàn giao, hồ sơ thiết bị và phiếu
  bảo trì dự án.
