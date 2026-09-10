# Phân quyền tài khoản và người dùng

> Kiểm tra theo working tree ngày 30/07/2026.

## 1. Cách đọc tài liệu

Quyền hiệu lực là kết quả kết hợp của group, ACL, record rule, menu/view và
guard Python. Ẩn menu không thay thế bảo mật backend.

Ký hiệu dùng trong các bảng:

| Ký hiệu | Ý nghĩa |
| --- | --- |
| R | Xem bản ghi |
| C | Tạo bản ghi |
| W | Chỉnh sửa bản ghi |
| D | Xóa bản ghi khỏi database |
| Action | Nút nghiệp vụ được guard Python cho phép |
| — | Không có quyền nghiệp vụ custom |

`Hủy` là chuyển trạng thái nghiệp vụ sang `cancelled`, khác với `D` là xóa
hẳn bản ghi. Một người có quyền bấm **Hủy** không đồng nghĩa có quyền xóa.

## 2. Vai trò và ứng dụng nhìn thấy

| Vai trò | Login demo | Ứng dụng nhìn thấy |
| --- | --- | --- |
| Giám đốc Xí nghiệp (GĐXN) | `enterprise.director.demo` | Chỉ **Quản lý dự án BTS** |
| Kỹ sư giám sát (KSGS) | `ksgs.demo` | Chỉ **Quản lý dự án BTS** |
| Trưởng phòng Kế hoạch | `tpkh.demo` | **Quản lý mua hàng và kho vật tư BTS** |
| Thủ kho | `warehouse.demo` | **Quản lý mua hàng và kho vật tư BTS** |
| Tổ quản lý hạ tầng | `infrastructure.demo` | **Quản lý bảo trì trạm BTS** và **Quản lý hợp đồng BTS** |
| Ban Giám đốc hợp đồng | `bgd.contract.demo` | **Quản lý hợp đồng BTS** |
| DTC Admin | `dtc.admin.demo` | **Settings**, không có app nghiệp vụ DTC |
| System Administrator | Tài khoản tạo DB | Toàn bộ app DTC và app Odoo gốc |

Role GĐXN được giới hạn ở runtime vào đúng cây menu **Quản lý dự án BTS**,
kể cả khi bật developer mode hoặc vô tình có thêm một role nghiệp vụ khác.
System Administrator không bị giới hạn này.

## 3. Group kỹ thuật

| Group XML ID | Vai trò |
| --- | --- |
| `group_bts_enterprise_director` | Giám đốc Xí nghiệp |
| `group_dtc_bts_ksgs` | Kỹ sư giám sát |
| `group_dtc_bts_pkh` | Trưởng phòng Kế hoạch |
| `group_dtc_bts_warehouse` | Thủ kho |
| `group_dtc_bts_infrastructure` | Tổ quản lý hạ tầng |
| `group_dtc_bts_contract_director` | Ban Giám đốc - Hợp đồng BTS |
| `group_dtc_bts_admin` | Quản trị user/group/cấu hình |
| `group_dtc_bts_manager` | Group kỹ thuật/dự phòng, không dùng trong demo |
| `group_show_core_apps` | Chỉ điều khiển root menu Odoo gốc |

GĐXN và Ban Giám đốc hợp đồng là hai vai trò khác nhau:

- GĐXN tạo/quản lý dự án trong phạm vi Xí nghiệp và phân công KSGS.
- BGĐ hợp đồng ký hồ sơ và ra quyết định trong nhánh hợp đồng/gia hạn thất bại.

## 4. Phạm vi dữ liệu

| Vai trò | Phạm vi bản ghi |
| --- | --- |
| GĐXN | Dự án có `enterprise_director_id` là chính mình và toàn bộ trạm/hồ sơ liên quan |
| KSGS | Dự án có `project_manager_id` là chính mình và toàn bộ trạm/hồ sơ liên quan |
| Trưởng phòng Kế hoạch | Yêu cầu vật tư, PO và dữ liệu tham chiếu cần cho luồng mua |
| Thủ kho | Yêu cầu vật tư, PO chỉ đọc, vật tư và phiếu kho cần cho cấp phát |
| Tổ hạ tầng | Hồ sơ bảo trì/hợp đồng thuộc luồng được giao; yêu cầu vật tư do mình tạo |
| BGĐ hợp đồng | Hồ sơ hợp đồng, batch và gia hạn cần ký/ra quyết định |
| DTC Admin | User, group và cấu hình; không có ACL nghiệp vụ custom |
| System Administrator | Không bị giới hạn bởi record rule nghiệp vụ DTC |

## 5. Ma trận CRUD dữ liệu chính

### 5.1. Dự án, trạm và đối tác

