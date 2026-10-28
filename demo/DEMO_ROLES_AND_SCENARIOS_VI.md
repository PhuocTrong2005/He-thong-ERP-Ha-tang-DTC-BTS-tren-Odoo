# Vai trò và kịch bản demo Quản lý hợp đồng BTS

> Đây là snapshot đã kiểm chứng ngày 28/10/2026 trên máy ban đầu. ID, mã batch tự sinh, ngày và URL có ID có thể khác trên máy mới. Dùng `Inspect` trong [README](README.md) để lấy mã/ID/URL hiện tại; seed tính ngày tương đối khi tạo lần đầu. Những bộ DIỄN TẬP đã ký trong mô tả là bằng chứng lịch sử local, không được phân phối bằng dump. File mẫu nằm tại `demo/DEMO-document.txt` tính từ thư mục gốc repo; trong hộp chọn file Windows dùng đường dẫn do `Resolve-Path demo/DEMO-document.txt` trả về.

Kiểm tra trực tiếp ngày **28/10/2026**, múi giờ Việt Nam, database **`bts_contract_demo`**.
Tài liệu dùng dữ liệu thật đang có trong Odoo local, gồm dữ liệu giả có nhãn DEMO.
Đọc bản [nhắc nhanh một trang](DEMO_CHEAT_SHEET_VI.md) khi trình diễn; đọc tài liệu này để hiểu quy trình.

## 1. Chuẩn bị và cách dùng

- Odoo: <http://127.0.0.1:8079/web>; email OTP: <http://127.0.0.1:8025>.
- Mật khẩu chỉ nằm trong `demo/.local/credentials.json`: dùng khóa `ksgs`, `bgd`, `infra` tương ứng.
- Đổi tài khoản bằng avatar góc phải → **Đăng xuất** rồi đăng nhập lại. Các tab trong cùng một hồ sơ Chrome dùng chung phiên: đổi user ở tab này cũng ảnh hưởng tab Odoo khác. Mailpit không cần đăng nhập.
- File **F** dùng trong mọi bước tải tài liệu: `demo/DEMO-document.txt` ([mở file mẫu](DEMO-document.txt)). Đây là tệp văn bản có chữ **TÀI LIỆU DEMO**, thay cho scan thật; không phải PDF/chữ ký số thật.
- Ngày nhập dùng `dd/mm/yyyy`, ví dụ `28/10/2026`; giá nhập số không phân cách hàng nghìn, ví dụ `13000000`.
- Odoo 17 tự lưu khi rời trường/chuyển màn hình hoặc bấm nút nghiệp vụ. Khi có biểu tượng đám mây **lưu** cạnh tiêu đề, bấm để lưu và chờ hết chỉ báo thay đổi; nếu nhập sai thì dùng biểu tượng hoàn tác. Không tìm nút **Sửa** kiểu Odoo cũ.
- Các URL dưới đây chỉ dùng trong database local này, sau khi đăng nhập đúng vai trò. Nếu mở từ URL làm menu đầu trang không đổi ngay, đi theo đường menu kèm theo.
- **Kịch bản A** dùng `DEMO-PENDING` và `DEMO-RENEWAL-PRACTICE`; **B** dùng `DEMO-LIVE`. Hai kịch bản có bộ đầu vào riêng. Sau khi tự demo, hồ sơ sẽ chuyển trạng thái thật; không thể coi chúng còn là bộ khởi đầu để chạy lần hai.

## 2. Ai làm gì và bàn giao cho ai?

Quy trình chính: **GĐXN tổ chức dự án/phân công → KSGS chuẩn bị hồ sơ theo trạm → BGĐ hợp đồng ký → Tổ hạ tầng theo dõi hạn, thương lượng gia hạn → BGĐ xác nhận gia hạn → Tổ hạ tầng theo dõi kỳ mới**.

| Vai trò / tài khoản có thật | Trách nhiệm và đầu vào → đầu ra | App/menu nghiệp vụ | Phạm vi xem đã kiểm tra | Được làm / bị chặn đã xác minh |
|---|---|---|---|---|
| **Giám đốc Xí nghiệp (GĐXN)**; `enterprise.director.demo` | Tổ chức dự án, giao KSGS; nhận báo cáo thất bại để xem xét/trình cấp quyết định → dự án có người chịu trách nhiệm | **Quản lý dự án BTS**; nhánh **Báo cáo chờ xem xét** theo nhóm trong XML | Dự án có **Giám đốc Xí nghiệp = chính user** và các trạm/hồ sơ thuộc dự án ấy. Ba dự án gốc LIVE/TESTED/PENDING chưa gán GĐXN nên user này không thấy chúng. Các bộ diễn tập mới được tạo bằng GĐXN và thuộc phạm vi user này | Đã dùng ORM dưới đúng user để tạo dự án diễn tập và giao `ksgs.demo`; ACL/record rule cho đọc/sửa trong phạm vi, chặn xóa trạm. Không có ACL tạo/sửa HĐ hoặc ký batch. Chưa thiết lập mật khẩu cho user này trong credentials local, không dùng để đăng nhập trong A/B; menu dựa XML/nhóm, chưa kiểm tra bằng phiên Chrome riêng |
| **Kỹ sư giám sát (KSGS)**; `ksgs.demo` / **DEMO KSGS** | Nhận dự án được giao và thông tin đàm phán/scan bên ngoài → hồ sơ dự thảo tại trạm, batch đủ hồ sơ gửi BGĐ | **Quản lý dự án BTS → Bảng tổng hợp / Danh sách dự án / Danh sách trạm BTS / Đối tác** | Dự án có **KSGS phụ trách dự án = DEMO KSGS**; trạm/HĐ/BB/batch theo dự án được giao. Không có quyền đọc model gia hạn | Tạo/sửa trạm và hồ sơ ban đầu còn dự thảo, nhập ngày nghiệm thu trạm, gửi batch ở dự án. Không tạo/xóa dự án; không sửa các trường thông tin BTS/phân công bị khóa; không xóa trạm; không ký/từ chối từng HĐ; không sửa HĐ đã gửi. Các thao tác chuẩn bị và gửi đã chạy thật |
| **Ban Giám đốc hợp đồng (BGĐ HĐ)**; `bgd.demo` / **DEMO BGD** | Nhận batch từ KSGS hoặc gia hạn từ Tổ hạ tầng → hồ sơ ký/xác nhận, batch hoàn tất hoặc quyết định từ chối | **Quản lý hợp đồng BTS → Tổng quan / Danh sách dự án / Gia hạn hợp đồng / Ký số hợp đồng → Batch hợp đồng ban đầu, Hợp đồng gia hạn chờ ký**; có nhánh đề nghị hủy | Xem hồ sơ của mọi dự án trong database demo; không áp bộ lọc dự án theo KSGS/GĐXN | Ký OTP từng dòng, hoàn thành batch khi đủ dòng ký; từ chối batch chưa ký dòng nào; xác nhận/từ chối gia hạn. Không tạo HĐ/gia hạn, không sửa trực tiếp dự án/trạm. Ký không đồng nghĩa được sửa điều khoản |
| **Tổ quản lý hạ tầng**; `infra.demo` / **DEMO INFRA** | Nhận HĐ hiệu lực và nhắc hạn → xử lý thương lượng, nhập điều khoản/file gia hạn, gửi BGĐ; nhận kết quả về để theo dõi | **Quản lý hợp đồng BTS → Tổng quan / Danh sách dự án / Gia hạn hợp đồng**; không có menu ký batch của BGĐ | Đọc dự án/trạm/HĐ/BB/batch toàn database demo; xem, lập và xử lý gia hạn | Đã xác minh tạo gia hạn, bắt đầu, nhập điều khoản/file, gửi ký. Chỉ đọc batch, không ký thay BGĐ; không sửa trạm/dự án. ACL cũng cho tạo/sửa HĐ/BB trong app hợp đồng, nhưng không phải actor nhập hồ sơ ban đầu của kịch bản theo dự án |
| **System Administrator**; `admin.demo` | Cài module, cấu hình SMTP, tài khoản, chuẩn bị dữ liệu → môi trường để nghiệp vụ thao tác | Quản trị kỹ thuật, các màn hình được nhóm System cho phép | Toàn database; code có ngoại lệ `base.group_system` | Quyền kỹ thuật rộng. **Không dùng để thay KSGS/BGĐ/Tổ hạ tầng khi trình diễn**; ba user nghiệp vụ không thuộc nhóm này |
| **DTC Admin**, khác System Administrator; tài khoản DTC Admin mẫu do module tạo có sẵn từ module | Quản trị người dùng/nhóm theo thiết kế → cấp quyền tổ chức | Thiết kế tài liệu gốc hướng tới Settings; không dùng trong A/B | Kiểm tra ORM: không có quyền đọc HĐ/BB/batch/gia hạn; có thể đọc dự án/trạm do quyền chuẩn kế thừa | Không mặc định có quyền ký; không đồng nhất với `admin.demo`. Chưa xác minh toàn bộ giao diện quản trị hoặc đặt mật khẩu cho tài khoản này |
| **Chủ đất**: `DEMO Chủ đất Nguyễn An`; **viễn thông**: `DEMO Viễn thông Sao Việt` | Cung cấp/thỏa thuận nội dung ngoài hệ thống → KSGS nhập đối tác/hồ sơ; Tổ hạ tầng ghi kết quả gia hạn | Là bản ghi **Đối tác**, không có menu đăng nhập riêng | Kiểm tra `user_ids` của cả hai: rỗng | **Không có tài khoản thao tác/portal tương ứng trong demo**. Không trình bày cảnh chủ đất hoặc nhà mạng đăng nhập duyệt/ký |

