# MIS Odoo Project — Quản lý trạm BTS DTC

> Tài liệu được kiểm tra và đồng bộ với working tree ngày 30/07/2026.

Hệ thống được xây dựng trên Odoo 17 Community để quản lý xuyên suốt vòng
đời dự án hạ tầng viễn thông BTS: từ dự án, trạm, hợp đồng và vật tư đến
bàn giao vận hành, bảo trì và sửa chữa.

## Chức năng chính

- Quản lý dự án và danh sách trạm BTS.
- Quản lý đối tác: nhà cung cấp, chủ đất, đối tác viễn thông và kỹ thuật
  viên ngoài.
- Quản lý yêu cầu vật tư, mua hàng, nhập kho, xuất kho và cấp phát theo
  dự án/trạm; phiếu xuất tự lấy dòng đã duyệt, xác nhận và giữ hàng.
- Quản lý hợp đồng thuê đất, hợp đồng cho thuê trạm, biên bản đàm phán,
  ký số theo batch và gia hạn hợp đồng.
- Cảnh báo hợp đồng sắp hết hạn bằng dashboard và `mail.activity`; tự cập
  nhật hợp đồng quá hạn bằng scheduled action.
- Bàn giao dự án sang vận hành và quản lý hồ sơ bảo trì theo trạm; lịch
  bảo trì đầu tiên tính từ ngày nghiệm thu dự án.
- Nhắc lịch bảo trì trước 3 ngày, checklist định kỳ và điều phối đề xuất
  sửa chữa/cấp vật tư.
- Dashboard riêng cho dự án, kho, hợp đồng và bảo trì.
- Phân quyền theo vai trò nghiệp vụ và giới hạn menu tương ứng.
- Giám đốc Xí nghiệp tạo/sửa project trong phạm vi của mình và phân công
  KSGS; KSGS chỉ đọc project được giao nhưng được tạo/sửa trạm và xử lý các
  workflow liên quan trong phạm vi đó.
- My Activities hỗ trợ batch chờ ký, hợp đồng sắp hết hạn, yêu cầu vật tư bị
  từ chối và phân công dự án; notification dashboard cũ vẫn chạy song song.

## Các module

| Module                    | Chức năng                                                  |
| ------------------------- | ---------------------------------------------------------- |
| `dtc_bts_base`            | Dữ liệu nền, dự án, trạm, đối tác, dashboard và nhóm quyền |
| `dtc_bts_inventory`       | Yêu cầu vật tư, mua hàng, nhập/xuất kho và cấp phát        |
| `dtc_bts_maintenance`     | Bàn giao vận hành, lịch bảo trì, checklist và sửa chữa     |
| `dtc_bts_contract`        | Hợp đồng, biên bản, ký số, cảnh báo hạn và gia hạn         |
| `dtc_bts_menu_visibility` | Giới hạn ứng dụng/menu theo vai trò                        |

Trạm BTS được biểu diễn bằng `project.task` và thuộc một
`project.project`. Các phân hệ hợp đồng, kho và bảo trì cùng tham chiếu
trực tiếp đến dự án/trạm này.

Tài liệu chi tiết từng phân hệ nằm tại
[docs/module_docs](docs/module_docs/README.md).

## Công nghệ

- Odoo 17 Community
- PostgreSQL 15
- Docker và Docker Compose

## Yêu cầu

- Docker Desktop trên Windows/macOS, hoặc Docker Engine trên Linux.
- Docker Compose v2 (`docker compose`).
- Git nếu lấy source từ repository.

## Cách chạy

### 1. Lấy source

```bash
git clone <REPO_URL>
cd mis-odoo-project
```

Nếu đã có source thì mở terminal tại thư mục chứa `docker-compose.yml`.

### 2. Tạo file môi trường

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Mở `.env` và thay tối thiểu mật khẩu PostgreSQL:

```dotenv
POSTGRES_PASSWORD=<MAT_KHAU_POSTGRES>
```

Không commit `.env` vào Git.

> `POSTGRES_DB` là database khởi tạo của PostgreSQL, không phải database
> nghiệp vụ được chọn trong Odoo.

