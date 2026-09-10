# Mapping Odoo cho hệ thống DTC BTS

> Kiểm tra theo working tree ngày 30/07/2026.

## 1. Mục đích tài liệu

Tài liệu này ánh xạ giữa nghiệp vụ thực tế, quy trình TO-BE và các
module/model/chức năng Odoo đang được triển khai trong repo. Tên model, field,
trạng thái và vai trò trong tài liệu bám theo source hiện tại; nội dung chưa có
trong source được ghi rõ là **Chưa triển khai** hoặc **Ngoài phạm vi demo hiện
tại**.

## 2. Tổng quan mapping module

| Nghiệp vụ | Module Odoo/custom module sử dụng | Model chính | Vai trò sử dụng | Mô tả mapping |
| --- | --- | --- | --- | --- |
| Quản lý vòng đời dự án và trạm BTS | `project`, `contacts`, `dtc_bts_base` | `project.project`, `project.task`, `res.partner`, `dtc.bts.dashboard` | GĐXN; KSGS; System Administrator | GĐXN tạo/sửa dự án và phân công; KSGS chỉ đọc dự án nhưng tạo/sửa các task đại diện cho trạm BTS. |
| Quản lý mua hàng và xuất nhập kho vật tư | `purchase`, `stock`, `product`, `dtc_bts_inventory` | `bts.material.request`, `bts.material.request.line`, `purchase.order`, `stock.picking`, `stock.move`, `product.template`, `product.product` | KSGS/Tổ hạ tầng yêu cầu; PKH duyệt và mua; Thủ kho nhập/xuất | Yêu cầu vật tư custom nối luồng dự án/bảo trì với quy trình mua và kho chuẩn của Odoo. |
| Quản lý bảo trì trạm BTS | `maintenance`, `mail`, `dtc_bts_maintenance` | `maintenance.equipment`, `bts.maintenance.batch`, `maintenance.request`, `bts.maintenance.checklist.item`, `bts.maintenance.checklist.result`, `bts.repair.proposal` | Tổ quản lý hạ tầng; KSGS bàn giao; System Administrator | Hồ sơ thiết bị neo theo trạm; phiếu bảo trì dự án sinh các phiếu kiểm tra trạm, checklist và đề xuất sửa chữa. |
| Quản lý hợp đồng trạm BTS | `mail`, `dtc_bts_contract` | `bts.contract`, `bts.negotiation.minutes`, `bts.contract.signature.batch`, `bts.contract.signature.batch.line`, `bts.contract.renewal` | KSGS; Tổ hạ tầng; BGĐ hợp đồng; System Administrator | Hồ sơ hợp đồng gắn trực tiếp với từng trạm; ký số gom theo batch dự án và gia hạn theo từng hợp đồng. |
| Phân quyền và ẩn/hiện ứng dụng | `base`, security của năm module custom, `dtc_bts_menu_visibility` | `res.users`, `res.groups`, `ir.model.access`, `ir.rule`, `ir.ui.menu` | Tất cả vai trò; DTC Admin; System Administrator | Group nghiệp vụ, ACL, record rule, giới hạn view/button và guard Python bảo vệ backend; module visibility thu gọn app switcher. |

## 3. Mapping nghiệp vụ Quản lý vòng đời dự án và trạm BTS

`dtc_bts_base` kế thừa model chuẩn thay vì tạo bảng dự án/trạm độc lập. Dự án
BTS là `project.project`; mỗi trạm BTS là một `project.task` thuộc dự án qua
`project_id`. `project.task` cũng là điểm neo để kho, bảo trì và hợp đồng cùng
tham chiếu tới một trạm thống nhất.