GĐXN quản lý việc tổ chức và phân công trong phạm vi xí nghiệp. BGĐ hợp đồng là vai trò ra quyết định ký hợp đồng; hai nhóm khác nhau, không thay nhau được. Phần báo thất bại/hủy có trong source nhưng không nằm trong luồng phỏng vấn chính và chưa được diễn tập toàn bộ.

### Những chỗ cần hiểu khác tài liệu cũ

| Tài liệu/ấn tượng dễ nhầm | Bản demo đã đối chiếu |
|---|---|
| KSGS vào app Hợp đồng hoặc trình duyệt từng HĐ | KSGS đi từ **trạm → Hồ sơ hợp đồng**, gửi cả batch từ **dự án → Hợp đồng trạm**. Không có app Hợp đồng cho KSGS |
| Nút ký dòng batch là “Ký số / xác nhận ký” | Trên dòng là **Ký số**; hộp thoại có **Gửi mã OTP**, **Mã OTP**, **Xác nhận và ký số**. “Ký số / xác nhận ký” là nút trên **gia hạn** |
| Mọi luồng ký đều có OTP | **Batch giai đoạn 1/2 có OTP**, gia hạn **không có OTP**: BGĐ tải file và xác nhận |
| Phải tải file đã ký trước khi ký dòng batch | Form OTP hiện không có trường upload file đã ký; backend lấy tài liệu nguồn làm file ký nội bộ khi OTP đúng. Gia hạn mới yêu cầu upload **Hồ sơ gia hạn đã ký số** |
| KSGS tuyệt đối không có quyền `write` project | ACL có write để phục vụ workflow, nhưng Python khóa danh sách trường thông tin BTS/phân công; không nên khẳng định mọi trường project đều bị khóa. Form cũng làm các trường thông tin BTS chỉ đọc |
| `term_years = 1` tự bảo đảm mọi HĐ kéo dài đủ một năm | Giá trị là dữ liệu nhập. HĐ cho thuê trạm TESTED hiện chỉ có kỳ ngắn để demo; không suy ra số ngày từ `term_years` |
| Giá thuê trên bản demo là VND | Database hiện dùng **USD**, dấu **$**; 12.000.000/24.000.000 là số giả kỹ thuật. Không gọi đó là đơn giá VND hay đơn giá thực tế |
| Đổi ngày nhắc sang tương lai sẽ luôn tạo ngay activity kỳ mới | Source `_schedule_expiry_activity` chỉ tạo khi đã vào cửa sổ nhắc. Sau gia hạn tới 2027, activity cũ đóng, **chưa có activity mới** cho đến khi vào cửa sổ. Đã đối chiếu code; kiểm chứng thực thi nêu ở mục 8 |
| Bộ mẫu được GĐXN tạo trên UI | Ba bộ gốc được script ORM chuẩn bị (`create_uid` kỹ thuật OdooBot), giao sẵn `DEMO KSGS`; **Giám đốc Xí nghiệp đang trống**. Bộ diễn tập riêng mới được tạo dưới vai trò GĐXN |
| App switcher chỉ có ứng dụng BTS | Không cài `dtc_bts_menu_visibility` vì kéo thêm Kho/Bảo trì. Vẫn có Thảo luận/Việc cần làm/Ứng dụng chuẩn; nhìn thấy menu không đồng nghĩa có mọi quyền ghi dữ liệu |
| Menu Danh sách dự án luôn tự chọn đúng form BTS | Khi kiểm tra UI, action dự án ID223 chưa gắn form rõ nên Odoo chọn nhầm form theo dõi hạn của module hợp đồng. Đã gắn tree ID626/form BTS ID627 có sẵn cho action trong **database demo** bằng [bind_project_views.py](bind_project_views.py); Chrome đã thấy lại **Thông tin dự án BTS**, **Hợp đồng trạm**, **Gửi BGĐ ký số**. Không sửa source nghiệp vụ/ACL/constraint |

## 3. Kiểm kê dữ liệu sử dụng trong A/B

Tại **28/10/2026**, HĐ thuê đất TESTED hết hạn **12/11/2026: còn 15 ngày**; cho thuê trạm TESTED hết hạn **11/11/2026: còn 14 ngày**. Cả hai đang **Hiệu lực** và phù hợp để xem cảnh báo 0–30 ngày. HĐ LIVE cũng hết hạn 12/11 nhưng còn **Dự thảo**, không được gọi là HĐ hiệu lực sắp hết hạn. Ngày seed không tự trượt theo ngày mở demo sau này.

| Bộ / dự án / trạm thật | Hồ sơ hợp đồng và đối tác | Batch / gia hạn hiện tại | Ai thao tác tiếp, dùng cho cảnh nào |
|---|---|---|---|
| **DEMO 01 - Thực hành dự thảo**, `DEMO-LIVE`, project ID **2**; **DEMO Trạm LIVE**, `DEMO-BTS-LIVE`, task ID **2** | `DEMO-LAND-LIVE` HĐ thuê đất ID **2**, **Dự thảo**, chủ đất **DEMO Chủ đất Nguyễn An**; `DEMO-MEMO-LIVE` BB thuê đất ID **2**, **Dự thảo**, cùng đối tác. Chưa có HĐ cho thuê trạm, chưa có ngày nghiệm thu | **Chưa có batch, chưa có gia hạn** | KSGS kiểm tra/nhập/sửa rồi gửi batch GĐ1. Bộ dành cho **B**, A chỉ xem, không gửi |
| **DEMO 02 - Kiểm thử thực tế**, `DEMO-TESTED`, project **3**; **DEMO Trạm TESTED**, `DEMO-BTS-TESTED`, task **3** | `DEMO-LAND-TESTED` ID **3**, thuê đất, **Hiệu lực**, chủ đất **DEMO Chủ đất Nguyễn An**; `DEMO-MEMO-TESTED` ID **3**, **Đã xác nhận**; `DEMO-LEASE-TESTED` ID **4**, cho thuê trạm, **Hiệu lực**, **DEMO Viễn thông Sao Việt**, liên kết thuê đất ID3. Ngày nghiệm thu trạm **28/10/2026** | `KS-HĐ-0001` ID1, **Giai đoạn 1**, **Hoàn tất**, 2/2 ký; `KS-HĐ-0002` ID2, **Giai đoạn 2**, **Hoàn tất**, 1/1 ký; `DEMO-RENEWAL-TESTED` ID1, gia hạn cho thuê trạm, **Hoàn thành**; `DEMO-RENEWAL-PRACTICE` ID2, gia hạn **thuê đất**, **Dự thảo**, chưa nhập điều khoản/file | BGĐ/KSGS xem kết quả hai giai đoạn; Tổ hạ tầng dùng dashboard/nhắc hạn và xử lý gia hạn PRACTICE trong **A** |
| **DEMO 03 - Chờ BGĐ ký**, `DEMO-PENDING`, project **4**; **DEMO Trạm PENDING**, `DEMO-BTS-PENDING`, task **4** | `DEMO-LAND-PENDING` ID **5**, thuê đất, **Chờ ký duyệt**, chủ đất **DEMO Chủ đất Nguyễn An**; `DEMO-MEMO-PENDING` ID **4**, **Chờ phê duyệt**; chưa nghiệm thu/chưa cho thuê trạm | `KS-HĐ-0003` ID **3**, **Giai đoạn 1**, **Đã gửi BGĐ**, 0/2 ký; dòng ID4 HĐ, ID5 BB, OTP **Chưa gửi** | BGĐ ký ngay trong **A**. KSGS không sửa hồ sơ ở trạng thái này |