| Dữ liệu | GĐXN | KSGS | TPKH | Thủ kho | Tổ hạ tầng | BGĐ HĐ | DTC Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dự án `project.project` | R/C/W | R | R | R | R | R | — |
| Trạm `project.task` | R/C/W | R/C/W | R | R | R | R | — |
| Đối tác `res.partner` | R | R/C/W | R | R | R | R | — |
| Dashboard dự án | R | R/C/W | — | — | — | — | — |

Quy tắc chi tiết:

- GĐXN tạo dự án; hệ thống ép `enterprise_director_id` về chính người tạo.
- Chỉ GĐXN hoặc System Administrator được phân công/đổi KSGS.
- GĐXN không chuyển dự án sang phạm vi GĐXN khác và không xóa dự án/trạm.
- KSGS **không được tạo, sửa hoặc xóa dự án**.
- KSGS được tạo và sửa trạm thuộc dự án được phân công, nhưng không được xóa
  trạm và không truy cập trạm ngoài phạm vi.
- KSGS có thể tạo/sửa đối tác phục vụ hồ sơ; các role tham chiếu chỉ đọc.

### 5.2. Yêu cầu vật tư

| Dữ liệu | GĐXN | KSGS | TPKH | Thủ kho | Tổ hạ tầng | BGĐ HĐ | DTC Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Yêu cầu vật tư | R | R/C/W | R/W | R/W | R/C/W | — | — |
| Dòng yêu cầu | R | R/C/W/D khi `draft` | R/W lượng duyệt | R | R/C/W/D khi `draft` | — | — |
| PO | — | — | Theo quyền Purchase User | R | — | — | — |
| Vật tư | — | Xem gián tiếp | C/R/W/D theo quyền Purchase/Product | R | Xem gián tiếp | — | — |
| Phiếu nhập/xuất | — | — | Không Validate BTS | R/C/W theo quyền Stock | — | — | — |

Không role nghiệp vụ nào được xóa bản ghi yêu cầu vật tư chính. KSGS/Tổ hạ
tầng chỉ thêm, sửa hoặc bớt dòng vật tư khi yêu cầu còn `draft`.

### 5.3. Hợp đồng

| Dữ liệu | GĐXN | KSGS | TPKH | Thủ kho | Tổ hạ tầng | BGĐ HĐ | DTC Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hợp đồng | R | R/C/W có giới hạn | — | — | R/C/W | R/W có giới hạn | — |
| Biên bản đàm phán | R | R/C/W có giới hạn | — | — | R/C/W | R/W có giới hạn | — |
| Batch ký số | R | R/C/W có giới hạn | — | — | R | R/W | — |
| Dòng batch | R | R/C | — | — | R | R/W | — |
| Gia hạn hợp đồng | R | — | — | — | R/C/W | R/W | — |

Không role nghiệp vụ nào có quyền xóa các chứng từ hợp đồng chính. KSGS chỉ
nhập/sửa hồ sơ ban đầu khi còn `draft`; hồ sơ đã đưa vào batch bị khóa.

### 5.4. Bảo trì

| Dữ liệu | GĐXN | KSGS | Tổ hạ tầng | BGĐ HĐ | DTC Admin |
| --- | --- | --- | --- | --- | --- |
| Hồ sơ thiết bị | R | — | R/C/W theo Maintenance Manager | — | — |
| Phiếu bảo trì dự án | R | — | R/C/W, không D | — | — |
| Phiếu kiểm tra/checklist | — | — | R/C/W theo trạng thái | — | — |
| Đề xuất sửa chữa | R | — | R/C/W; quyền D có thể kế thừa từ Maintenance Manager | — | — |

GĐXN chỉ theo dõi dữ liệu bảo trì trong phạm vi dự án của mình; menu vẫn chỉ
nằm trong app Dự án. KSGS không thao tác hồ sơ bảo trì sau khi bàn giao.

## 6. Quyền theo vai trò

### 6.1. Giám đốc Xí nghiệp

Được phép:

- chỉ thấy app **Quản lý dự án BTS**;
- tạo dự án trong phạm vi của chính mình;
- nhập/sửa thông tin và trạng thái dự án;
- phân công hoặc thay đổi KSGS phụ trách;
- tạo/sửa trạm trong dự án thuộc phạm vi;
- xem yêu cầu vật tư, hợp đồng, batch, gia hạn và hồ sơ bảo trì liên quan;
- theo dõi Activity/chatter phân công.

Không được phép:

- xóa dự án hoặc trạm;
- chuyển dự án sang GĐXN khác;
- duyệt yêu cầu vật tư, tạo PO hoặc Validate kho;
- gửi/ký/từ chối hồ sơ hợp đồng;
- xử lý bảo trì;
- ra quyết định hủy theo nhánh hợp đồng nếu không đồng thời là BGĐ hợp đồng.