Mật khẩu quản lý database trên màn hình Odoo lấy trực tiếp từ
`admin_passwd` trong `config/odoo.conf`. Biến `ODOO_MASTER_PASSWORD` trong
file môi trường hiện chỉ mang tính tham chiếu và chưa được Docker Compose
đưa vào file cấu hình Odoo. Trước khi triển khai ra môi trường dùng chung,
cần đổi `admin_passwd` trong `config/odoo.conf`.

### 3. Khởi động

```bash
docker compose up -d
```

Kiểm tra trạng thái:

```bash
docker compose ps
```

Hai container chính phải ở trạng thái `Up`; PostgreSQL nên hiển thị
`healthy`.

### 4. Mở Odoo

Truy cập:

```text
http://localhost:8069
```

Nếu đã đổi `ODOO_PORT` trong `.env`, sử dụng cổng tương ứng.

Ở lần chạy đầu:

1. Mở màn hình quản lý database.
2. Nhập master password từ `admin_passwd` trong `config/odoo.conf`.
3. Tạo database nghiệp vụ, ví dụ `mis_project_dtc`.
4. Đăng nhập bằng tài khoản quản trị vừa tạo.

### 5. Cài module

Trong Odoo:

1. Mở **Apps**.
2. Bật developer mode nếu chưa thấy **Update Apps List**.
3. Chạy **Update Apps List**.
4. Tìm và cài các module BTS.

Thứ tự khuyến nghị:

1. `dtc_bts_base`
2. `dtc_bts_inventory`
3. `dtc_bts_maintenance`
4. `dtc_bts_contract`
5. `dtc_bts_menu_visibility`

Odoo sẽ tự cài các dependency chuẩn cần thiết.

Sau khi thay đổi source hoặc cập nhật phiên bản, vào **Apps** và bấm
**Upgrade** cho module liên quan. Với source hiện tại, cần upgrade:

- `dtc_bts_base`
- `dtc_bts_inventory`
- `dtc_bts_maintenance`
- `dtc_bts_contract`

## Các lệnh vận hành thường dùng

Xem log Odoo:

```bash
docker compose logs -f odoo
```

Xem log PostgreSQL:

```bash
docker compose logs -f db
```

Khởi động lại Odoo:

```bash
docker compose restart odoo
```

Dừng hệ thống nhưng giữ dữ liệu:

```bash
docker compose down
```

Khởi động lại:

```bash
docker compose up -d
```

Kiểm tra health endpoint:

```text
http://localhost:8069/web/health
```

Kết quả bình thường:

```json
{ "status": "pass" }
```

## Xóa toàn bộ dữ liệu và chạy lại

> Cảnh báo: thao tác sau xóa toàn bộ database và dữ liệu Odoo trong
> Docker volumes.

```bash
docker compose down -v --remove-orphans
docker compose up -d
```

Chỉ sử dụng khi chắc chắn không cần giữ dữ liệu hoặc đã có bản sao lưu.

## Tài liệu sử dụng và kiểm thử

- [Mục lục tài liệu kỹ thuật](docs/module_docs/README.md)
- [Tổng quan hệ thống](docs/module_docs/00_tong_quan_he_thong.md)
- [Phân hệ bảo trì](docs/module_docs/03_dtc_bts_maintenance.md)
- [Phân hệ hợp đồng](docs/module_docs/04_dtc_bts_contract.md)
- [Phân quyền hệ thống](docs/module_docs/06_phan_quyen_he_thong.md)
- [Hướng dẫn test và import demo](docs/module_docs/07_huong_dan_test_va_import_demo.md)
- [Mapping nghiệp vụ với Odoo](docs/module_docs/08_mapping_odoo.md)
- [Luồng email nghiệp vụ](docs/module_docs/09_luong_email.md)

`docs/module_docs` là nguồn tài liệu kỹ thuật duy nhất của dự án. Nội dung
vận hành theo từng module được duy trì tại đây để tránh nhiều tài liệu mô tả
cùng một logic nhưng không còn đồng bộ.