| Thành phần nghiệp vụ | Cách thể hiện trên Odoo | Model/field liên quan | Ghi chú |
| --- | --- | --- | --- |
| Dự án BTS | Bản ghi dự án | `project.project`; `project_code`, `name` | `project_code` bắt buộc, duy nhất và sinh bằng sequence. |
| Trạm BTS | Task thuộc dự án | `project.task`; `project_id`, `station_code`, `name` | `station_code` bắt buộc, duy nhất và sinh bằng sequence. |
| Loại trạm | Phân loại ở cấp dự án | `project.project.station_type`: `macro`, `cell` | Trạm đọc lại qua `project.task.project_station_type`; một dự án hiện mang một loại trạm. |
| Địa bàn dự án | Tỉnh/thành, quận/huyện, xã/phường | `province`, `district`, `commune` | Trạm có các field related `project_province`, `project_district`, `project_commune`. |
| Vị trí trạm | Địa chỉ và tọa độ | `project.task.site_address`, `latitude`, `longitude` | Source kiểm tra miền hợp lệ của vĩ độ và kinh độ. |
| Đối tác viễn thông | Contact được phân loại | `project.project.telecom_partner_id` → `res.partner`; `partner_type = telecom_partner` | `res.partner.partner_type` còn có `supplier`, `landowner`, `external_technician`, `other`. |
| Người phụ trách dự án/trạm | User nội bộ | `project_manager_id`, `assigned_user_id`, `user_ids` | Khi chọn `assigned_user_id`, onchange đồng bộ user được giao trên task. |
| Mốc thời gian | Kế hoạch và nghiệm thu | `planned_start_date`, `planned_end_date`, `project.project.acceptance_date`, `project.task.acceptance_date` | Ngày nghiệm thu dự án neo lịch bảo trì đầu tiên; ngày nghiệm thu trạm mở HĐ cho thuê trạm. Ngày kết thúc dự kiến không được trước ngày bắt đầu. |
| Trạng thái dự án | Selection trên form dự án | `project.project.state` | Tự tổng hợp khi tất cả trạm cùng trạng thái; toàn bộ trạm đạt `contracted` đưa dự án sang `approved`. |
| Trạng thái trạm | Selection theo vòng đời trạm | `project.task.station_state` | Batch ký số giai đoạn 1 đưa trạm tới `contracted`; giai đoạn 2 đưa tới `station_lease_signed`. |
| Trạng thái bàn giao trạm | Theo dõi mức sẵn sàng/tiếp nhận | `project.task.handover_state` | Khác với `project.project.maintenance_handover_state`, là trạng thái bàn giao cả dự án sang bảo trì. |
| Dashboard dự án | Root app **Quản lý dự án BTS** và menu **Bảng tổng hợp** | `dtc.bts.dashboard` | Tổng hợp dự án/trạm, Macro/Cell, tiến độ; hiển thị thông báo vật tư `ready` và batch ký đủ cho KSGS. |
| Hồ sơ hợp đồng theo trạm | Tab **Hồ sơ hợp đồng** trên form trạm và tab tổng hợp **Hợp đồng trạm** trên dự án | `project.task` cùng `land_contract_id`, `negotiation_minutes_id`, `station_lease_contract_id` và ba field file scan | KSGS sửa trạm để chuẩn bị hồ sơ; form dự án chỉ tổng hợp và gửi batch. |
| Liên kết kho | Smart button/tác vụ tạo yêu cầu từ dự án | `project.project.bts_material_request_ids`, `bts_material_request_count` | Chỉ tạo từ dự án ở trạng thái `approved`; chứng từ dùng `bts_project_id`. |
| Liên kết bảo trì | Bàn giao, hồ sơ thiết bị và phiếu bảo trì | `maintenance_handover_state`, `bts_maintenance_equipment_ids`, `bts_maintenance_batch_ids` | Bàn giao chính của demo diễn ra ở cấp dự án; hồ sơ thiết bị lại neo từng trạm. |
| Liên kết hợp đồng | Hợp đồng/biên bản gắn trạm; chỉ số hạn tổng hợp lên dự án | `bts.contract.station_id`, `bts.negotiation.minutes.station_id`; các field `contract_*` trên `project.project` | Form **Danh sách dự án** trong app Hợp đồng là form riêng để theo dõi hạn, không phải form nghiệp vụ của KSGS. |

Menu app dự án gồm **Bảng tổng hợp**, **Danh sách dự án**, **Danh sách trạm
BTS** và **Đối tác**. Root app hiện cho GĐXN, KSGS và System Administrator;
GĐXN bị giới hạn runtime chỉ vào cây app này.

## 4. Mapping nghiệp vụ Quản lý mua hàng và kho vật tư

Yêu cầu vật tư custom là lớp điều phối giữa dự án/bảo trì và các chứng từ chuẩn
Purchase/Inventory. `purchase.order`, `purchase.order.line`, `stock.picking` và
`stock.move` được mở rộng bằng các field tham chiếu DTC BTS.

| Nghiệp vụ thực tế | Chức năng Odoo | Model | Người thao tác | Cải tiến so với Excel/Zalo |
| --- | --- | --- | --- | --- |
| Lập nhu cầu vật tư thi công | Nút tạo yêu cầu từ dự án; nhập các dòng số lượng | `bts.material.request`, `bts.material.request.line`; `source = project_construction` | KSGS | Yêu cầu gắn mã dự án, người yêu cầu và lịch sử trạng thái; không phải ghép file/chat thủ công. |
| Lập nhu cầu sửa chữa | Tạo yêu cầu từ đề xuất sửa chữa | `bts.repair.proposal` → `bts.material.request`; `source = maintenance`, `repair_proposal_id`, `station_id` | Tổ hạ tầng | Truy vết được từ checklist lỗi đến đề xuất, yêu cầu và phiếu xuất. |
| Gửi yêu cầu | Action từ `draft` sang `requested` | `bts.material.request.action_submit()` | KSGS hoặc Tổ hạ tầng | Workflow và chatter lưu dấu thay vì nhắn Zalo rời rạc. |
| Duyệt/từ chối | Nhập `quantity_approved`, duyệt hoặc ghi `rejection_reason` | `bts.material.request` và dòng yêu cầu | PKH | Tách rõ số lượng yêu cầu, số lượng duyệt, tồn khả dụng và cần mua. |
| Kiểm tra thiếu tồn | `_refresh_supply_state()` tính trạng thái cung ứng | `quantity_available`, `quantity_to_purchase`, `quantity_issued` | Hệ thống; PKH theo dõi | Trạng thái phản ánh tồn và PO đang mở, giảm tổng hợp Excel thủ công. |
| Mua bổ sung | Chọn `vendor_id`, tạo PO từ phần còn thiếu | `purchase.order`, `purchase.order.line.bts_material_request_line_id` | PKH | PO giữ liên kết hai chiều với yêu cầu và dự án. |
| Nhập hàng | PO sinh receipt có thông tin dự án/yêu cầu | `stock.picking`; `picking_type_code = incoming` | Thủ kho | Chỉ khi receipt của PO gắn đúng yêu cầu đã nhận đủ số lượng duyệt, hệ thống mới cho phép cấp phát. |
| Xuất/cấp phát | Tạo outgoing picking từ số lượng còn thiếu và tồn khả dụng; tự confirm/assign | `stock.picking`, `stock.move`; `picking_type_code = outgoing` | Thủ kho | Phiếu tự lấy dòng yêu cầu, không cần nhập lại sản phẩm; Validate chặn tổng lượng vượt phần duyệt còn lại. |
| Danh mục vật tư | Sản phẩm được đánh dấu dùng cho BTS | `product.template.is_bts_material`, `product.product.is_bts_material` | PKH thao tác; Thủ kho chỉ đọc | Dùng chung Product/UoM chuẩn, lọc đúng vật tư BTS; guard Python chặn Thủ kho tạo/sửa/xóa. |
| Thông báo workflow | Tạo thông báo khi chờ duyệt, PO chờ nhập, sẵn sàng cấp phát và chờ khóa PO | `bts.material.notification`; `approval`, `incoming`, `ready`, `lock_po` | PKH, Thủ kho hoặc requester theo từng bước | Dashboard Kho và Dự án hiển thị đúng công việc cho từng vai trò. |

