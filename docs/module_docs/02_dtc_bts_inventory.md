# Phân hệ mua hàng và kho vật tư (`dtc_bts_inventory`)

> Kiểm tra theo working tree ngày 30/07/2026.

## Mục đích

Phân hệ quản lý yêu cầu cấp phát vật tư BTS, kiểm tra tồn, mua bổ sung,
nhập kho và xuất kho theo dự án. Module mở rộng Purchase, Inventory và
Product của Odoo.

## Model và liên kết

### `bts.material.request`

- `name`: mã yêu cầu sinh từ sequence.
- `bts_project_id`: dự án bắt buộc.
- `source`: `project_construction`, `maintenance` hoặc `manual`.
- `request_user_id`, `request_date`: người và ngày yêu cầu.
- `vendor_id`: nhà cung cấp dự kiến khi cần mua.
- `line_ids`: vật tư, đơn vị tính, số lượng yêu cầu/duyệt/đã cấp.
- `purchase_order_ids`: các PO được tạo từ yêu cầu.
- `picking_ids`: các phiếu nhập/xuất liên quan.
- `notification_ids`: thông báo chờ duyệt, chờ nhập, sẵn sàng cấp phát và chờ khóa PO.
- Khi module bảo trì được cài, yêu cầu có thêm `station_id` và
  `repair_proposal_id`.

### Model Odoo được mở rộng

- `purchase.order` và `purchase.order.line`: liên kết dự án và yêu cầu vật tư.
- `stock.picking` và `stock.move`: liên kết dự án, yêu cầu và dòng yêu cầu.
- `product.template`/`product.product`: field `is_bts_material`.
- `project.project`: nút tạo/xem yêu cầu vật tư trên dự án đã được phê duyệt.

## Trạng thái yêu cầu vật tư

| Mã | Hiển thị | Ý nghĩa |
| --- | --- | --- |
| `draft` | Nháp | Người yêu cầu đang lập |
| `requested` | Đã gửi | Chờ PKH duyệt |
| `approved` | Đã duyệt | Trạng thái tương thích dữ liệu cũ |
| `waiting_purchase` | Chờ mua hàng / bổ sung vật tư | Đã duyệt, đang chờ tạo/xác nhận PO |
| `purchasing` | Đang mua hàng | Đã xác nhận PO, chờ Thủ kho hoàn tất phiếu nhập |
| `ready` | Sẵn sàng cấp phát | Đã nhập đủ số lượng duyệt của PO gắn với yêu cầu |
| `partially_delivered` | Cấp phát một phần | Đã xuất một phần |
| `issued` | Hoàn tất yêu cầu | Đã xuất đủ; chờ/đã khóa PO |
| `postponed` | Tạm hoãn | PKH tạm dừng xử lý và bắt buộc nhập lý do; có thể duyệt hoặc từ chối sau đó |
| `rejected` | Từ chối | PKH từ chối |
| `cancelled` | Hủy | Yêu cầu đã hủy |

## Luồng cấp phát

1. KSGS tạo yêu cầu từ form dự án; Tổ hạ tầng tạo từ đề xuất sửa chữa.
2. Người yêu cầu gửi: `draft` → `requested`.
3. PKH duyệt số lượng: `requested` → `waiting_purchase`.
4. PKH chọn nhà cung cấp, tạo và xác nhận PO cho toàn bộ số lượng được duyệt.
   Khi PO được xác nhận, yêu cầu chuyển `purchasing`; Thủ kho nhận email và
   thông báo trên dashboard Kho để theo dõi phiếu nhập. Đề xuất sửa chữa chỉ
   tạo yêu cầu vật tư, không tự tạo PO.
5. Thủ kho mở phiếu nhập được sinh từ đúng PO và xác nhận khi hàng thực tế về.
   Chỉ khi các PO gắn với yêu cầu đã nhận đủ toàn bộ số lượng duyệt, yêu cầu
   mới chuyển `ready`; tồn kho chung không còn làm yêu cầu tự nhảy trạng thái.
6. Hệ thống gửi email và thông báo sẵn sàng cấp phát cho KSGS/người yêu cầu.
7. Thủ kho tạo phiếu xuất từ yêu cầu. Hệ thống tự sinh dòng sản phẩm với
   số lượng `min(lượng duyệt còn lại, tồn khả dụng)`, tự gọi
   `action_confirm()` và `action_assign()`. Vì vậy phiếu không còn bước
   “Đánh dấu việc cần làm”; Thủ kho không nhập lại sản phẩm.
8. Thủ kho kiểm tra lượng thực xuất và Validate. Backend khóa dòng yêu cầu
   khi kiểm tra, quy đổi đúng đơn vị tính và chặn tổng lượng Validate vượt
   số lượng được duyệt còn lại.