### 6.2. Kỹ sư giám sát

Được phép:

- chỉ xem dự án được GĐXN phân công;
- tạo/sửa trạm trong dự án được phân công;
- tạo/sửa đối tác và hồ sơ hợp đồng ban đầu theo trạm;
- tạo, thêm/bớt dòng và gửi yêu cầu vật tư từ dự án `approved`;
- hủy yêu cầu do chính mình tạo nếu chưa có phiếu xuất hoàn thành;
- đặt lại yêu cầu `rejected`/`cancelled` về `draft` rồi gửi lại;
- tải scan HĐ thuê đất, BB đàm phán và HĐ cho thuê trạm;
- gửi batch ký số theo dự án khi tất cả trạm đủ hồ sơ;
- báo đàm phán thuê đất thất bại;
- bàn giao dự án sang bảo trì bằng action riêng khi mọi trạm đã
  `handover`/`cancelled`;
- nhận Activity phân công, thông báo vật tư sẵn sàng và kết quả batch.

Không được phép:

- tạo, sửa hoặc xóa dự án;
- tự phân công/đổi KSGS hoặc GĐXN;
- xóa trạm;
- duyệt yêu cầu, tạo PO, nhập/xuất kho;
- submit/ký/từ chối từng hợp đồng hoặc biên bản riêng lẻ;
- ký batch/gia hạn;
- tiếp nhận hoặc xử lý bảo trì.

### 6.3. Trưởng phòng Kế hoạch

- Chỉ đọc dự án/trạm làm tham chiếu.
- Xem, duyệt hoặc từ chối yêu cầu vật tư; nhập số lượng duyệt.
- Chọn nhà cung cấp, tạo và xử lý PO.
- Có thể hủy yêu cầu chưa có phiếu xuất hoàn thành.
- Không thêm/xóa dòng yêu cầu của requester; chỉ sửa lượng duyệt.
- Thấy menu nhập/xuất để theo dõi nhưng không được tạo hoặc Validate phiếu kho BTS.
- Không thao tác hợp đồng, bảo trì hoặc dữ liệu dự án/trạm.

### 6.4. Thủ kho

- Chỉ đọc dự án/trạm, PO, dòng PO và danh mục vật tư.
- Xem/cập nhật yêu cầu phục vụ cấp phát nhưng không sửa dòng nhu cầu.
- Tạo phiếu xuất từ yêu cầu; kiểm tra tồn, giữ hàng và Validate picking.
- Nhập kho theo receipt của PO.
- Có thể hủy yêu cầu chưa có phiếu xuất hoàn thành.
- Không duyệt yêu cầu, tạo/sửa PO hoặc tạo/sửa/xóa vật tư.

### 6.5. Tổ quản lý hạ tầng

- Chỉ đọc dữ liệu nền dự án/trạm.
- Tiếp nhận bàn giao, tạo hồ sơ thiết bị và phiếu bảo trì.
- Sinh checklist, nhập kết quả, tạo/xử lý đề xuất sửa chữa.
- Tạo yêu cầu vật tư từ đề xuất; thêm/bớt dòng khi `draft`, gửi và gửi lại.
- Theo dõi hợp đồng đến hạn; khởi tạo/nhập điều khoản/tải scan gia hạn.
- Gửi hồ sơ gia hạn cho BGĐ ký.
- Không tạo PO, Validate kho hoặc ký số.

### 6.6. Ban Giám đốc hợp đồng

- Chỉ đọc dữ liệu nền dự án/trạm/đối tác.
- Ký từng dòng batch, từ chối batch trước khi có dòng đã ký và hoàn thành
  batch khi mọi dòng đã ký.
- Ký hoặc từ chối hồ sơ gia hạn; phải nhập lý do khi từ chối.
- Sau báo cáo thất bại hợp lệ, quyết định hủy trạm hoặc hủy dự án.
- Không tạo dự án/trạm, yêu cầu vật tư, PO hoặc hồ sơ bảo trì.

### 6.7. DTC Admin và System Administrator

- DTC Admin quản lý user/group/cấu hình trong Settings nhưng không chạy thay
  workflow nghiệp vụ.
- System Administrator có toàn bộ ACL System, bỏ qua record rule nghiệp vụ và
  được phép qua các guard có ngoại lệ `base.group_system`.

## 7. Ma trận action nghiệp vụ