Luồng trạng thái chính là `draft` → `requested` → `waiting_purchase` →
`purchasing` → `ready` → `partially_delivered`/`issued`. Nhánh ngoại lệ dùng
`rejected` hoặc `cancelled`. `ready` chỉ phát sinh sau khi receipt của các PO
gắn đúng yêu cầu đã nhận đủ; tồn kho chung không làm yêu cầu tự nhảy trạng thái.

Menu app kho được phân vai rõ: PKH tạo/xử lý **Đơn mua hàng** nhưng không thấy
**Nhập kho/Xuất kho**. Thủ kho thấy **Yêu cầu cấp phát**, **Đơn mua hàng**,
**Nhập kho**, **Xuất kho** và **Danh mục vật tư**; PO và danh mục vật tư chỉ
đọc. ACL và guard Python vẫn kiểm tra quyền nếu model/action được gọi trực tiếp.

## 5. Mapping nghiệp vụ Quản lý bảo trì trạm BTS

| Hạng mục nghiệp vụ | Odoo xử lý bằng gì | Model/field/state | Vai trò |
| --- | --- | --- | --- |
| Bàn giao dự án sang bảo trì | KSGS bàn giao, Tổ hạ tầng tiếp nhận ở cấp dự án | `project.project.maintenance_handover_state`, `maintenance_handover_date`, `maintenance_handover_by_id`, `maintenance_accepted_by_id`, `maintenance_accepted_date` | KSGS; Tổ hạ tầng |
| Hồ sơ thiết bị theo trạm | Mỗi trạm có tối đa một equipment | `maintenance.equipment.station_id`, `bts_project_id`, `effective_date`, `next_action_date`, `bts_state` | Tổ hạ tầng |
| Tạo hồ sơ hàng loạt | Wizard sinh equipment cho các trạm đủ điều kiện | `bts.maintenance.equipment.bulk.wizard`; `effective_date = project_id.acceptance_date` | Tổ hạ tầng; chặn nếu dự án chưa nghiệm thu |
| Phiếu bảo trì dự án | Một batch gom các trạm của dự án và chu kỳ 1/3/6 tháng | `bts.maintenance.batch`; `project_id`, `maintenance_cycle_months`, `state` | Tổ hạ tầng |
| Phiếu kiểm tra từng trạm | Batch sinh một request cho mỗi equipment/trạm | `maintenance.request`; `maintenance_batch_id`, `station_id`, `station_page_state` | Tổ hạ tầng nhập/xác nhận |
| Checklist mẫu | Danh mục theo loại equipment và tần suất | `bts.maintenance.checklist.item`; `category_id`, `frequency_months`, `is_external_required` | Tổ hạ tầng |
| Kết quả checklist | Dòng kết quả theo request/hạng mục | `bts.maintenance.checklist.result`; `result_state`, `measurement_value`, `note`, `is_resolved` | Tổ hạ tầng |
| Ghi nhận lỗi | `need_repair` hoặc `need_replacement` làm `has_failure = True` khi chưa xử lý | `maintenance.request.has_failure`, `bts.maintenance.checklist.result.result_state` | Hệ thống tính; Tổ hạ tầng kiểm tra |
| Đề xuất sửa chữa | Gom các checklist lỗi của một request hoặc một batch | `bts.repair.proposal`, `bts.repair.proposal.line` | Tổ hạ tầng |
| Vật tư sửa chữa | Dòng vật tư đề xuất sinh yêu cầu nguồn bảo trì | `bts.repair.proposal.material.line` → `bts.material.request`; `source = maintenance` | Tổ hạ tầng tạo; PKH/Thủ kho xử lý |
| Hoàn tất sửa chữa | Cập nhật kết quả, đóng lỗi checklist và lịch sử equipment | `repair_result`, `repair_completed_date`, `is_resolved`, `last_repair_date`, `last_repair_note` | Tổ hạ tầng |
| Nhắc lịch | Scheduled action tạo `mail.activity` trước hạn 3 ngày | `maintenance.equipment.next_action_date` | Hệ thống; user kỹ thuật/Tổ hạ tầng nhận |
| KTV thuê ngoài | Lưu như đối tác và chọn trên phiếu trạm | `res.partner` với `partner_type = external_technician`; `executor_type = external`, `external_technician_partner_id` | Tổ hạ tầng nhập/xác nhận lại |