9. Hoàn tất phiếu xuất cập nhật `quantity_issued`, sau đó chuyển yêu cầu
   thành `partially_delivered` hoặc `issued` (**Hoàn tất yêu cầu**).
10. Khi đã xuất đủ, Trưởng phòng Kế hoạch nhận email/thông báo để bấm
    **Khóa PO**; thao tác này kết thúc chuỗi mua–nhập–xuất.

`Loại hoạt động` được hệ thống chọn là loại xuất kho của warehouse. Trường
địa chỉ giao hàng chuẩn của Odoo hiện không phải nguồn địa chỉ trạm; chứng
từ BTS được truy vết bằng dự án, yêu cầu và dòng yêu cầu vật tư.

Nếu yêu cầu đến từ sửa chữa, khi mọi yêu cầu còn hiệu lực đã `issued`, đề
xuất sửa chữa tự chuyển sang `ready_to_repair`.

## Thông báo vật tư

`bts.material.notification` theo dõi bốn công việc:

- `approval`: yêu cầu mới chờ Trưởng phòng Kế hoạch duyệt;
- `incoming`: PO đã xác nhận, chờ Thủ kho nhập hàng;
- `ready`: hàng đã nhập đủ, KSGS/người yêu cầu đến nhận;
- `lock_po`: đã xuất đủ, chờ Trưởng phòng Kế hoạch khóa PO.

Thông báo `ready` hiển thị trên dashboard Dự án; ba loại còn lại hiển thị trên
dashboard Kho và đều có thể đánh dấu đã xem.

Dashboard kho không hiển thị thẻ “Vật tư sẵn sàng cấp phát”; dashboard này
tập trung vào công việc vận hành kho.

## Dashboard cung ứng vật tư công trình

Dashboard không phân tích kho theo mô hình mua–bán hoặc tối ưu tồn. Mục tiêu
là đối chiếu chuỗi nghiệp vụ của từng dòng vật tư:

`Nhu cầu được duyệt → Đã mua → Đã nhập → Đã xuất cho công trình`

Các KPI:

- số dự án có nhu cầu vật tư;
- tỷ lệ dòng vật tư đã cấp đủ;
- số dòng còn thiếu nhập;
- số dòng đã nhập nhưng đang chờ xuất.

Dashboard còn hiển thị:

- tiến độ cấp phát theo dự án, tính bằng tỷ lệ hoàn tất trung bình của các
  dòng vật tư, không cộng lẫn số lượng có đơn vị tính khác nhau;
- cơ cấu yêu cầu theo bốn nhóm: chờ duyệt, đang mua/chờ nhập, chờ xuất/cấp
  một phần và đã cấp đủ;
- bảng đối chiếu nhu cầu, đã mua, đã nhập, đã xuất, còn thiếu, chờ xuất và
  mua vượt theo từng vật tư;
- cảnh báo dự án thiếu vật tư, vật tư nhập rồi chưa xuất, mua vượt nhu cầu
  hoặc dự án đã hoàn thành nhưng còn vật tư treo.

## Menu và vai trò thao tác

- App kho, dashboard và menu yêu cầu: PKH, Thủ kho, System Administrator.
- Đơn mua hàng: PKH được tạo/xử lý; Thủ kho chỉ đọc; System Administrator toàn
  quyền.
- Nhập kho/Xuất kho: Thủ kho và System Administrator.
- Danh mục vật tư: PKH và System Administrator được thao tác; Thủ kho chỉ đọc.

KSGS và Tổ hạ tầng có quyền cần thiết trên yêu cầu vật tư nhưng không thấy
app/menu Kho; họ chỉ mở form yêu cầu từ màn hình Dự án hoặc Sửa chữa.
DTC Admin không tham gia duyệt, mua hàng hay nhập/xuất kho.

Các action còn kiểm tra group ở Python, nên việc gọi RPC hoặc URL trực tiếp
không thay thế được quyền nghiệp vụ.

Thủ kho không kế thừa `purchase.group_purchase_user`. Module cấp ACL chỉ đọc
riêng trên `purchase.order`/`purchase.order.line`; đồng thời view và guard
Python chặn tạo, sửa, xóa `product.template`/`product.product`.

## Import danh mục vật tư

Module khai báo sẵn các đơn vị thường dùng: `Cái`, `Bộ`, `Bao`, `Thùng`,
`Bịch`, `m2`, `m3`.

Khi import Product:

- dùng đúng tên đơn vị tính đã khai báo;
- giá trị tiếng Việt `Hàng hóa`/`Hàng hoá` ở field loại sản phẩm được
  chuẩn hóa thành mã kỹ thuật `product`;
- nên xuất file mẫu từ màn hình Danh mục vật tư để lấy đúng tên cột và
  external ID nếu cần cập nhật dữ liệu đã có.
