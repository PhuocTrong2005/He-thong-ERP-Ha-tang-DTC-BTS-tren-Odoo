# Phân hệ hợp đồng BTS (`dtc_bts_contract`)

> Kiểm tra theo working tree ngày 30/07/2026.

## Phạm vi

Module quản lý biên bản đàm phán, hợp đồng thuê đất/thuê hạ tầng, gia hạn,
hồ sơ bàn giao trạm và dashboard cảnh báo hợp đồng.

## Model chính

| Model                               | Chức năng                                    |
| ----------------------------------- | -------------------------------------------- |
| `bts.negotiation.minutes`           | Biên bản đàm phán thuê đất hoặc thuê hạ tầng |
| `bts.contract`                      | Hợp đồng BTS                                 |
| `bts.contract.renewal`              | Lịch sử và tiến trình gia hạn                |
| `bts.contract.signature.batch`      | Batch gửi BGĐ ký số theo dự án/giai đoạn     |
| `bts.contract.signature.batch.line` | Từng hồ sơ trạm trong batch ký số            |
| `bts.station.handover`              | Hồ sơ bàn giao trạm                          |
| `bts.contract.dashboard`            | Dashboard hợp đồng                           |

Mọi hồ sơ đều liên kết với `project.task` là trạm BTS và suy ra dự án.
Không có hồ sơ hợp đồng gom ở cấp `project.project`.

## Điểm tạo hồ sơ ban đầu

KSGS không vào app Hợp đồng. KSGS mở từng `project.task` và dùng tab **Hồ
sơ hợp đồng** để chuẩn bị hồ sơ ban đầu:

- tải trực tiếp Scan HĐ thuê đất, Scan BB đàm phán và Scan HĐ cho thuê
  trạm;
- mở **Chi tiết hợp đồng** hoặc **Chi tiết BB đàm phán** để nhập nội dung;
- quay lại tab **Hợp đồng trạm** trên dự án để xem tổng hợp và gửi toàn bộ
  hồ sơ bằng nút **Gửi BGĐ ký số**.

Form chi tiết hợp đồng trong ngữ cảnh Dự án là view riêng cho KSGS. Form
không có statusbar phức tạp và không có các nút **Trình duyệt**, **Ký
duyệt**, **Từ chối**, **Thanh lý** hoặc **Gia hạn**. KSGS nhập được mã,
loại, trạm, đối tác, ngày ký giấy, ngày hiệu lực/hết hạn, thời hạn, giá
thuê, chu kỳ thanh toán, file scan và ghi chú khi hồ sơ còn `draft`.

Form biên bản mở từ tab hồ sơ trạm cũng là view chuẩn bị hồ sơ riêng, không có
workflow phê duyệt lẻ. HĐ cho thuê trạm chỉ được tải sau khi trạm có
`acceptance_date`. KSGS nhập mốc này trên form trạm.

Khi lưu, hệ thống tự tạo hoặc cập nhật hồ sơ `draft` tương ứng:

- HĐ thuê đất → `bts.contract(contract_type='land_lease')`.
- BB đàm phán → `bts.negotiation.minutes`.
- HĐ cho thuê trạm → `bts.contract(contract_type='infrastructure_lease')`.

Các hồ sơ được gắn `station_id` của dòng trạm; không tạo dữ liệu hợp đồng
ở cấp dự án.

Sau khi hồ sơ vào batch ký số, KSGS không thể sửa nội dung hoặc thay file.
Nếu BGĐ từ chối batch khi chưa ký dòng nào, hồ sơ được trả về `draft` và
KSGS có thể sửa để gửi lại.

## Batch ký số theo dự án

KSGS bấm **Gửi BGĐ ký số** tại tab **Hợp đồng trạm**. Hệ thống tự xác
định giai đoạn kế tiếp và kiểm tra đủ hồ sơ trên tất cả trạm của dự án:

- Giai đoạn 1: mỗi trạm có HĐ thuê đất và BB đàm phán.
- Giai đoạn 2: mỗi trạm đã nghiệm thu và có HĐ cho thuê trạm; chỉ mở sau
  khi batch giai đoạn 1 đã hoàn tất.

Hồ sơ được xem là đủ để gửi khi:

- HĐ có đối tác, ngày hiệu lực, ngày hết hạn, thời hạn và file scan;
- HĐ cho thuê trạm có liên kết HĐ thuê đất cùng trạm;
- BB đàm phán có đối tác, ngày đàm phán và file scan;
- hồ sơ vẫn ở `draft`.

Constraint backend kiểm tra liên kết HĐ thuê đất ngay khi trường liên kết
được gán, kể cả hồ sơ HĐ cho thuê trạm còn ở `draft`: hợp đồng liên kết
phải có loại `land_lease` và cùng `station_id`.