KTV thuê ngoài hiện không phải `res.users`, không có tài khoản nội bộ hoặc
portal. Kết quả từ sheet/form ngoài Odoo do Tổ hạ tầng kiểm tra rồi nhập hoặc
xác nhận lại. Portal cho KTV thuê ngoài: **Chưa triển khai**.

Model `bts.station.handover` có trong module hợp đồng để lưu hồ sơ bàn giao từng
trạm, nhưng luồng bàn giao sang bảo trì và menu demo hiện dùng các field
`maintenance_handover_*` trên `project.project`.

## 6. Mapping nghiệp vụ Quản lý hợp đồng trạm BTS

Mọi `bts.contract` và `bts.negotiation.minutes` đều bắt buộc gắn
`station_id`; `project_id` là field related từ trạm. Vì vậy hợp đồng không được
gắn chung ở cấp dự án.

| Hồ sơ/nghiệp vụ | Model Odoo | Trạng thái chính | Người xử lý | Quy tắc nghiệp vụ |
| --- | --- | --- | --- | --- |
| Hợp đồng thuê đất | `bts.contract`; `contract_type = land_lease` | `draft`, `submitted`, `active`, `renewal_agreed`, `liquidated`, `expired`, `cancelled` | KSGS nhập ban đầu; Tổ hạ tầng xử lý hồ sơ lẻ và gia hạn; BGĐ ký | Đối tác nếu đã phân loại phải là `landowner`; mỗi trạm chỉ có một hợp đồng theo loại. |
| Hợp đồng cho thuê trạm | `bts.contract`; `contract_type = infrastructure_lease` | Như hợp đồng thuê đất | KSGS nhập sau nghiệm thu trạm; BGĐ ký | `related_land_contract_id` bắt buộc khi rời draft; nếu có liên kết thì luôn phải là HĐ thuê đất cùng `station_id`; thời hạn cho thuê trạm không được vượt HĐ thuê đất. |
| Biên bản đàm phán | `bts.negotiation.minutes` | `draft`, `pending_approval`, `confirmed`, `rejected`; `converted` chỉ giữ cho dữ liệu legacy | KSGS nhập ban đầu; Tổ hạ tầng trình; BGĐ xác nhận/từ chối | Biên bản là hồ sơ riêng, không tự chuyển thành hợp đồng trong luồng hiện tại. |
| Tab **Hồ sơ hợp đồng** | Mở rộng form `project.task` | `land_contract_dossier_state`, `negotiation_dossier_state`, `station_lease_dossier_state`, `digital_signature_state` | KSGS | Tải scan HĐ thuê đất, BB đàm phán, HĐ cho thuê trạm; hệ thống tạo/đồng bộ hồ sơ dự thảo. |
| Batch ký số theo dự án | `bts.contract.signature.batch` | `draft`, `submitted`, `partially_signed`, `done`, `rejected` | KSGS tạo/gửi; BGĐ ký/từ chối/hoàn tất | `phase_1` gom HĐ thuê đất + BB; `phase_2` gom HĐ cho thuê trạm. Chỉ hoàn tất khi mọi line đã ký. |
| Dòng hồ sơ ký số | `bts.contract.signature.batch.line` | `pending`, `signed`, `rejected` | BGĐ hợp đồng | `document_type` xác định hợp đồng hoặc biên bản; phải tải file đã ký trước `action_sign()`. |
| Gia hạn hợp đồng | `bts.contract.renewal` | `draft`, `in_progress`, `pending_signature`, `completed`, `rejected`, `cancelled` | Tổ hạ tầng theo dõi, khởi tạo, nhập điều khoản và gửi ký; BGĐ ký/từ chối | Phải có file scan, ngày ký/hiệu lực/hết hạn mới; khi ký, cập nhật hợp đồng về `active`. |
| Theo dõi đến hạn | Dashboard và form dự án riêng trong app Hợp đồng | `days_to_expiration`, `is_expiring_soon`, `is_expiring_within_30_days`; các field `contract_due_*` | Tổ hạ tầng, BGĐ | Cron cập nhật hợp đồng quá hạn và tạo `mail.activity`; dashboard có KPI/cảnh báo. |
| Hồ sơ bàn giao trạm | `bts.station.handover` | `draft`, `handed_over`, `cancelled` | Model đã có | Không phải luồng bàn giao bảo trì chính trong demo hiện tại. |