| Action | GĐXN | KSGS | TPKH | Thủ kho | Tổ hạ tầng | BGĐ HĐ | System |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Tạo dự án | Có | Không | Không | Không | Không | Không | Có |
| Sửa thông tin/trạng thái dự án | Có | Không | Không | Không | Không | Không | Có |
| Phân công/đổi KSGS | Có | Không | Không | Không | Không | Không | Có |
| Tạo/sửa trạm | Có | Có | Không | Không | Không | Không | Có |
| Xóa dự án/trạm | Không | Không | Không | Không | Không | Không | Có |
| Tạo/gửi yêu cầu vật tư dự án | Không | Có | Không | Không | Không | Không | Có |
| Duyệt/từ chối yêu cầu | Không | Không | Có | Không | Không | Không | Có |
| Hủy yêu cầu chưa xuất hoàn thành | Chỉ đọc | Nếu là requester | Có | Có | Nếu là requester | Không | Có |
| Tạo PO | Không | Không | Có | Không | Không | Không | Có |
| Tạo/Validate phiếu kho BTS | Không | Không | Không | Có | Không | Không | Có |
| Nhập hồ sơ hợp đồng ban đầu | Chỉ đọc | Có | Không | Không | Không | Không | Có |
| Gửi batch ban đầu | Không | Có | Không | Không | Không | Không | Có |
| Ký/từ chối/hoàn thành batch | Không | Không | Không | Không | Không | Có | Có |
| Báo đàm phán đất thất bại | Không | Có | Không | Không | Không | Không | Có |
| Quyết định hủy trạm/dự án do đàm phán thất bại | Không | Không | Không | Không | Không | Có | Có |
| Bàn giao dự án sang bảo trì | Không | Có | Không | Không | Không | Không | Có |
| Tiếp nhận bàn giao | Không | Không | Không | Không | Có | Không | Có |
| Tạo/xử lý phiếu bảo trì, sửa chữa | Chỉ đọc | Không | Không | Không | Có | Không | Có |
| Tạo/gửi yêu cầu vật tư sửa chữa | Không | Không | Không | Không | Có | Không | Có |
| Tạo/chuẩn bị/gửi gia hạn | Chỉ đọc | Không | Không | Không | Có | Không | Có |
| Ký/từ chối gia hạn | Chỉ đọc | Không | Không | Không | Không | Có | Có |
| Báo không gia hạn được | Không | Không | Không | Không | Có | Không | Có |
| Quyết định hủy trạm/dự án do không gia hạn | Không | Không | Không | Không | Không | Có | Có |

Các guard action chạy ở Python nên gọi RPC/URL trực tiếp không vượt qua được.

## 8. Hủy dự án và hủy trạm

Có hai khái niệm cần phân biệt:

1. GĐXN có quyền sửa trường `project.project.state`, bao gồm đặt dự án thành
   `cancelled`, vì GĐXN là chủ dữ liệu dự án.
2. Nhánh hủy do hợp đồng/gia hạn thất bại là workflow có báo cáo, lý do,
   người ra quyết định, email và cập nhật liên quan. Chỉ BGĐ hợp đồng hoặc
   System Administrator chạy được action này.

KSGS không còn quyền write dự án nên không thể tự đặt dự án thành
`cancelled`. KSGS chỉ có thể báo đàm phán thất bại để BGĐ hợp đồng quyết định.

Trạng thái `project.task.station_state = cancelled` vẫn tồn tại. KSGS/GĐXN
có quyền sửa trạm trong phạm vi; action hủy do hợp đồng thất bại vẫn chỉ dành
cho BGĐ hợp đồng và lưu đầy đủ dấu vết quyết định.

## 9. Kỹ thuật viên thuê ngoài

KTV thuê ngoài chỉ là `res.partner` với
`partner_type = external_technician`, không có `res.users`.

Tổ hạ tầng kiểm tra kết quả từ biểu mẫu ngoài hệ thống rồi nhập/xác nhận lại
trên Odoo.

## 10. Kiểm tra sau khi đổi quyền

1. Upgrade `dtc_bts_base`, `dtc_bts_maintenance` và
   `dtc_bts_menu_visibility`.
2. Đăng xuất/đăng nhập lại để làm mới session và menu cache.
3. GĐXN phải chỉ thấy app Dự án, tạo/sửa dự án và phân công KSGS được.
4. KSGS phải thấy dự án được giao nhưng không có quyền tạo/sửa/xóa dự án.
5. KSGS phải tạo/sửa được trạm trong dự án được giao.
6. KSGS vẫn tạo/gửi yêu cầu vật tư, gửi batch và bàn giao bảo trì được.
7. Thử RPC trực tiếp để xác nhận ACL/record rule/guard backend cùng chặn.
8. System Administrator vẫn phải thao tác được toàn hệ thống.