Nếu một trạm thiếu dữ liệu, hệ thống không tạo batch và trả thông báo theo
giai đoạn, kèm danh sách trạm/trường còn thiếu:

- `Chưa đủ HĐ thuê đất/BB đàm phán cho tất cả trạm.`
- `Chưa đủ HĐ cho thuê trạm cho tất cả trạm.`

Backend kiểm tra lại toàn bộ tập dòng ngay khi submit batch. Vì vậy không
thể dùng RPC để gửi một batch thiếu trạm hoặc sai hồ sơ.

Một batch chứa nhiều dòng hồ sơ theo trạm. Trạng thái:

`draft` → `submitted` → `partially_signed` → `done`

BGĐ có thể từ chối batch `submitted` khi chưa ký dòng nào, chuyển sang
`rejected` và trả các hồ sơ chưa ký về dự thảo.

BGĐ tải file đã ký và bấm **Ký số / xác nhận ký** trên từng dòng. Hệ thống
mở hộp thoại xác thực OTP:

1. BGĐ chọn kênh email và bấm **Gửi mã OTP**.
2. OTP được gửi ngay tới email của chính user đang đăng nhập.
3. BGĐ nhập OTP và xác nhận ký trong thời hạn 5 phút.

OTP được lưu dưới dạng băm, chỉ dùng một lần và chỉ user đã yêu cầu mã mới
được xác nhận. Nhập sai 5 lần sẽ khóa mã; cron một phút chuyển mã quá hạn
sang `expired`. Kênh SMS hiện là điểm tích hợp dự phòng, chưa kết nối nhà
cung cấp SMS thực tế.

Sau khi OTP hợp lệ, hệ thống lưu dấu vết gồm user, thời điểm, IP, user agent,
payload và mã băm chữ ký; file đã ký trở thành chỉ đọc. Khi tất cả dòng đã
ký, batch ở `partially_signed`; BGĐ bấm **Hoàn thành batch** để:

- Giai đoạn 1 chuyển tất cả trạm trong batch sang `contracted`.
- Giai đoạn 2 chuyển tất cả trạm trong batch sang `station_lease_signed`.
- Dashboard dự án tạo thông báo hoàn tất cho KSGS gửi batch, người quản lý
  dự án và KSGS phụ trách các trạm.

Action mở từ tab Dự án khóa tường minh vào tree/form hồ sơ KSGS. Action
trong app Hợp đồng khóa vào tree/form workflow đầy đủ. Hai ngữ cảnh không
dùng lẫn view dù cùng model `bts.contract`.

## Biên bản đàm phán

Trạng thái:

`draft` → `pending_approval` → `confirmed`.

`rejected` dùng khi Ban Giám đốc phụ trách hợp đồng từ chối. Biên bản bị
từ chối có thể đưa về `draft`.

Biên bản là hồ sơ upload/ký số độc lập theo trạm và là một dòng riêng
trong batch giai đoạn 1. Không có thao tác chuyển biên bản thành
`bts.contract`.

Giá trị `converted` và liên kết `converted_to_contract_id` chỉ được giữ
trong model để bảo toàn dữ liệu lịch sử từ luồng cũ; chúng không xuất hiện
trong thao tác/menu mới.

## Hợp đồng

Loại hợp đồng:

- `land_lease`: thuê đất.
- `infrastructure_lease`: cho thuê trạm; liên kết hợp đồng thuê đất cùng
  trạm.

Trạng thái:

| Mã               | Hiển thị              |
| ---------------- | --------------------- |
| `draft`          | Dự thảo               |
| `submitted`      | Chờ ký duyệt          |
| `active`         | Hiệu lực              |
| `renewal_agreed` | Đã thống nhất gia hạn |
| `liquidated`     | Đã thanh lý           |
| `expired`        | Hết hạn               |
| `cancelled`      | Đã hủy                |

Luồng hồ sơ ban đầu theo dự án:

1. KSGS tải scan, mở form chi tiết và nhập đủ nội dung từ tab **Hồ sơ hợp
   đồng** trên form từng trạm.
2. KSGS gửi batch ở cấp dự án; hệ thống chuyển HĐ sang `submitted` và BB
   đàm phán sang `pending_approval`.
3. BGĐ xử lý từng dòng tại menu **Ký số hợp đồng**. HĐ đã ký chuyển
   `active`; BB đã ký chuyển `confirmed`.
4. Khi ký đủ, BGĐ hoàn thành batch để cập nhật trạng thái tất cả trạm và
   phát thông báo dashboard.