KSGS chỉ chuẩn bị hồ sơ và gửi batch từ app **Quản lý dự án BTS**. KSGS không
có menu app **Quản lý hợp đồng BTS** và không ký hồ sơ. BGĐ xử lý ký số tại
menu **Ký số hợp đồng**, gồm batch ban đầu và hồ sơ gia hạn chờ ký. Tổ hạ
tầng và BGĐ thấy **Tổng quan**,
**Danh sách dự án**, **Gia hạn hợp đồng** theo quyền dữ liệu/action cụ thể.
PKH không thấy app Hợp đồng.

Các trạng thái tổng hợp trên tab của KSGS là:

- `land_contract_dossier_state`: `missing`, `uploaded`, `submitted`, `signed`,
  `active`, `closed`;
- `negotiation_dossier_state`: `missing`, `uploaded`, `pending_approval`,
  `confirmed`, `converted`, `rejected`;
- `station_lease_dossier_state`: `not_ready`, `missing`, `uploaded`,
  `submitted`, `signed`, `active`, `closed`;
- `digital_signature_state`: `not_ready`, `pending`, `partial`, `completed`.

Tổ hạ tầng chạy `action_start()` và `action_complete()`; BGĐ chạy
`action_sign_signature()` hoặc `action_reject_signature()`. PKH không tham gia
phân hệ Hợp đồng.

## 7. Mapping phân quyền người dùng

| Vai trò | User demo | App nhìn thấy | Chức năng được làm | Chức năng không được làm |
| --- | --- | --- | --- | --- |
| Giám đốc Xí nghiệp | `enterprise.director.demo` | Chỉ Quản lý dự án BTS | Tạo/sửa dự án trong phạm vi; phân công KSGS; tạo/sửa trạm; theo dõi hồ sơ liên quan | Không xóa dự án/trạm; không duyệt kho, ký hợp đồng hoặc xử lý bảo trì |
| KSGS | `ksgs.demo` | Quản lý dự án BTS | Chỉ đọc dự án được giao; tạo/sửa trạm; tạo/gửi yêu cầu vật tư dự án; bàn giao bảo trì; nhập hồ sơ hợp đồng theo trạm và gửi batch | Không tạo/sửa/xóa dự án; không xóa trạm; không duyệt/mua/xuất vật tư; không tiếp nhận bảo trì; không ký hợp đồng |
| Trưởng phòng Kế hoạch | `tpkh.demo` | Quản lý mua hàng và kho vật tư BTS | Duyệt/từ chối yêu cầu; nhập lượng duyệt; tạo/xử lý PO; theo dõi phiếu nhập/xuất | Không tạo hoặc xác nhận phiếu kho; không sửa dự án/trạm; không thấy app Hợp đồng |
| Thủ kho | `warehouse.demo` | Quản lý mua hàng và kho vật tư BTS | Xem yêu cầu, PO và danh mục vật tư; nhập/xuất kho; tạo phiếu xuất và xác nhận picking BTS | Không duyệt yêu cầu; không tạo/sửa PO; không tạo/sửa/xóa vật tư; không thấy app Dự án/Bảo trì/Hợp đồng |
| Tổ quản lý hạ tầng | `infrastructure.demo` | Quản lý bảo trì trạm BTS; Quản lý hợp đồng BTS | Tiếp nhận bàn giao; quản lý equipment/batch/checklist/sửa chữa; tạo yêu cầu vật tư sửa chữa; theo dõi, khởi tạo, nhập điều khoản, tải scan và gửi ký gia hạn | Không thao tác kho/PO; không ký số; không sửa dữ liệu nền dự án/trạm |
| Ban Giám đốc hợp đồng | `bgd.contract.demo` | Quản lý hợp đồng BTS | Ký/từ chối line và batch; ký/từ chối biên bản, hợp đồng, gia hạn; thanh lý hợp đồng | Không tạo hồ sơ nghiệp vụ ban đầu; không thấy app Dự án/Kho/Bảo trì; chưa duyệt đề xuất sửa chữa |
| DTC Admin | `dtc.admin.demo` | Settings | Quản trị user, group và cấu hình quyền | Không phải actor nghiệp vụ; không thấy các app nghiệp vụ DTC và không được guard cho chạy thay vai trò |
| System Administrator | Tài khoản thuộc `base.group_system` | Toàn bộ app DTC và app Odoo gốc | Có ACL System, qua ngoại lệ guard, thấy Apps/Settings/Technical; phục vụ dev/demo | Không bị giới hạn như user demo; cần dùng có kiểm soát |

Các group nghiệp vụ chính là `group_dtc_bts_ksgs`, `group_dtc_bts_pkh`,
`group_dtc_bts_warehouse`, `group_dtc_bts_infrastructure`,
`group_dtc_bts_contract_director` và `group_dtc_bts_admin`.
`group_dtc_bts_manager` chỉ còn là group kỹ thuật/dự phòng, không dùng trong
luồng demo; `manager.demo` bị vô hiệu hóa.

> Ẩn menu không thay thế bảo mật backend. Quyền thực tế là tổ hợp của group,
> ACL, record rule, giới hạn menu/view/button và guard Python. Không cộng group
> tùy tiện để “chữa” lỗi quyền vì có thể làm lộ app hoặc mở rộng ACL ngoài vai
> trò dự kiến.

