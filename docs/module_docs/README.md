# Tài liệu kỹ thuật các module DTC BTS

Đây là nguồn tài liệu kỹ thuật duy nhất của repository, được đồng bộ với
working tree hiện tại ngày 30/07/2026. Khi logic thay đổi, cập nhật tài liệu theo
module tương ứng thay vì tạo thêm tài liệu tổng hợp trùng nội dung.

## Mục lục

1. [Tổng quan hệ thống](00_tong_quan_he_thong.md)
2. [Dự án và trạm BTS](01_dtc_bts_base.md)
3. [Mua hàng và kho vật tư](02_dtc_bts_inventory.md)
4. [Bảo trì trạm BTS](03_dtc_bts_maintenance.md)
5. [Hợp đồng BTS](04_dtc_bts_contract.md)
6. [Cơ chế ẩn/hiện ứng dụng](05_dtc_bts_menu_visibility.md)
7. [Phân quyền tài khoản và người dùng](06_phan_quyen_he_thong.md)
8. [Hướng dẫn test và import dữ liệu demo](07_huong_dan_test_va_import_demo.md)
9. [Mapping nghiệp vụ với Odoo](08_mapping_odoo.md)
10. [Luồng email nghiệp vụ](09_luong_email.md)
11. [Mô tả chi tiết và ý nghĩa của 4 dashboard](10_mo_ta_chi_tiet_4_dashboard.md)

## Quy ước

- Tên model, field, trạng thái và XML ID được viết bằng `code`.
- DTC Admin chỉ quản trị user/group/cấu hình, không phải actor nghiệp vụ.
- “System Administrator” là user thuộc `base.group_system`, có cơ chế toàn
  quyền riêng phục vụ dev/demo.
- Menu hiển thị và quyền truy cập dữ liệu là hai lớp độc lập.
- Ngày nghiệm thu dự án và ngày nghiệm thu từng trạm là hai mốc riêng:
  mốc dự án dùng tính lịch bảo trì đầu tiên; mốc trạm dùng mở hồ sơ HĐ
  cho thuê trạm.
- Các giá trị lịch đã lưu trước khi đổi công thức không tự hồi tố chỉ bằng
  việc upgrade code; cần chạy cập nhật dữ liệu khi có yêu cầu migration.
- Thông tin bí mật như mật khẩu SMTP, Gmail App Password và mã OTP không
  được ghi vào tài liệu hoặc commit vào repository.