5. Khi ký, hệ thống lưu người/ngày ký và tạo `mail.activity` nhắc hạn nếu
   hợp đồng có ngày hết hạn hợp lệ. Ngày nhắc lấy từ trường **Nhắc trước
   (ngày)** của chính hợp đồng.
6. Hợp đồng `active` có thể đánh dấu đã thống nhất gia hạn.
7. Tổ hạ tầng khởi tạo/điều phối, PKH xử lý nội dung thương lượng và BGĐ
   ký hoặc từ chối hồ sơ gia hạn.
8. Ban Giám đốc phụ trách hợp đồng phê duyệt thanh lý.
9. Cron chuyển hợp đồng hiệu lực đã quá ngày hết hạn sang `expired` và bổ
   sung hoặc cập nhật activity cảnh báo khi cần.

Form workflow đầy đủ trong app Hợp đồng và các action trình/ký/thanh lý
vẫn được giữ cho vai trò được phân quyền và dữ liệu nghiệp vụ tương ứng.
KSGS không được gọi trực tiếp action submit/approve/sign trên từng HĐ hoặc
BB, kể cả qua RPC.

Quyền ký duyệt và thanh lý được kiểm tra cả ở button và Python; group Quản
lý nghiệp vụ chung không thay thế group Ban Giám đốc hợp đồng.
System Administrator vẫn là ngoại lệ kỹ thuật. DTC Admin không phải actor
trong quy trình.

## Nhắc hạn hợp đồng

Mỗi hợp đồng có trường `alert_before_days` hiển thị là **Nhắc trước
(ngày)**, mặc định 30 và phải lớn hơn 0. Deadline của activity được tính:

`Ngày hết hạn - Nhắc trước (ngày)`

Ví dụ hợp đồng còn 10 ngày:

- đặt **Nhắc trước = 7** thì activity có deadline sau 3 ngày;
- đổi thành **Nhắc trước = 5** thì deadline được cập nhật thành sau 5
  ngày.

Đây là ví dụ người dùng thay đổi cấu hình của một hợp đồng, không phải hệ
thống tự đổi từ 7 ngày xuống 5 ngày. Giá trị mặc định vẫn là 30 ngày.

Nếu ngày nhắc đã qua, deadline được đặt bằng ngày hiện tại. Activity được
giao cho tất cả người dùng đang hoạt động thuộc Tổ hạ tầng; khi nhóm không
có người nhận, hệ thống dùng người ký duyệt hoặc người đang thao tác.

Khi ngày hết hạn, số ngày nhắc hoặc trạng thái hợp đồng thay đổi, activity
cũ được xóa và tính lại. Việc ký gia hạn cũng xóa activity theo hạn cũ,
cập nhật ngày hết hạn mới và tạo activity theo kỳ mới. Hệ thống không tạo
nhiều activity trùng cho cùng hợp đồng/người nhận.

Scheduled action **Hợp đồng BTS: nhắc hạn và cập nhật hết hạn** chạy mỗi
ngày:

1. Chuyển hợp đồng `active` có ngày hết hạn nhỏ hơn ngày hiện tại sang
   `expired`.
2. Với từng hợp đồng `active` chưa hết hạn, dùng chính
   `alert_before_days` của hợp đồng để tạo hoặc cập nhật activity còn
   thiếu.

Scheduled action này độc lập với **Hợp đồng BTS: cập nhật tổng hợp đến
hạn**. Job tổng hợp chỉ làm mới các trường lưu trên dự án/trạm; job nhắc
hạn mới xử lý activity và trạng thái `expired`.

Dashboard và **Danh sách dự án** vẫn dùng cửa sổ nghiệp vụ cố định 0–30
ngày để phân loại **Sắp hết hạn**. Trường **Nhắc trước (ngày)** điều khiển
deadline của `mail.activity`, không thay đổi cửa sổ KPI 30 ngày.

## Gia hạn

`bts.contract.renewal` do Tổ quản lý hạ tầng xử lý và có trạng thái:

`draft` → `in_progress` → `pending_signature` → `completed`.

Tổ hạ tầng bấm **Gửi BGĐ ký số** sau khi hoàn thành xử lý. BGĐ tải hồ sơ đã ký
và bấm **Ký số / xác nhận ký**; lúc đó hệ thống mới cập nhật ngày hết hạn
và giá thuê mới lên hợp đồng.

BGĐ có thể nhập lý do và từ chối hồ sơ `pending_signature`, chuyển sang
`rejected`. Tổ hạ tầng có thể đưa hồ sơ bị từ chối về `draft`.

Luồng nghiệp vụ nằm hoàn toàn trong app Hợp đồng:

1. Dashboard và **Danh sách dự án** tổng hợp hợp đồng `active` còn từ 0
   đến 30 ngày hoặc đã quá hạn; cron tạo activity cho Tổ hạ tầng theo
   trường **Nhắc trước (ngày)** của từng hợp đồng.
2. Tổ hạ tầng mở hợp đồng từ dòng trạm và có thể tạo hồ sơ gia hạn.
3. Tổ hạ tầng bắt đầu xử lý, thương lượng ngoài thực tế và nhập ngày ký mới,
   ngày hiệu lực mới, ngày hết hạn mới, giá thuê mới nếu có.
4. Tổ hạ tầng tải file scan gia hạn theo trạm và gửi BGĐ ký số.
5. BGĐ nhận cảnh báo trên **Tổng quan** và xử lý hồ sơ tại **Ký số hợp
   đồng → Hợp đồng gia hạn chờ ký**. Menu **Gia hạn hợp đồng** vẫn lưu toàn
   bộ hồ sơ để Tổ hạ tầng theo dõi và xử lý.
6. Sau khi BGĐ xác nhận ký, hệ thống cập nhật `sign_date`,
   `effective_date`, `expiration_date` và `rental_price` của hợp đồng.

Đối với HĐ cho thuê trạm (`infrastructure_lease`), cả lúc gửi ký và lúc
BGĐ xác nhận, hệ thống kiểm tra HĐ thuê đất liên kết:

- Đang `active` hoặc `renewal_agreed`.
- Có ngày hết hạn không sớm hơn ngày hết hạn mới của HĐ cho thuê trạm.

Không đạt điều kiện thì hồ sơ không thể chuyển tiếp.

## Hồ sơ bàn giao

`bts.station.handover` lưu người bàn giao/nhận, ngày bàn giao, checklist hồ
sơ và ghi chú. Trạng thái:

`draft` → `handed_over`, hoặc `cancelled`.

## Dashboard hợp đồng

Dashboard phân tích trực tiếp dữ liệu Odoo, không nhúng công cụ BI bên ngoài:

- Biểu đồ số hợp đồng theo các mốc quá hạn, dưới 60 ngày, 60–90 ngày và
  trên 90 ngày.
- Ma trận nhiệt số hợp đồng theo tỉnh/thành và mốc hạn.
- Biểu đồ đối tác cần ưu tiên gia hạn, tính từ hợp đồng quá hạn hoặc còn
  không quá 90 ngày.
- Bảng cảnh báo hợp đồng đất hết hạn sớm hơn hợp đồng hạ tầng liên quan.
- Khung cảnh báo/công việc vẫn hiển thị hợp đồng chờ ký, chờ gia hạn,
  sắp/quá hạn, biên bản chờ phê duyệt và bản ghi gia hạn đang thực hiện.

## Menu

Ứng dụng `Quản lý hợp đồng BTS` gồm:

- Tổng quan
- Danh sách dự án
- Gia hạn hợp đồng
- Ký số hợp đồng

Không có menu **Biên bản đàm phán** độc lập. KSGS upload biên bản từ tab
**Hồ sơ hợp đồng** trên trạm; BGĐ ký biên bản trong batch giai đoạn 1.

Việc menu xuất hiện không tự cấp quyền thao tác; ACL và kiểm tra action vẫn
được áp dụng độc lập.

Root app Hợp đồng chỉ hiển thị cho Tổ hạ tầng, BGĐ hợp đồng và
System Administrator. KSGS không thấy root app. Model hồ sơ bàn giao vẫn
được giữ để tương thích nhưng hiện không có menu.

Menu **Ký số hợp đồng** chỉ hiển thị cho BGĐ hợp đồng/System, gồm
**Batch hợp đồng ban đầu** ở trạng thái `submitted`/`partially_signed` và
**Hợp đồng gia hạn chờ ký** ở trạng thái `pending_signature`.

Menu **Danh sách dự án** mở form `project.project` riêng của app Hợp đồng.
Form chỉ hiển thị mã/tên dự án, các chỉ số hợp đồng và tab **Trạm có hợp
đồng đến hạn** với nút **Xem hợp đồng** lọc theo trạm. Form này không kế
thừa form Dự án hoặc Bảo trì và không có trạng thái bàn giao bảo trì.

Ngược lại, form trong app Quản lý dự án BTS không có tab **Theo dõi hợp
đồng/trạm**. App Dự án giữ tab **Hợp đồng trạm** để tổng hợp và gửi batch;
phần chuẩn bị hồ sơ nằm trên form trạm.

Dashboard dùng view HTML/CSS toàn chiều rộng và tự thích ứng theo kích thước
màn hình. Các mã hợp đồng trong bảng cảnh báo mở trực tiếp hồ sơ tương ứng.