`dtc_bts_menu_visibility.group_show_core_apps` chỉ điều khiển việc nhìn thấy
Discuss, To-do, Project, Purchase, Inventory, Maintenance, Accounting,
Spreadsheet Dashboard, Apps, Settings và Technical/Tests. System
Administrator kế thừa group này; DTC Admin chỉ được thêm riêng vào Settings.

## 8. Mapping trạng thái nghiệp vụ

### 8.1 Trạng thái dự án `project.project.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Dự thảo | Hồ sơ dự án mới | GĐXN |
| `survey` | Khảo sát | Đang khảo sát dự án | GĐXN |
| `approved` | Đã phê duyệt | Tất cả trạm đã ký HĐ thuê đất và biên bản đàm phán; KSGS được tạo yêu cầu vật tư | Hệ thống tổng hợp từ trạm |
| `in_progress` | Đang triển khai | Dự án đang thi công/triển khai | GĐXN |
| `done` | Hoàn thành | Dự án đã hoàn thành | GĐXN |
| `cancelled` | Đã hủy | Dự án dừng thực hiện | GĐXN hoặc workflow quyết định của BGĐ hợp đồng |

Trạng thái dự án được hệ thống tổng hợp khi tất cả trạm cùng trạng thái. Nếu
các trạm ở nhiều trạng thái khác nhau, dự án giữ nguyên trạng thái hiện tại.

### 8.2 Trạng thái trạm `project.task.station_state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `survey` | Khảo sát | Trạm mới/đang khảo sát | KSGS |
| `negotiating` | Đàm phán | Đang chuẩn bị thỏa thuận/hồ sơ | KSGS |
| `contracted` | Đã kí hợp đồng thuê đất và biên bản đàm phán | Batch giai đoạn 1 đã ký đủ và hoàn tất | Hệ thống theo action của BGĐ |
| `construction` | Thi công | Trạm đang thi công | KSGS |
| `acceptance` | Nghiệm thu | Trạm đang/đã qua bước nghiệm thu | KSGS |
| `station_lease_signed` | Đã kí hợp đồng cho thuê trạm | Batch giai đoạn 2 đã ký đủ và hoàn tất | Hệ thống theo action của BGĐ |
| `handover` | Bàn giao hồ sơ | Trạm chuyển sang bước bàn giao | KSGS/Tổ hạ tầng theo luồng |
| `operating` | Vận hành | Trạm được tiếp nhận vận hành | Tổ hạ tầng |
| `cancelled` | Hủy | Giá trị legacy, không thuộc luồng chính | KSGS/System |

### 8.3 Trạng thái yêu cầu vật tư `bts.material.request.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Nháp | Người yêu cầu đang nhập dòng vật tư | KSGS/Tổ hạ tầng |
| `requested` | Đã gửi | Chờ PKH xem xét | KSGS/Tổ hạ tầng gửi |
| `approved` | Đã duyệt | PKH đã duyệt số lượng | PKH |
| `waiting_purchase` | Chờ mua hàng / bổ sung vật tư | Đã duyệt, chờ tạo/xác nhận PO | Hệ thống/PKH |
| `purchasing` | Đang mua hàng | PO đã xác nhận, Thủ kho chờ hàng về và nhập kho | PKH/Thủ kho |
| `ready` | Sẵn sàng cấp phát | PO gắn với yêu cầu đã được nhập đủ số lượng duyệt | Hệ thống; Thủ kho xử lý |
| `partially_delivered` | Cấp phát một phần | Đã xuất một phần số lượng duyệt | Hệ thống; Thủ kho |
| `issued` | Hoàn tất yêu cầu | Đã xuất đủ số lượng duyệt; PKH khóa PO để kết thúc | Hệ thống; Thủ kho/PKH |
| `rejected` | Từ chối | PKH từ chối và ghi lý do | PKH |
| `cancelled` | Hủy | Yêu cầu bị hủy hợp lệ | Người yêu cầu/PKH/Thủ kho theo guard |

### 8.4 Trạng thái phiếu bảo trì `bts.maintenance.batch.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Nháp | Đang khai báo dự án, ngày và chu kỳ | Tổ hạ tầng |
| `generated` | Đã sinh danh sách trạm | Đã tạo request/checklist cho các trạm | Tổ hạ tầng |
| `in_progress` | Đang kiểm tra | Ít nhất một trạm bắt đầu kiểm tra | Tổ hạ tầng |
| `submitted` | Chờ tổ hạ tầng kiểm tra | Tất cả trạm đã hoàn tất hoặc có lỗi và phiếu được gửi kiểm tra | Tổ hạ tầng |
| `reviewed` | Đã kiểm tra kết quả | Kết quả đã được xác nhận | Tổ hạ tầng |
| `done` | Hoàn tất | Phiếu kết thúc; không còn lỗi sửa chữa chưa xử lý | Tổ hạ tầng |
| `cancelled` | Đã hủy | Phiếu dừng xử lý | Tổ hạ tầng |