HĐ thuê đất cả ba bộ: ngày ký/hiệu lực **12/11/2025**, hết hạn **12/11/2026**, thời hạn nhập **1 năm**, giá giả **12000000 USD**, chu kỳ **Hàng năm**, nhắc trước **30 ngày**. BB ngày **28/10/2026**. Cho thuê trạm TESTED: ký/hiệu lực **28/10/2026**, giá **24000000 USD**, hết hạn sau gia hạn **11/11/2026**. Các đối tác trên là dữ liệu DEMO, không phải người dùng ký bên ngoài.

Các ô quan hệ có thể hiển thị **`bts.contract,3`**, **`bts.contract,4`** hoặc **`bts.contract.renewal,2`** vì model không khai báo tên hiển thị nghiệp vụ. Đó là ID kỹ thuật có thật, không phải mất dữ liệu; mở bản ghi để đọc trường **Mã hợp đồng/Mã gia hạn**. Không nhầm `bts.contract,3` với batch ID3.

### URL mở nhanh và đường menu

| Bản ghi | URL local | Đường menu bình thường |
|---|---|---|
| Dự án LIVE | [Mở dự án](http://127.0.0.1:8079/web#id=2&model=project.project&view_type=form&action=223) | KSGS → Quản lý dự án BTS → Danh sách dự án → DEMO 01 |
| Trạm LIVE | [Mở trạm](http://127.0.0.1:8079/web#id=2&model=project.task&view_type=form&action=224) | KSGS → Danh sách trạm BTS → DEMO Trạm LIVE |
| Batch PENDING | [KS-HĐ-0003](http://127.0.0.1:8079/web#id=3&model=bts.contract.signature.batch&view_type=form&action=243) | BGĐ → Quản lý hợp đồng BTS → Ký số hợp đồng → Batch hợp đồng ban đầu |
| Dashboard | [Tổng quan](http://127.0.0.1:8079/web#action=245) | BGĐ/Tổ hạ tầng → Quản lý hợp đồng BTS → Tổng quan |
| Thuê đất TESTED | [DEMO-LAND-TESTED](http://127.0.0.1:8079/web#id=3&model=bts.contract&view_type=form&action=234) | Tổ hạ tầng/BGĐ → Tổng quan → cảnh báo HĐ tương ứng → Mở chi tiết |
| Cho thuê trạm TESTED | [DEMO-LEASE-TESTED](http://127.0.0.1:8079/web#id=4&model=bts.contract&view_type=form&action=234) | Tổ hạ tầng/BGĐ → Tổng quan → Mở chi tiết của HĐ |
| Gia hạn thực hành | [DEMO-RENEWAL-PRACTICE](http://127.0.0.1:8079/web#id=2&model=bts.contract.renewal&view_type=form&action=235) | Tổ hạ tầng → Gia hạn hợp đồng → tìm mã PRACTICE |
| Hai batch hoàn tất | [GĐ1](http://127.0.0.1:8079/web#id=1&model=bts.contract.signature.batch&view_type=form&action=243), [GĐ2](http://127.0.0.1:8079/web#id=2&model=bts.contract.signature.batch&view_type=form&action=243) | KSGS → dự án TESTED → tab Hợp đồng trạm để đối chiếu kết quả trạm/hồ sơ; dùng URL để xem chính batch đã hoàn tất |

Menu **Batch hợp đồng ban đầu** áp domain chỉ `submitted/partially_signed`; ký xong batch biến mất khỏi danh sách này là đúng. Chọn bộ lọc **Hoàn tất** trong cùng action vẫn không bỏ được domain. Dùng URL batch hoàn tất hoặc kết quả ở dự án, không kết luận đã mất dữ liệu.

## 4. Cách ký một dòng batch bằng OTP — dùng chung cho A/B

Chỉ thực hiện với **`bgd.demo`**, batch đã gửi và dòng còn **Chờ ký**:

1. Trong tab **Hồ sơ trong batch**, bấm **Ký số** ở cuối đúng dòng HĐ/BB cần ký; có thể phải kéo ngang bảng sang phải.
2. Hộp thoại **Ký số hồ sơ bằng OTP**: kiểm tra dự án/trạm/loại hồ sơ, giữ **Kênh nhận OTP = Email**, bấm **Gửi mã OTP**. Không chọn SMS: source hiện chỉ có hook mô phỏng SMS, không có nhà cung cấp thật.
3. Sang Mailpit, mở email mới nhất gửi tới **`bgd@demo.invalid`**, đọc mã vừa nhận. Không dùng lại mã từ lần kiểm thử trước hoặc mã của dòng khác.
4. Quay lại hộp thoại, nhập vào **Mã OTP**, bấm **Xác nhận và ký số**. Việc lưu trường OTP kích hoạt kiểm tra trên server; nút xác nhận đóng hộp thoại khi hợp lệ. **Không upload file đã ký trong hộp thoại batch này.**
5. Thành công: dòng chuyển **Đã ký**, **Trạng thái OTP = Đã sử dụng**, có người/ngày ký, tổng số đã ký tăng. Nhập lại OTP của dòng đã ký không phải bước quy trình.

Mã ngẫu nhiên, lưu băm, hạn 5 phút, tối đa 5 lần thử, gắn với người yêu cầu mã. Khi hết hạn/sai mã, xem phản hồi trong hộp thoại và gửi mã mới theo quyền hợp lệ. Không đưa mã vào ghi chú hoặc tài liệu.

Lời trình bày: “Tôi tách người lập và người ký. OTP xác thực chính tài khoản BGĐ; hệ thống lưu người, thời gian và dấu vết kiểm tra tính toàn vẹn của tài liệu.”

Đây là **ký/xác nhận nội bộ bằng HMAC**, không phải chữ ký số được chứng thực bên ngoài. Backend hiện dùng tài liệu nguồn làm file ký nội bộ. Gia hạn là thao tác BGĐ tải file và xác nhận, không được mô tả là đã kiểm tra chứng thư số bên ngoài.

## 5. A — Trình diễn phỏng vấn 7–10 phút

Mục tiêu: ít nhập liệu, thể hiện phân vai, ký batch, điều kiện giai đoạn 2, quản lý hạn và gia hạn. Dùng hồ sơ chuẩn bị sẵn và nói rõ điều đó. Các bước dưới đây thực sự chuyển trạng thái PENDING/PRACTICE khi **bạn** làm; lúc bàn giao chúng vẫn chưa bị dùng.

### A1 — 0:00–1:15 · KSGS giải thích đầu vào

- **User/bản ghi/đường mở:** `ksgs.demo`; dự án `DEMO-LIVE` → **Quản lý dự án BTS → Danh sách dự án → DEMO 01 - Thực hành dự thảo → Thông tin dự án BTS**; mở trạm `DEMO-BTS-LIVE` → tab **Hồ sơ hợp đồng** → **Chi tiết hợp đồng**, sau đó **Chi tiết BB đàm phán**. URL ở mục 3.
- **Điều kiện/nhập/file:** user đã được giao dự án; `DEMO-LAND-LIVE` và `DEMO-MEMO-LIVE` còn dự thảo, đủ dữ liệu. Không nhập thêm, không upload; các scan DEMO đã có. F sẵn để giới thiệu nếu cần.
- **Thao tác/kết quả:** xem KSGS phụ trách, chủ đất, ngày/giá/chu kỳ/scan; quay về dự án → tab **Hợp đồng trạm**, chỉ trỏ nút **Gửi BGĐ ký số**, **không bấm** trong A. Dấu hiệu đúng: thông tin dự án chỉ đọc, hồ sơ trạm đã tải scan, chưa nghiệm thu, chưa có batch của LIVE.
- **Nói:** “Bộ này được chuẩn bị sẵn bằng ORM, đã giao tôi làm KSGS. Tôi nhập hồ sơ ở từng trạm; hệ thống gom đủ HĐ thuê đất và biên bản của tất cả trạm trước khi trình BGĐ.”
- **Dễ vướng:** không thấy app Hợp đồng là đúng quyền KSGS; không dùng admin để mở thay. Nếu lỡ gửi LIVE, dừng việc coi LIVE là bộ bắt đầu B; không reset.

### A2 — 1:15–4:00 · BGĐ ký hai hồ sơ đã gửi

- **User/bản ghi/đường mở:** đổi sang `bgd.demo` → **Quản lý hợp đồng BTS → Ký số hợp đồng → Batch hợp đồng ban đầu → KS-HĐ-0003**, dự án **DEMO 03 - Chờ BGĐ ký**. [Mở batch](http://127.0.0.1:8079/web#id=3&model=bts.contract.signature.batch&view_type=form&action=243).
- **Điều kiện/nhập/file:** trạng thái **Đã gửi BGĐ**, giai đoạn 1, 0/2; dòng HĐ `DEMO-LAND-PENDING` và BB `DEMO-MEMO-PENDING`. Không sửa điều khoản, không upload F trong batch; mã OTP lấy trực tiếp từ Mailpit.
- **Thao tác/kết quả:** kiểm tra hai dòng → thực hiện mục 4 **lần lượt cho cả hai dòng**. Sau dòng đầu batch **Đã ký một phần**; sau dòng thứ hai vẫn có thể là **Đã ký một phần**, số lượng đã ký phải **2/2**. Dấu hiệu: cả hai dòng **Đã ký**, OTP **Đã sử dụng**, người ký **DEMO BGD**.
- **Nói:** “Đây là bộ đã được KSGS gửi trước để tiết kiệm nhập liệu. Một batch chứa hai hồ sơ độc lập; ký một HĐ không tự ký luôn biên bản.”
- **Dễ vướng:** mở đúng batch theo **dự án PENDING**, tránh `KS-HĐ-0007` là ngoại lệ. Không dùng OTP cũ; gửi mã riêng cho mỗi dòng. Bấm ký mà không thấy nút ở cuối bảng thì kéo ngang.

### A3 — 4:00–4:30 · BGĐ hoàn tất batch

- **User/bản ghi/đường mở:** vẫn `bgd.demo`, form `KS-HĐ-0003` → nút đầu form **Hoàn thành batch**.
- **Điều kiện/nhập/file:** 2/2 dòng **Đã ký**; không nhập thêm, không file.
- **Thao tác/kết quả:** bấm **Hoàn thành batch**. Dấu hiệu: batch **Hoàn tất**, có ngày hoàn tất; HĐ `DEMO-LAND-PENDING` **Hiệu lực**, BB **Đã xác nhận**; trạm PENDING chuyển **Đã kí hợp đồng thuê đất và biên bản đàm phán**. Batch không còn trong danh sách đang chờ.
- **Nói:** “Ký từng chứng từ và hoàn tất cả đợt là hai mốc khác nhau. Hoàn tất đợt mới cập nhật tiến độ trạm và thông báo cho người lập.”
- **Dễ vướng:** chưa đủ chữ ký thì chưa được hoàn tất; quay lại ký dòng còn thiếu, không sửa trạng thái bằng tài khoản quản trị.

### A4 — 4:30–5:30 · BGĐ xem kết quả giai đoạn 2 đã kiểm thử

- **User/bản ghi/đường mở:** `bgd.demo` → **Tổng quan** → **Mở chi tiết** của `DEMO-LEASE-TESTED`; hoặc [mở HĐ ID4](http://127.0.0.1:8079/web#id=4&model=bts.contract&view_type=form&action=234). [Batch KS-HĐ-0002](http://127.0.0.1:8079/web#id=2&model=bts.contract.signature.batch&view_type=form&action=243) dùng để xem kết quả 1/1.
- **Điều kiện/nhập/file:** TESTED đã nghiệm thu **28/10/2026**, hai batch hoàn tất. Không nhập/sửa/upload gì.
- **Thao tác/kết quả:** chỉ vào loại **Cho thuê trạm**, đối tác **DEMO Viễn thông Sao Việt**, liên kết thuê đất cùng **DEMO Trạm TESTED** (`bts.contract,3`), hạn **11/11/2026 ≤ 12/11/2026**. Dấu hiệu: **Hiệu lực**, batch GĐ2 **Hoàn tất**.
- **Nói:** “Tôi dùng kết quả đã kiểm thử để giới thiệu giai đoạn 2. Hồ sơ cho thuê trạm chỉ tải sau khi trạm có ngày nghiệm thu; hợp đồng này dựa trên thuê đất cùng trạm.”
- **Dễ vướng:** menu chờ ký không hiện batch hoàn tất; dùng URL hoặc xem kết quả tại dự án, không đi tìm bằng bộ lọc Hoàn tất trong action chờ.

### A5 — 5:30–7:15 · Tổ hạ tầng nhận nhắc hạn, xử lý gia hạn thuê đất

- **User/bản ghi/đường mở:** đổi `infra.demo` → **Quản lý hợp đồng BTS → Tổng quan**; xem cảnh báo `DEMO-LAND-TESTED` còn **15 ngày**. Bấm biểu tượng **đồng hồ Hoạt động** ở thanh trên để xem công việc đến hạn của mình; mở HĐ và vùng **Hoạt động** trong chatter để xem đúng cảnh báo của HĐ. Sau đó **Gia hạn hợp đồng → DEMO-RENEWAL-PRACTICE** ([ID2](http://127.0.0.1:8079/web#id=2&model=bts.contract.renewal&view_type=form&action=235)).
- **Điều kiện/nhập/file:** gia hạn **Dự thảo**, HĐ gốc thuê đất TESTED **Hiệu lực**. Bấm **Bắt đầu thực hiện**; nhập **Ngày ký mới = 28/10/2026**, **Ngày hiệu lực mới = 28/10/2026**, **Ngày hết hạn mới = 12/11/2027**, **Giá thuê mới = 13000000**; tại **File scan gia hạn từ Tổ hạ tầng**, upload **F**. Ngày thực hiện gia hạn giữ **28/10/2026**.
- **Thao tác/kết quả:** lưu → **Gửi BGĐ ký số**. Dấu hiệu: **Chờ BGĐ ký số**, file hiện `DEMO-document.txt`; HĐ gốc vẫn hạn **12/11/2026**, chưa cập nhật chỉ vì Tổ hạ tầng đã nhập đề xuất.
- **Nói:** “Sau khi HĐ có hiệu lực, trách nhiệm chuyển sang Tổ hạ tầng. Nhắc hạn giúp bắt đầu thương lượng; điều khoản mới là đề xuất, chỉ thay HĐ gốc sau BGĐ xác nhận.”
- **Dễ vướng:** phải bắt đầu xử lý mới thấy nút gửi; phải đủ ba ngày mới và file. Đừng chọn nhầm `DEMO-RENEWAL-TESTED` đã hoàn thành hoặc hợp đồng cho thuê trạm.

### A6 — 7:15–8:30 · BGĐ xác nhận gia hạn, không OTP

- **User/bản ghi/đường mở:** đổi `bgd.demo` → **Quản lý hợp đồng BTS → Ký số hợp đồng → Hợp đồng gia hạn chờ ký → DEMO-RENEWAL-PRACTICE**.
- **Điều kiện/nhập/file:** hồ sơ vừa chuyển **Chờ BGĐ ký số**; kiểm tra HĐ gốc **DEMO-LAND-TESTED**, ngày mới **12/11/2027** và giá đề xuất. Trong nhóm **Ký số bởi BGĐ**, upload **F** vào **Hồ sơ gia hạn đã ký số**; đây chỉ là file giả cho demo, không phải file đã được tổ chức chứng thực ký.
- **Thao tác/kết quả:** bấm **Ký số / xác nhận ký**. Dấu hiệu: **Hoàn thành**, có **Người ký (BGĐ)** và **Ngày ký**, biến mất khỏi menu gia hạn chờ ký. Không có bước gửi OTP ở luồng này.
- **Nói:** “Luồng gia hạn hiện triển khai xác nhận file của BGĐ, không dùng OTP như batch ban đầu. Tôi phân biệt rõ hành vi phần mềm đã có với tích hợp chữ ký số chưa triển khai.”
- **Dễ vướng:** không tải file thì bị chặn; Tổ hạ tầng không được bấm nút ký. Nếu không thấy hồ sơ, kiểm tra A5 đã gửi và đăng nhập đúng BGĐ.

### A7 — 8:30–9:30 · Tổ hạ tầng đối chiếu kết quả

- **User/bản ghi/đường mở:** đổi `infra.demo` → mở lại [DEMO-LAND-TESTED](http://127.0.0.1:8079/web#id=3&model=bts.contract&view_type=form&action=234), **Lịch sử gia hạn**; sau đó **Tổng quan** và vùng **Hoạt động** của hợp đồng.
- **Điều kiện/nhập/file:** A6 đã hoàn thành; không nhập/sửa/upload gì.
- **Thao tác/kết quả:** kiểm tra hạn mới **12/11/2027**, giá **13000000 USD**, trạng thái **Hiệu lực**, gia hạn PRACTICE **Hoàn thành**. Cảnh báo 15 ngày của HĐ thuê đất TESTED không còn; activity hết hạn cũ không còn là công việc mở. **Chưa có activity kỳ 2027** vì chưa vào cửa sổ 30 ngày. `DEMO-LEASE-TESTED` vẫn còn hạn **11/11/2026**, nên dashboard vẫn có cảnh báo khác; không kỳ vọng tổng dashboard về 0.
- **Nói:** “Tôi kiểm tra dữ liệu gốc và công việc theo dõi sau phê duyệt, không dừng ở thông báo ký thành công. Gia hạn thuê đất không tự gia hạn hợp đồng nhà mạng.”
- **Dễ vướng:** trang cũ chưa tải lại thì refresh; không đánh dấu thủ công **Hoàn tất** activity để giả lập kết quả gia hạn.

## 6. B — Thực hành đầy đủ 20–30 phút

Dùng **DEMO-LIVE**, không phụ thuộc việc A đã chạy hay chưa. Nếu LIVE đã có batch, không chạy lại bước gửi GĐ1. Bộ ba ngày cố định dưới đây hợp lệ cho ngày kiểm tra 28/10/2026; nếu thực hành sau 12/11/2026, phải chuẩn bị bộ mới hoặc điều khoản hợp lệ, không gọi dữ liệu cũ là sắp hết hạn.

### B1 — 0–2 phút · KSGS nhận dự án đã phân công

- **User/bản ghi/menu:** `ksgs.demo` → **Quản lý dự án BTS → Danh sách dự án → DEMO 01 - Thực hành dự thảo (`DEMO-LIVE`) → Thông tin dự án BTS**; dùng URL project ID2.
- **Trước bước/nhập/file:** dự án chưa có batch, trạm LIVE chưa nghiệm thu; không nhập thêm, không file. Kiểm tra **KSGS phụ trách dự án = DEMO KSGS**, đối tác viễn thông **DEMO Viễn thông Sao Việt**; GĐXN đang trống.
- **Làm/kết quả/xác nhận:** xem thông tin và mở trạm `DEMO-BTS-LIVE`. Dấu hiệu: xem được dự án được giao, có 1 trạm. Không tạo lại dự án/trạm này.
- **Nói:** “Trong vận hành GĐXN tạo dự án và phân công. Riêng bộ này được chuẩn bị kỹ thuật để tập trung vào hợp đồng, không giả vờ tôi vừa chạy quy trình tạo dự án.”
- **Lỗi/cách xử lý:** không thấy dự án thì kiểm tra user `ksgs.demo`; không sửa phân công để tự lấy quyền.

### B2 — 2–6 phút · KSGS chuẩn bị thuê đất và biên bản tại trạm

- **User/bản ghi/menu:** `ksgs.demo` → **Danh sách trạm BTS → DEMO Trạm LIVE → Hồ sơ hợp đồng**; [task ID2](http://127.0.0.1:8079/web#id=2&model=project.task&view_type=form&action=224).
- **Trước bước/nhập/file:** HĐ/BB còn dự thảo. Có thể giữ scan sẵn; để tập upload, bấm bút thay file ở **1. Scan HĐ thuê đất** và **2. Scan BB đàm phán**, chọn **F** cho từng ô rồi lưu. Không thay scan sau khi gửi batch.
- **Làm:** **Chi tiết hợp đồng** → mở `DEMO-LAND-LIVE`; kiểm tra/nhập đúng bảng dưới → lưu → quay lại trạm → **Chi tiết BB đàm phán** → `DEMO-MEMO-LIVE` → kiểm tra/nhập bảng BB → lưu. Dữ liệu đã điền đủ từ trước; không cần xóa để gõ lại.

| Hồ sơ | Trường | Giá trị cụ thể |
|---|---|---|
| HĐ | Mã hợp đồng / Loại hợp đồng / Trạm | `DEMO-LAND-LIVE` / **Thuê đất** / **DEMO Trạm LIVE** |
| HĐ | Đối tác | **DEMO Chủ đất Nguyễn An** |
| HĐ | Ngày ký hợp đồng / Ngày hiệu lực / Ngày hết hạn | **12/11/2025 / 12/11/2025 / 12/11/2026** |
| HĐ | Thời hạn (năm) / Giá thuê / Chu kỳ thanh toán | **1 / 12000000 / Hàng năm**; tiền tệ hiện USD |
| HĐ | Ghi chú | `DEMO thực hành hồ sơ thuê đất tại trạm LIVE` |
| BB | Mã biên bản / Loại / Trạm / Đối tác | `DEMO-MEMO-LIVE` / **Đàm phán thuê đất** / **DEMO Trạm LIVE** / **DEMO Chủ đất Nguyễn An** |
| BB | Ngày đàm phán / Giá thuê thống nhất | **28/10/2026 / 12000000** |

- **Kết quả/xác nhận:** có file trong cả hai hồ sơ, đúng đối tác và ngày; tại trạm hai loại hồ sơ **Đã tải scan**. Nhãn tổng hợp “Chờ ký số” trên trạm chưa có nghĩa đã gửi batch: kiểm tra trạng thái HĐ vẫn **Dự thảo** và dự án chưa có batch.
- **Nói:** “HĐ thuê đất và biên bản là hai chứng từ độc lập cùng trạm. Việc đàm phán thực tế diễn ra ngoài hệ thống; tôi ghi nhận kết quả và bằng chứng.”
- **Lỗi/cách xử lý:** đối tác thuê đất phải là loại **Chủ đất**; không chọn viễn thông. Nếu đã gửi thì form bị khóa, không dùng admin để sửa.

### B3 — 6–8 phút · KSGS gửi cả dự án giai đoạn 1

- **User/bản ghi/menu:** `ksgs.demo` → **Danh sách dự án → DEMO 01 → Hợp đồng trạm → Gửi BGĐ ký số**.
- **Trước bước/nhập/file:** tất cả trạm của LIVE có HĐ thuê đất + BB đủ dữ liệu, còn dự thảo; không có batch đang xử lý. Không nhập thêm/file mới.
- **Làm/kết quả/xác nhận:** bấm gửi một lần; hệ thống tạo batch **Giai đoạn 1 - HĐ thuê đất và BB đàm phán**, 2 dòng, **Đã gửi BGĐ**. HĐ **Chờ ký duyệt**, BB **Chờ phê duyệt**, scan bị khóa. **Ghi mã batch vừa sinh và URL trên thanh địa chỉ: `________`**. Không ấn định trước số kế tiếp vì sequence đã được dùng cho diễn tập/ngoại lệ.
- **Nói:** “Điểm kiểm soát là đủ hồ sơ của tất cả trạm trước khi gửi một đợt ở cấp dự án.”
- **Lỗi/cách xử lý:** có thông báo thiếu trường/trạm thì trở lại đúng trạm bổ sung; có batch chưa hoàn tất thì xử lý batch ấy, không tạo trùng.

### B4 — 8–12 phút · BGĐ ký hai dòng, hoàn tất GĐ1

- **User/bản ghi/menu:** `bgd.demo` → **Quản lý hợp đồng BTS → Ký số hợp đồng → Batch hợp đồng ban đầu** → chọn **dự án DEMO 01 / GĐ1**, mã vừa ghi ở B3; không chọn PENDING hoặc TỪ CHỐI.
- **Trước bước/nhập/file:** batch **Đã gửi BGĐ**, 0/2; không cần file mới; OTP lấy từ Mailpit, email `bgd@demo.invalid`.
- **Làm/kết quả/xác nhận:** thực hiện đầy đủ mục 4 cho dòng **Hợp đồng thuê đất** và dòng **Biên bản đàm phán** → khi 2/2 **Đã ký**, bấm **Hoàn thành batch**. Dấu hiệu batch **Hoàn tất**; `DEMO-LAND-LIVE` **Hiệu lực**, BB **Đã xác nhận**, trạm **Đã kí hợp đồng thuê đất và biên bản đàm phán**. Lưu URL batch để xem lại vì menu chờ không còn hiện.
- **Nói:** “OTP xác nhận người ký từng chứng từ. Trạng thái trạm chỉ chuyển sau khi batch đủ chữ ký và được BGĐ hoàn tất.”
- **Lỗi/cách xử lý:** ký đủ nhưng chưa hoàn tất thì GĐ2 chưa mở; không chỉ đóng hộp thoại rồi đổi vai ngay.

### B5 — 12–14 phút · KSGS nhập mốc nghiệm thu trạm

- **User/bản ghi/menu:** `ksgs.demo` → **Danh sách trạm BTS → DEMO Trạm LIVE → Thông tin trạm BTS**.
- **Trước bước/nhập/file:** batch GĐ1 đã hoàn tất. Nhập **Ngày nghiệm thu/Bàn giao = 28/10/2026**, lưu; không file ở bước này.
- **Làm/kết quả/xác nhận:** quay tab **Hồ sơ hợp đồng**. Ô **3. Scan HĐ cho thuê trạm** trở nên có thể tải. Ngày nghiệm thu dự án được tổng hợp từ trạm; không cố sửa ngày nghiệm thu ở dự án bằng KSGS.
- **Nói:** “Mốc nghiệm thu từng trạm mở điều kiện cho hồ sơ cho thuê. Đây là nhập mốc giả cho demo, không phải phần mềm tự kiểm tra hay thực hiện nghiệm thu kỹ thuật.”
- **Lỗi/cách xử lý:** còn chỉ đọc thì kiểm tra đã lưu ngày trên đúng trạm, không phải chỉ nhập ngày ở project.

### B6 — 14–17 phút · KSGS lập cho thuê trạm, liên kết thuê đất

- **User/bản ghi/menu:** vẫn KSGS, trạm LIVE → **Hồ sơ hợp đồng → 3. Scan HĐ cho thuê trạm** upload **F** → lưu → **Chi tiết hợp đồng**, chọn hồ sơ loại **Cho thuê trạm** mới tạo.
- **Trước bước/nhập/file:** trạm đã nghiệm thu; `DEMO-LAND-LIVE` hiệu lực. Hệ thống tự tạo hồ sơ dự thảo sau tải scan; **không bấm tạo thêm một HĐ khác**.
- **Nhập:** mã **`DEMO-LEASE-LIVE`**; loại **Cho thuê trạm**; trạm **DEMO Trạm LIVE**; đối tác **DEMO Viễn thông Sao Việt**; **Hợp đồng thuê đất liên quan = `bts.contract,2` / DEMO-LAND-LIVE**, cùng trạm; ngày ký/hiệu lực **28/10/2026**, hết hạn **07/11/2026**, thời hạn nhập **1**, giá **24000000**, chu kỳ **Hàng năm**; giữ file F vừa tải. Giá và kỳ ngắn là dữ liệu giả.
- **Làm/kết quả/xác nhận:** lưu, mở HĐ thuê đất được liên kết để đối chiếu **Trạm BTS = LIVE**, hết hạn **12/11/2026**, rồi quay lại. Dấu hiệu HĐ cho thuê **Dự thảo**, có đối tác/file/ngày và liên kết thuê đất cùng trạm.
- **Nói:** “Đất là cơ sở để cho nhà mạng thuê trạm. Tôi kiểm tra liên kết cùng trạm và chủ động chọn thời hạn nằm trong kỳ thuê đất.”
- **Lỗi/cách xử lý:** ô liên kết có thể hiện ID kỹ thuật; đừng chọn `bts.contract,3` của TESTED. Cùng trạm được constraint backend kiểm tra; không tuyên bố backend ban đầu đã kiểm tra mọi quan hệ thời hạn như luồng gia hạn.

### B7 — 17–20 phút · Gửi và ký batch giai đoạn 2

- **User/bản ghi/menu:** KSGS → dự án LIVE → **Hợp đồng trạm → Gửi BGĐ ký số**; ghi mã batch mới **`________`**. Đổi BGĐ → menu **Batch hợp đồng ban đầu**, chọn đúng **DEMO 01 / Giai đoạn 2 - HĐ cho thuê trạm**.
- **Trước bước/nhập/file:** GĐ1 **Hoàn tất**; trạm có nghiệm thu và cho thuê dự thảo đủ trường/scan. Không file mới/nhập điều khoản; một OTP mới lấy Mailpit.
- **Làm/kết quả/xác nhận:** batch GĐ2 có **1 dòng** `DEMO-LEASE-LIVE` → ký theo mục 4 → **Hoàn thành batch**. HĐ **Hiệu lực**, trạm **Đã kí hợp đồng cho thuê trạm**, batch **Hoàn tất**. Không gọi trạm này đã bàn giao vận hành/bảo trì: chưa chạy luồng đó.
- **Nói:** “Hai giai đoạn có điều kiện và chứng từ khác nhau. Chỉ hoàn tất GĐ1 chưa đủ để cho thuê trạm.”
- **Lỗi/cách xử lý:** báo còn batch đang xử lý thì hoàn tất GĐ1; báo thiếu cho thuê thì kiểm tra B5/B6 cho đúng trạm.

### B8 — 20–22 phút · Tổ hạ tầng đọc hạn và khởi tạo gia hạn mới

- **User/bản ghi/menu:** `infra.demo` → **Tổng quan** → cảnh báo `DEMO-LEASE-LIVE` → **Mở chi tiết**; có thể **Danh sách dự án → DEMO 01 → Trạm có hợp đồng đến hạn** để mở HĐ từ dòng trạm.
- **Trước bước/nhập/file:** cho thuê LIVE hiệu lực, hạn **07/11/2026** (còn 10 ngày), thuê đất hạn **12/11/2026** (15 ngày), nhắc trước 30. Chưa có gia hạn LIVE; không file trước khi mở form.
- **Làm/kết quả/xác nhận:** xem công việc nhắc hạn của **DEMO INFRA** trong chatter hoặc đồng hồ Hoạt động. Bấm **Tạo bản ghi gia hạn** trên HĐ; form mới gắn đúng HĐ `DEMO-LEASE-LIVE`. Nhập **Mã gia hạn = DEMO-RENEWAL-LIVE**, **Ngày thực hiện gia hạn = 28/10/2026**, ghi chú `DEMO gia hạn cho thuê trạm LIVE`; lưu hộp thoại. Mở lại qua **Gia hạn hợp đồng**, tìm mã vừa tạo.
- **Nói:** “Tôi tạo một hồ sơ gia hạn riêng để giữ lịch sử. Hợp đồng gốc chưa thay đổi khi mới lập đề nghị.”
- **Lỗi/cách xử lý:** không chọn PRACTICE của thuê đất TESTED. Nút Tạo bản ghi gia hạn đòi user Tổ hạ tầng và HĐ hiệu lực/đã thống nhất gia hạn.

### B9 — 22–24 phút · Tổ hạ tầng nhập và gửi điều khoản hợp lệ

- **User/bản ghi/menu:** `infra.demo` → **Gia hạn hợp đồng → DEMO-RENEWAL-LIVE → Bắt đầu thực hiện**.
- **Trước bước/nhập/file:** gia hạn mới **Dự thảo**, HĐ thuê đất cùng trạm đang **Hiệu lực**, hết hạn 12/11. Nhập **Ngày ký mới = 28/10/2026**, **Ngày hiệu lực mới = 28/10/2026**, **Ngày hết hạn mới = 11/11/2026**, **Giá thuê mới = 25000000**; upload **F** vào **File scan gia hạn từ Tổ hạ tầng**.
- **Làm/kết quả/xác nhận:** lưu → **Gửi BGĐ ký số** → **Chờ BGĐ ký số**. HĐ gốc còn hạn 07/11 và giá 24000000. Không nhập hạn xa hơn 12/11 vì lease được bảo đảm bằng kỳ đất còn lại.
- **Nói:** “Gia hạn nhà mạng chỉ đến phạm vi đất đang có. Nếu muốn kéo dài thêm một năm, phải xử lý gia hạn đất trước rồi mới đề xuất cho thuê trạm tương ứng.”
- **Lỗi/cách xử lý:** muốn diễn ngoại lệ quá hạn, làm mục E5 trên bộ diễn tập riêng; trong luồng hợp lệ giữ 11/11. Nếu thiếu file/ngày thì bổ sung, không đổi trạng thái thủ công.

### B10 — 24–26 phút · BGĐ xác nhận hồ sơ gia hạn

- **User/bản ghi/menu:** `bgd.demo` → **Ký số hợp đồng → Hợp đồng gia hạn chờ ký → DEMO-RENEWAL-LIVE**.
- **Trước bước/nhập/file:** **Chờ BGĐ ký số**; kiểm tra trạm LIVE, hạn 11/11. Upload **F** vào **Hồ sơ gia hạn đã ký số** trong nhóm **Ký số bởi BGĐ**.
- **Làm/kết quả/xác nhận:** bấm **Ký số / xác nhận ký**, không tìm nút OTP. **Hoàn thành**, có người/ngày ký. Server kiểm tra lại bao phủ thuê đất lúc ký, không chỉ khi Tổ hạ tầng gửi.
- **Nói:** “Phê duyệt là điểm áp dụng điều khoản mới vào hợp đồng gốc; điều kiện thuê đất được kiểm lại tại thời điểm quyết định.”
- **Lỗi/cách xử lý:** file mới tải nhưng chưa xong thì chờ; nút ký tự lưu dữ liệu form trước khi thực thi. Nếu không phải BGĐ thì đổi user đúng vai.

### B11 — 26–28 phút · Tổ hạ tầng xác nhận dữ liệu gốc và nhắc hạn

- **User/bản ghi/menu:** `infra.demo` → mở `DEMO-LEASE-LIVE` qua **Tổng quan → Mở chi tiết**, tab **Lịch sử gia hạn**, vùng **Hoạt động**.
- **Trước bước/nhập/file:** B10 hoàn thành; không nhập/sửa/upload.
- **Làm/kết quả/xác nhận:** HĐ vẫn **Hiệu lực**, ngày hết hạn **11/11/2026**, giá **25000000 USD**, lịch sử có `DEMO-RENEWAL-LIVE` **Hoàn thành**. Cảnh báo theo hạn cũ 07/11 được đóng và tính lại theo hạn 11/11; công việc mở cho infra có deadline hôm nay **28/10/2026** do vẫn trong cửa sổ nhắc. Dashboard vẫn **Sắp hết hạn**: gia hạn thêm 4 ngày không đưa HĐ ra ngoài cửa sổ 30 ngày. `alert_before_days` không tự đổi.
- **Nói:** “Tôi kiểm thử kết quả sau phê duyệt trên hợp đồng và công việc liên quan. Gia hạn thành công không có nghĩa mọi cảnh báo phải biến mất.”
- **Lỗi/cách xử lý:** phải tải lại trang để thấy dữ liệu mới; không đánh dấu công việc thủ công để thay kết quả hệ thống. Kịch bản A cho ví dụ gia hạn xa khiến cảnh báo và activity mở biến mất.

## 7. Ngoại lệ có bằng chứng thực thi và cách trở về luồng hợp lệ

**Không dùng `KS-HĐ-0003` để thử từ chối trước phỏng vấn.** Đã tạo bộ riêng để bạn thử; các thông báo trong ngoặc kép bên dưới là thông báo đã thu từ Odoo, không phải diễn giải tự đặt. Phân biệt thông báo backend đã chạy với thao tác UI bị ẩn/chỉ đọc.

### E1 — Thiếu hồ sơ của một trạm

- **Dữ liệu/đường mở:** `ksgs.demo` → **Danh sách dự án → DEMO NGOẠI LỆ - Dữ liệu kiểm tra riêng**, mã **DEMO-EXCEPTION**, project ID6; **DEMO Trạm NGOẠI LỆ**, mã **DEMO-BTS-EXCEPTION**, task ID6, chưa HĐ/BB. [Mở dự án](http://127.0.0.1:8079/web#id=6&model=project.project&view_type=form&action=223).
- **Thao tác:** tab **Hợp đồng trạm → Gửi BGĐ ký số**, không cần nhập/file.
- **Thông báo đã chạy qua ORM đúng user:** “Chưa đủ HĐ thuê đất/BB đàm phán cho tất cả trạm.”, dòng chi tiết “- DEMO Trạm NGOẠI LỆ: thiếu HĐ thuê đất; thiếu BB đàm phán”. Không tạo batch thành công.
- **Ý nghĩa/cách về:** batch là kiểm soát đủ bộ hồ sơ, không chỉ có một file bất kỳ. Đóng thông báo; muốn tiếp tục thì vào trạm tải F vào hai scan và nhập dữ liệu như B2 với mã riêng có hậu tố EXCEPTION. Để bộ này lặp lại E1, chỉ đóng thông báo, không cần sửa gì.

### E2 — KSGS không ký và không sửa nội dung đã gửi

- **Dữ liệu/đường mở:** `ksgs.demo` → trạm PENDING, tab **Hồ sơ hợp đồng**, mở HĐ **DEMO-LAND-PENDING**. Không nhập/file.
- **UI:** hồ sơ đã gửi chỉ đọc, không có nút ký của BGĐ. Đã kiểm tra backend trên HĐ diễn tập **DEMO-LAND-REHEARSAL** lúc submitted: ghi `Ghi chú` bị chặn với “KSGS không thể sửa hồ sơ đã được gửi vào quy trình ký số.”; gọi ký HĐ lẻ bị chặn với “KSGS không được ký hoặc từ chối từng hợp đồng riêng lẻ.” Không nói rằng bấm một nút ẩn trên UI sẽ hiện hai thông báo này.
- **Ý nghĩa/cách về:** người lập không tự phê duyệt hoặc thay nội dung sau khi gửi. Nếu BGĐ chưa ký dòng nào, BGĐ có thể từ chối batch để trả hồ sơ về dự thảo, KSGS sửa rồi gửi lại; không lấy quyền admin sửa thẳng hồ sơ đang chờ.

### E3 — BGĐ từ chối batch trước khi ký

- **Dữ liệu/đường mở:** `bgd.demo` → **Ký số hợp đồng → Batch hợp đồng ban đầu → KS-HĐ-0007**, dự án **DEMO TỪ CHỐI - Dữ liệu kiểm tra riêng**, mã **DEMO-REJECT**, project ID7, trạm **DEMO Trạm TỪ CHỐI**, `DEMO-BTS-REJECT`, task ID7; 0/2, **Đã gửi BGĐ**. [Mở batch](http://127.0.0.1:8079/web#id=7&model=bts.contract.signature.batch&view_type=form&action=243).
- **Thao tác:** để trống **Lý do từ chối** → **Từ chối batch**. Kiểm chứng backend cùng workflow trên `KS-HĐ-0004`: “Vui lòng nhập lý do từ chối batch.” Sau đó nhập **`DEMO cần bổ sung nội dung file scan trước khi ký.`**, lưu → **Từ chối batch**; không OTP/file.
- **Hành vi đã kiểm chứng:** trên bộ diễn tập `KS-HĐ-0004`, batch **Từ chối**, HĐ/BB trả **Dự thảo**. `KS-HĐ-0007` được để nguyên **Đã gửi BGĐ** để bạn tự diễn. Không khẳng định đã bấm từ chối KS-HĐ-0007.
- **Ý nghĩa/cách về:** trả lại để sửa có lý do và dấu vết; không thể dùng như thao tác rollback sau khi đã có chữ ký. KSGS mở trạm TỪ CHỐI, sửa ghi chú/scan, quay dự án gửi lại; **batch mới** sẽ được sinh, batch bị từ chối giữ lịch sử. Không có nút reset batch cũ trong luồng này.

### E4 — Chưa nghiệm thu và liên kết sai trạm

- **Dữ liệu/thao tác UI:** KSGS → **DEMO Trạm NGOẠI LỆ** chưa nghiệm thu → **Hồ sơ hợp đồng**: **3. Scan HĐ cho thuê trạm** chỉ đọc, không cần upload để trình bày. Nhập ngày nghiệm thu đúng trạm rồi lưu sẽ mở ô upload, như B5.
- **Backend đã chạy trên trạm DIỄN TẬP trước nghiệm thu:** thử ghi scan bị chặn: “Chỉ được tải HĐ cho thuê trạm sau khi trạm đã có ngày nghiệm thu.” Thử tạo HĐ cho thuê của trạm DIỄN TẬP nhưng chọn thuê đất TESTED bị chặn: “Hợp đồng cho thuê trạm phải liên kết với hợp đồng thuê đất cùng trạm.”
- **Ý nghĩa/cách về:** UI ngăn sớm, constraint bảo vệ cả khi gọi API. Dropdown UI đã lọc cùng trạm nên **không hứa có thể chọn sai từ dropdown thông thường**. Sửa mốc nghiệm thu/liên kết đúng trạm; thao tác API sai đã rollback, không để lại HĐ lỗi.

### E5 — Gia hạn cho thuê trạm vượt hạn đất

- **Dữ liệu tại thời điểm kiểm:** `DEMO-LEASE-REHEARSAL`, trạm **DEMO Trạm DIỄN TẬP**, đất khi ấy hết hạn **12/11/2026**; hồ sơ **DEMO-RENEWAL-REHEARSAL**, Tổ hạ tầng đã nhập hạn mới **17/11/2026**, có file F và ba ngày mới. Sau phép thử này, thuê đất diễn tập đã được gia hạn đến **12/11/2027** để kiểm tra nhắc hạn; không dùng trạng thái hiện tại để lặp lại nguyên lỗi 17/11/2026.
- **Thao tác/nguồn bằng chứng:** đúng user `infra.demo`, gọi **Gửi BGĐ ký số** qua HTTP. Thông báo thật: “Không thể gia hạn HĐ cho thuê trạm DEMO-LEASE-REHEARSAL đến ngày 17/11/2026: HĐ thuê đất cùng trạm phải đang hiệu lực và có ngày hết hạn không sớm hơn ngày hết hạn mới.”
- **Ý nghĩa/cách về:** không cam kết thuê trạm vượt quyền sử dụng đất. Đã sửa về **11/11/2026**, gửi lại theo workflow hợp lệ. Khi muốn tự thử trên LIVE, chỉ thực hiện trước B9 gửi thành công: thử **17/11**, đóng lỗi rồi sửa **11/11**. Không sửa hồ sơ diễn tập đã hoàn tất để chạy lại.

## 8. Mức xác minh, bộ bắt đầu còn nguyên và giới hạn

**Bằng chứng local** (bị Git bỏ qua, không chép mật khẩu/OTP sang tài liệu): `demo/.local/scenario-inventory.json`, `rehearsal-events.json`, `exception-ready.json`, `scenario-ui-events.json`, `scenario-ui-last.txt`, `scenario-final-check.json`, `project-view-binding.json`, ảnh `scenario-*.png`; và báo cáo kiểm thử ở lần thiết lập trước.

- Đã đọc registry/ACL/record rule/field labels và dữ liệu bằng ORM; đọc Python/XML các action ký, gửi batch, gia hạn, nhắc hạn; kiểm tra giao diện Chrome bằng tài khoản nghiệp vụ.
- Đã tạo bộ **DEMO DIỄN TẬP - Kiểm chứng kịch bản**, mã **DEMO-REHEARSAL**, project/task ID5, qua đúng vai trò GĐXN/KSGS. Đã thử thiếu hồ sơ, sai quyền, sai liên kết, chưa nghiệm thu, từ chối không lý do và từ chối hợp lệ, rồi gửi lại. `KS-HĐ-0004` lưu **Từ chối**, GĐ1 gửi lại là `KS-HĐ-0005`, GĐ2 là `KS-HĐ-0006`. Chữ ký OTP thực hiện trên bộ diễn tập, không dùng hết batch PENDING của người dùng.
- Ký OTP trên Chrome dùng luồng **Ký số → Gửi mã OTP → Xác nhận và ký số**, mã lấy từ Mailpit; không hard-code/đặt trạng thái đã ký. Cuối cùng kiểm tra đủ **3 dòng diễn tập đã ký**, OTP **used**, chữ ký nội bộ hợp lệ, hai batch **Hoàn tất**. Đã tải F trên UI vào hồ sơ gia hạn **DEMO-RENEWAL-REHEARSAL** ID3, bấm **Ký số / xác nhận ký** trên Chrome, hồ sơ **Hoàn thành**, không OTP.
- Đã dùng thêm gia hạn thuê đất riêng **DEMO-RENEWAL-LAND-REHEARSAL** ID4 để kiểm chứng tình huống của A7 qua ORM đúng user: hạn đất diễn tập **12/11/2027**, giá **13000000**, số activity mở hết hạn của HĐ đó từ **2 xuống 0** (hai người nhận hạ tầng). Không tạo activity kỳ mới khi chưa đến cửa sổ nhắc. HĐ gốc của người dùng TESTED không bị thay đổi bởi phép thử này.
- Đã điều chỉnh **cấu hình chọn view** của action dự án trong database demo: thêm hai liên kết `ir.actions.act_window.view`, có XML ID `bts_local_demo.project_action_tree/form`. Script idempotent [bind_project_views.py](bind_project_views.py) lưu lại cách áp dụng. Nếu khôi phục một database mới, cần chạy script này; không coi đây là thay đổi đã áp vào source module gốc.
- Các bộ diễn tập/ngoại lệ cũng xuất hiện trong danh sách/dashboard tổng hợp; **không đọc số tổng toàn database thành số của riêng DEMO-TESTED**. Chọn tên HĐ/dự án nêu trong cảnh để đối chiếu.
- Chưa kiểm chứng nhà cung cấp chữ ký số/SMS thực tế (không được tích hợp ở luồng này); chưa chờ đủ 5 phút để kiểm thử hết hạn hoặc thử sai đủ 5 lần trên bộ hiện tại; chưa kiểm thử mọi tổ hợp quyền, toàn bộ nhánh hủy/thất bại hoặc lịch cron chạy tự động. GĐXN được kiểm qua ORM/nhóm/ACL, chưa đăng nhập UI vì không đặt mật khẩu cho user có sẵn.
- Không reset/xóa dữ liệu hiện có, không sửa logic nghiệp vụ, không commit/push. SMTP demo chỉ tới Mailpit; các container Odoo/PostgreSQL/Mailpit vẫn dùng mạng backend cách ly.

**Khi bàn giao, các đầu vào dành cho bạn vẫn là:** LIVE HĐ/BB **Dự thảo**, không batch/không nghiệm thu; PENDING `KS-HĐ-0003` **Đã gửi BGĐ**, **0/2**; PRACTICE **Dự thảo**; EXCEPTION **thiếu hồ sơ, không batch**; REJECT `KS-HĐ-0007` **Đã gửi BGĐ**, **0/2**. Không chạy `demo/verify.py` để “chuẩn bị lại” vì nó có thao tác trên dữ liệu, không phải nút reset demo.

## 9. Xử lý lỗi và tự ôn BA

| Gặp gì | Kiểm tra và xử lý |
|---|---|
| Không mở được web | Mở Docker Desktop, dùng lệnh **Start/Status** trong [README](README.md); cổng đúng là **8079**, không phải 8069 |
| URL báo không đủ quyền | Nhìn user đang đăng nhập; KSGS không mở gia hạn/app hợp đồng. Chuyển đúng user; URL không cấp thêm quyền |
| Không thấy hồ sơ trong menu chờ | Kiểm tra trạng thái thực tế và dự án. Batch/renewal hoàn tất hoặc bị từ chối không thuộc domain chờ; mở URL đã lưu hoặc danh sách gia hạn đầy đủ |
| Có nhiều email trong Mailpit | Lọc người nhận `bgd@demo.invalid`, mở thư OTP mới nhất của lần gửi hiện tại. Module có user demo gốc với email khác; mọi thư vẫn chỉ bị bắt local |
| Hộp OTP không đóng | Đọc phản hồi, đúng dòng/mã/user/thời hạn; mã sai/hết hạn thì gửi mã mới theo workflow. Không dùng SMS hoặc chỉnh hash/trạng thái |
| Gia hạn gửi/kiểm tra ký thất bại | Đủ ngày và scan của Tổ hạ tầng, file BGĐ; HĐ đất cùng trạm phải hiệu lực/đã thống nhất gia hạn và bao phủ hạn mới đối với cho thuê trạm |
| Giá hiện `$`, quan hệ hiện `bts.contract,N` | Đây là cấu hình/hiển thị hiện có. Gọi đúng tiền tệ giả USD, mở bản ghi đối chiếu mã/trạm; không tự nói đó là VND |
| Muốn chạy lại từ đầu sau khi đã ký | Không đổi ngược trạng thái hoặc xóa batch. Dùng bộ chưa dùng; nếu cần thêm, chuẩn bị bộ mới có mã DEMO riêng qua ORM và quyền chuẩn |

Ba câu nên tự trả lời trước phỏng vấn: **Ai chịu trách nhiệm ở trạng thái này? Điều kiện gì cho phép chuyển tiếp? Tôi kiểm tra dữ liệu và công việc nào sau quyết định?** Nút bấm là cách thể hiện ba câu trả lời đó trên Odoo.

Nguồn đối chiếu trong repo: [phạm vi dự án theo user](../addons/dtc_bts_base/models/ir_rule.py), [guard dự án/phân công](../addons/dtc_bts_base/models/project_project.py), [chuẩn bị scan tại trạm](../addons/dtc_bts_contract/models/project_task.py), [gửi batch từ dự án](../addons/dtc_bts_contract/models/project_project.py), [batch/OTP/chữ ký](../addons/dtc_bts_contract/models/bts_contract_signature_batch.py), [gia hạn](../addons/dtc_bts_contract/models/bts_contract_renewal.py), [nhắc hạn](../addons/dtc_bts_contract/models/bts_contract.py), [form OTP/batch](../addons/dtc_bts_contract/views/bts_contract_signature_batch_views.xml), [form gia hạn](../addons/dtc_bts_contract/views/bts_contract_renewal_views.xml). Menu/giá trị hiển thị trong kịch bản đã đối chiếu database và Chrome, không chỉ dựa vào mô tả manifest.
