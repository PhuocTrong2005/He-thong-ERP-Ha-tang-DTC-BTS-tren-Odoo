# Cơ chế ẩn/hiện ứng dụng (`dtc_bts_menu_visibility`)

> Kiểm tra theo working tree ngày 30/07/2026.

## Mục đích

Module giữ các ứng dụng Odoo gốc được cài đặt để module custom tái sử dụng
model và nghiệp vụ, nhưng thu gọn app switcher cho người dùng DTC thông
thường.

Các form custom vẫn có thể kế thừa model/view chuẩn Odoo. Việc ẩn root app
không làm mất các nút hoặc field cần thiết trong action custom; các bước dư
thừa phải được xử lý tại view hoặc workflow của phân hệ tương ứng.

## Group điều khiển

`dtc_bts_menu_visibility.group_show_core_apps`
(`Hiển thị phân hệ Odoo gốc`) là group kỹ thuật quyết định việc nhìn thấy
các root menu Odoo gốc.

System Administrator (`base.group_system`) tự động kế thừa group này, đồng
thời kế thừa các group manager của Project, Purchase, Stock, Maintenance
và Accounting.

## Root menu được điều khiển

Module gán trực tiếp `groups_id` của các menu sau cho
`group_show_core_apps`:

- Discuss
- To-do
- Project
- Purchase
- Inventory
- Maintenance
- Accounting
- Spreadsheet Dashboard
- Apps
- Settings
- Technical/Tests

Do đó:

- người dùng không có group chỉ thấy các ứng dụng custom mà group nghiệp
  vụ của họ cho phép;
- người có `group_show_core_apps` thấy lại các ứng dụng Odoo gốc;
- Administrator luôn thấy Apps, Settings, Technical và các ứng dụng gốc.
- DTC Admin chỉ được bổ sung menu Settings để quản lý tài khoản, group và
  cấu hình; không được gán `group_show_core_apps`.

Ngoài danh sách root tĩnh, role GĐXN có lớp lọc runtime trên
`ir.ui.menu._visible_menu_ids()`: chỉ các menu nằm dưới cây **Quản lý dự án
BTS** được trả về. Lọc này vẫn áp dụng khi bật debug hoặc khi tài khoản có
thêm role nghiệp vụ; System Administrator được miễn lọc.

## Phân biệt hiển thị và bảo mật

Ẩn menu chỉ thay đổi điều hướng giao diện. Nó không phải ACL và không tự
chặn model, action hoặc URL trực tiếp.

Quyền thực tế là kết quả kết hợp của:

1. group của user;
2. ACL (`ir.model.access.csv`);
3. record rule (`ir.rule`);
4. group/invisible trên menu, view và button;
5. kiểm tra nghiệp vụ trong Python.

Ví dụ, một user có thể thấy menu Yêu cầu cấp phát nhưng record rule chỉ cho
thấy yêu cầu do mình tạo hoặc thuộc dự án mình phụ trách. Ngược lại, thêm
`group_show_core_apps` chỉ làm hiện menu Odoo gốc, không tự cấp quyền đọc
hay sửa dữ liệu bên trong.

## Lưu ý vận hành

- Không gán `group_show_core_apps` đại trà nếu muốn giao diện chỉ tập trung
  vào DTC BTS.
- Khi một menu biến mất, cần kiểm tra cả group của menu cha và menu con.
- Khi user thấy menu nhưng gặp Access Error, cần kiểm tra ACL/record rule,
  không sửa module visibility để “chữa” quyền dữ liệu.
- Không xóa group này khỏi System Administrator vì sẽ làm mất Apps,
  Settings hoặc Technical.