### 8.5 Trạng thái đề xuất sửa chữa `bts.repair.proposal.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Nháp | Đề xuất mới từ checklist lỗi | Tổ hạ tầng |
| `confirmed` | Đã xác nhận | Đã xác nhận và có nhu cầu vật tư | Tổ hạ tầng |
| `waiting_material` | Chờ vật tư | Yêu cầu vật tư đang xử lý | Tổ hạ tầng theo dõi; kho xử lý chứng từ liên quan |
| `ready_to_repair` | Sẵn sàng sửa chữa | Không cần vật tư hoặc đã cấp đủ | Hệ thống/Tổ hạ tầng |
| `repairing` | Đang sửa chữa | Đã bắt đầu thực hiện | Tổ hạ tầng |
| `done` | Hoàn tất | Có kết quả; checklist lỗi được đánh dấu đã xử lý | Tổ hạ tầng |
| `cancelled` | Hủy | Đề xuất bị hủy | Tổ hạ tầng |

Các trạng thái cũ `submitted`, `approved`, `rejected` được migration trong
`init()` sang `confirmed`, `ready_to_repair`, `cancelled`; không phải trạng
thái workflow hiện tại.

### 8.6 Trạng thái hợp đồng `bts.contract.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Dự thảo | Hồ sơ đang chuẩn bị | KSGS/Tổ hạ tầng theo ngữ cảnh |
| `submitted` | Chờ ký duyệt | Hồ sơ đã trình BGĐ | Tổ hạ tầng hoặc batch |
| `active` | Hiệu lực | BGĐ đã ký; hợp đồng đang hiệu lực | BGĐ |
| `renewal_agreed` | Đã thống nhất gia hạn | Đã đánh dấu thống nhất gia hạn | Tổ hạ tầng |
| `liquidated` | Đã thanh lý | Hợp đồng đã chấm dứt qua thanh lý | BGĐ |
| `expired` | Hết hạn | Hệ thống xác định đã quá hạn | Scheduled action |
| `cancelled` | Đã hủy | Hủy dự thảo hoặc BGĐ từ chối hồ sơ chờ ký | Tổ hạ tầng/BGĐ theo trạng thái |

### 8.7 Trạng thái batch ký số `bts.contract.signature.batch.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Dự thảo | KSGS đang tạo batch và các line hồ sơ | KSGS |
| `submitted` | Đã gửi BGĐ | Batch chờ ký | KSGS gửi; BGĐ xử lý |
| `partially_signed` | Đã ký một phần | Có line đã ký nhưng chưa đủ | BGĐ |
| `done` | Hoàn tất | Tất cả line đã ký và BGĐ hoàn tất batch | BGĐ |
| `rejected` | Từ chối | BGĐ từ chối trước khi có line đã ký; hồ sơ trả về để sửa | BGĐ |

Line của batch dùng `pending` (Chờ ký), `signed` (Đã ký), `rejected` (Từ
chối).

### 8.8 Trạng thái gia hạn `bts.contract.renewal.state`

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Vai trò thường thao tác |
| --- | --- | --- | --- |
| `draft` | Dự thảo | Hồ sơ gia hạn mới | Tổ hạ tầng |
| `in_progress` | Đang thực hiện | Tổ hạ tầng đang xử lý/nhập điều khoản mới | Tổ hạ tầng |
| `pending_signature` | Chờ BGĐ ký số | Đã có scan và đủ ngày mới, chờ ký | Tổ hạ tầng gửi; BGĐ xử lý |
| `completed` | Hoàn thành | BGĐ đã ký; điều khoản mới cập nhật vào hợp đồng | BGĐ |
| `rejected` | BGĐ từ chối | Bị từ chối và có lý do | BGĐ |
| `cancelled` | Đã hủy | Hồ sơ dừng trước khi chờ ký/hoàn thành | Tổ hạ tầng |

## 9. Mapping dữ liệu ERD với Odoo

| Thực thể trong ERD | Model Odoo/source | Loại | Vai trò trong hệ thống |
| --- | --- | --- | --- |
| Project | `project.project` | Chuẩn Odoo được mở rộng | Dự án BTS; điểm gom trạm, vật tư, bảo trì, batch ký và chỉ số hợp đồng |
| Station | `project.task` | Chuẩn Odoo được mở rộng | Trạm BTS; điểm neo hợp đồng, biên bản, equipment và dữ liệu vị trí |
| Partner | `res.partner` | Chuẩn Odoo được mở rộng | Nhà cung cấp, chủ đất, đối tác viễn thông, KTV thuê ngoài |
| User/Role | `res.users`, `res.groups` | Chuẩn Odoo được cấu hình/mở rộng | Tài khoản, vai trò và quyền |
| Material request | `bts.material.request`, `bts.material.request.line` | Custom | Nhu cầu và số lượng vật tư theo dự án/nguồn |
| Product/UoM | `product.template`, `product.product`, `uom.uom` | Chuẩn Odoo được mở rộng | Danh mục vật tư BTS và đơn vị tính |
| Purchase | `purchase.order`, `purchase.order.line` | Chuẩn Odoo được mở rộng | Mua phần vật tư thiếu, nối về yêu cầu/dự án |
| Inventory transfer | `stock.picking`, `stock.move` | Chuẩn Odoo được mở rộng | Nhập/xuất và số lượng cấp phát thực tế |
| Material notification | `bts.material.notification` | Custom | Thông báo `ready` cho người yêu cầu |
| Equipment | `maintenance.equipment` | Chuẩn Odoo được mở rộng | Hồ sơ thiết bị/vận hành của từng trạm |
| Maintenance batch | `bts.maintenance.batch` | Custom | Phiếu bảo trì cấp dự án |
| Station inspection | `maintenance.request` | Chuẩn Odoo được mở rộng | Phiếu kiểm tra từng trạm trong batch |
| Checklist template/result | `bts.maintenance.checklist.item`, `bts.maintenance.checklist.result` | Custom | Hạng mục mẫu và kết quả kiểm tra |
| Repair proposal | `bts.repair.proposal`, `.line`, `.material.line` | Custom | Điều phối lỗi, sửa chữa và vật tư cần cấp |
| Contract | `bts.contract` | Custom | Hợp đồng thuê đất/cho thuê trạm |
| Negotiation minutes | `bts.negotiation.minutes` | Custom | Biên bản đàm phán theo trạm |
| Signature batch | `bts.contract.signature.batch`, `.line` | Custom | Gom và ký số hồ sơ theo dự án/giai đoạn |
| Contract renewal | `bts.contract.renewal` | Custom | Lịch sử và workflow gia hạn |
| Station handover dossier | `bts.station.handover` | Custom | Hồ sơ bàn giao theo trạm; không phải luồng bàn giao bảo trì chính của demo |
| Message/Activity | `mail.thread`, `mail.activity.mixin`, `mail.activity` | Chuẩn Odoo được kế thừa | Chatter, theo dõi thay đổi và nhắc hạn |
| Attachment | Field `Binary(attachment=True)` và `ir.attachment` phía Odoo | Chuẩn Odoo | Lưu scan ban đầu, file ký số và hồ sơ gia hạn |
| Dashboard | `dtc.bts.dashboard`, `dtc.bts.inventory.dashboard`, `bts.maintenance.dashboard`, `bts.contract.dashboard` | Custom | Tổng hợp KPI và điều hướng theo phân hệ |

## 10. Phạm vi demo hiện tại

### Đã nằm trong phạm vi demo

- Tạo dự án, trạm BTS, đối tác và theo dõi trạng thái.
- Nhập hồ sơ hợp đồng theo từng trạm từ tab **Hồ sơ hợp đồng** trên form trạm.
- Tạo yêu cầu vật tư từ dự án; PKH duyệt/từ chối và mua bổ sung.
- Thủ kho nhập; phiếu xuất tự lấy dòng duyệt, confirm/assign và cập nhật số
  lượng đã cấp sau Validate.
- Bàn giao dự án sang bảo trì và Tổ hạ tầng tiếp nhận.
- Tạo hồ sơ equipment theo trạm với lịch đầu tiên neo ngày nghiệm thu dự
  án, phiếu bảo trì dự án, checklist và kết quả.
- Tạo đề xuất sửa chữa; nếu cần thì sinh yêu cầu vật tư nguồn `maintenance`.
- Gửi batch ký số theo dự án; BGĐ tải bản ký, ký từng hồ sơ và hoàn tất batch.
- Theo dõi hợp đồng đến hạn, khởi tạo, thương lượng và ký số gia hạn.
- Dashboard và phân quyền tách theo KSGS, PKH, Thủ kho, Tổ hạ tầng, BGĐ,
  DTC Admin và System Administrator.

### Chưa triển khai hoặc ngoài phạm vi

| Nội dung | Trạng thái hiện tại |
| --- | --- |
| Portal/tài khoản Odoo cho KTV thuê ngoài | **Chưa triển khai**. KTV là `res.partner`; Tổ hạ tầng nhập/xác nhận kết quả. |
| Điều xe/đội xe phục vụ khảo sát, bảo trì | **Chưa triển khai** trong các module DTC BTS. |
| Kế toán, hóa đơn, hạch toán và thanh toán hợp đồng/mua hàng | **Ngoài phạm vi demo hiện tại**. Module `account` là dependency phục vụ nền tảng/menu nhưng không có workflow kế toán DTC custom. |
| Báo cáo tài chính, dòng tiền hoặc lợi nhuận theo trạm | **Chưa triển khai**. Dashboard hiện là dashboard nghiệp vụ dự án/kho/bảo trì/hợp đồng. |
| BGĐ duyệt đề xuất sửa chữa | **Chưa triển khai**. Workflow hiện do Tổ hạ tầng xác nhận và thực hiện. |
| Tự động chuyển trạng thái dự án theo một sơ đồ bắt buộc | **Chưa triển khai**; `project.project.state` hiện là selection và ràng buộc dữ liệu. |
| Chuyển biên bản đàm phán thành hợp đồng trong luồng hiện tại | **Không dùng trong demo**; `converted` và `converted_to_contract_id` chỉ giữ tương thích legacy. |

## 11. Kết luận

Odoo được dùng làm nền ERP tích hợp: các model chuẩn Project, Contacts,
Purchase, Inventory, Product, Maintenance và Mail được kế thừa; model custom
xử lý yêu cầu vật tư, checklist, sửa chữa, hợp đồng, ký số và gia hạn đặc thù
BTS. `project.task` là điểm neo dữ liệu của từng trạm, còn `project.project`
gom luồng cấp dự án. Kho, bảo trì và hợp đồng liên kết quanh hai lớp dữ liệu này
để tạo một chuỗi truy vết thống nhất thay cho các file Excel và trao đổi rời
rạc.
