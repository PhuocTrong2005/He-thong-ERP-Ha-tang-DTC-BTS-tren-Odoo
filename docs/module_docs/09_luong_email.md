# Mô tả các luồng email trong hệ thống DTC BTS

Tài liệu này mô tả các trường hợp hệ thống gửi email trong quá trình làm việc. Nội
dung được trình bày theo trình tự nghiệp vụ để người sử dụng dễ theo dõi: ai thực
hiện công việc, hệ thống thông báo cho ai và người nhận cần làm gì tiếp theo.

## 1. Phân công dự án cho KSGS

Khi Giám đốc Xí nghiệp tạo dự án và phân công KSGS phụ trách, hệ thống gửi email
cho KSGS được giao nhiệm vụ. Email cho biết dự án nào vừa được phân công, thông
tin cơ bản của dự án và đường dẫn để KSGS mở dự án trên hệ thống.

Nếu Giám đốc Xí nghiệp thay đổi người phụ trách, KSGS mới sẽ nhận được email phân
công. Từ thời điểm đó, KSGS mới chịu trách nhiệm theo dõi và thực hiện các công
việc của dự án.

## 2. Trình ký hồ sơ hợp đồng

Sau khi chuẩn bị đầy đủ hồ sơ, KSGS gửi yêu cầu ký đến Ban Giám đốc. Hệ thống gửi
email cho người có trách nhiệm ký, trong đó ghi rõ dự án, loại hồ sơ, số lượng hồ
sơ và thời hạn xử lý.

Ban Giám đốc mở hồ sơ từ email và thực hiện ký số. Khi yêu cầu gửi mã xác thực,
hệ thống gửi mã OTP đến email của chính người đang ký. Mã OTP chỉ có hiệu lực
trong thời gian ngắn và chỉ được sử dụng một lần.

Nếu hồ sơ được ký hoàn tất, hệ thống gửi email cho KSGS và người đã lập đợt trình
ký để thông báo hồ sơ đã hoàn thành.

Nếu Ban Giám đốc từ chối ký, người từ chối phải ghi rõ lý do. Hệ thống gửi email
cho KSGS và người lập đợt trình ký để họ biết nguyên nhân, chỉnh sửa hồ sơ và
trình lại khi cần.

## 3. Xử lý trường hợp không thương lượng được hợp đồng ban đầu

Khi KSGS không thương lượng được hợp đồng thuê đất, KSGS ghi nhận nguyên nhân
trên hệ thống. Hệ thống gửi email cho Giám đốc Xí nghiệp để xem xét.

Giám đốc Xí nghiệp có thể tiếp tục xử lý hoặc trình Ban Giám đốc quyết định. Khi
trình lên Ban Giám đốc, hệ thống gửi email kèm thông tin dự án, trạm và lý do
thương lượng không thành công.

Sau khi có quyết định hủy trạm hoặc hủy dự án, hệ thống gửi email cho những
người liên quan để tất cả cùng biết kết quả cuối cùng và dừng các công việc không
còn cần thiết.

## 4. Luồng yêu cầu vật tư và cấp phát kho

Một yêu cầu vật tư chỉ hoàn thành sau khi đã đi hết các bước duyệt yêu cầu, đặt
hàng, nhập kho, cấp phát và khóa đơn mua hàng. Việc Trưởng phòng duyệt yêu cầu
không có nghĩa là vật tư đã sẵn sàng cấp phát.

### Bước 1: KSGS gửi yêu cầu vật tư

KSGS lập yêu cầu cấp vật tư cho dự án và gửi duyệt. Hệ thống gửi email cho Trưởng
phòng Kế hoạch để thông báo có yêu cầu mới cần xử lý.

Trưởng phòng Kế hoạch có thể duyệt, tạm hoãn hoặc từ chối yêu cầu:

- Nếu duyệt, yêu cầu chuyển sang giai đoạn chờ đặt hàng. Hệ thống chưa chuyển yêu
  cầu sang trạng thái sẵn sàng cấp phát.
- Nếu tạm hoãn, KSGS nhận được email thông báo kèm lý do tạm hoãn.
- Nếu từ chối, KSGS nhận được email nêu rõ lý do để điều chỉnh và gửi lại khi cần.

### Bước 2: Đặt hàng và thông báo cho Thủ kho

Sau khi yêu cầu được duyệt, bộ phận Kế hoạch lập đơn mua hàng cho đúng dự án và
xác nhận đặt hàng.

Khi đơn hàng được xác nhận, hệ thống gửi email cho Thủ kho. Email cho biết đơn
hàng nào đã được đặt, phục vụ dự án nào và yêu cầu vật tư nào đang chờ nhập kho.
Thủ kho dựa vào thông tin này để chuẩn bị tiếp nhận hàng.

Ở bước này, yêu cầu đang trong giai đoạn chờ hàng về kho. KSGS chưa thể đến nhận
vật tư và Thủ kho chưa thể lập phiếu xuất.

### Bước 3: Hàng về kho và xác nhận phiếu nhập

Khi nhà cung cấp giao hàng, Thủ kho tạo phiếu nhập kho theo đúng đơn mua hàng và
xác nhận số lượng thực tế đã nhận.

Nếu hàng mới về một phần, yêu cầu tiếp tục ở trạng thái chờ nhập đủ. Hệ thống
chưa gửi email sẵn sàng cấp phát cho KSGS.

Khi kho đã nhận đủ toàn bộ số lượng được duyệt, yêu cầu chuyển sang trạng thái
**Sẵn sàng cấp phát**. Hệ thống gửi email cho đúng KSGS đã tạo yêu cầu, thông báo
vật tư của dự án đã sẵn sàng và có thể đến kho nhận hàng.

### Bước 4: KSGS đến nhận và Thủ kho xác nhận phiếu xuất

Sau khi nhận được email, KSGS đến kho nhận vật tư. Thủ kho tạo phiếu xuất gắn với
đúng yêu cầu và xác nhận số lượng thực tế đã giao.

Nếu mới giao một phần, yêu cầu được ghi nhận là đã cấp phát một phần và chưa kết
thúc. Hệ thống chưa gửi yêu cầu khóa đơn mua hàng.

Khi Thủ kho đã xuất đủ toàn bộ vật tư, yêu cầu chuyển sang trạng thái **Hoàn tất
yêu cầu**. Hệ thống gửi email cho Trưởng phòng Kế hoạch, thông báo việc cấp phát
đã hoàn tất và đề nghị kiểm tra, khóa đơn mua hàng.

### Bước 5: Trưởng phòng khóa đơn mua hàng

Trưởng phòng Kế hoạch mở yêu cầu từ thông báo, kiểm tra phiếu nhập, phiếu xuất và
đơn mua hàng. Sau khi thông tin đã đầy đủ, Trưởng phòng thực hiện **Khóa PO**.

Chỉ khi hoàn thành bước khóa PO thì toàn bộ luồng yêu cầu vật tư mới được xem là
kết thúc.

Tóm tắt luồng kho:

> KSGS gửi yêu cầu → Trưởng phòng duyệt → xác nhận đặt hàng → Thủ kho nhận email
> chờ nhập → Thủ kho xác nhận nhập đủ → KSGS nhận email sẵn sàng cấp phát →
> Thủ kho xác nhận xuất đủ → Trưởng phòng nhận email hoàn tất → Trưởng phòng
> khóa PO.

## 5. Hoàn thành và bàn giao dự án sang bảo trì

Khi toàn bộ công việc của dự án đã hoàn thành, hệ thống gửi email cho Giám đốc
Xí nghiệp để thông báo dự án đã đủ điều kiện bàn giao.

Giám đốc Xí nghiệp thực hiện bàn giao dự án cho Tổ quản lý hạ tầng. Hệ thống gửi
email cho những người thuộc Tổ quản lý hạ tầng, kèm thông tin dự án và yêu cầu
tiếp nhận.

Sau khi Tổ quản lý hạ tầng xác nhận tiếp nhận, dự án chính thức chuyển sang giai
đoạn vận hành và bảo trì. Hệ thống gửi email lại cho Giám đốc Xí nghiệp để xác
nhận việc bàn giao đã hoàn tất.

## 6. Nhắc lịch bảo trì

Hằng ngày, hệ thống kiểm tra các thiết bị và trạm sắp đến hạn bảo trì. Trước ngày
đến hạn, người phụ trách nhận được email nhắc việc.

Nếu thiết bị đã được giao cho một kỹ thuật viên cụ thể, email được gửi cho kỹ
thuật viên đó. Nếu chưa phân công kỹ thuật viên, hệ thống gửi thông báo cho Tổ
quản lý hạ tầng để bố trí người thực hiện.

Email nhắc bảo trì cho biết dự án, trạm, thiết bị, ngày đến hạn và các công việc
cần theo dõi. Các nội dung đến hạn được tổng hợp để hạn chế gửi quá nhiều email
riêng lẻ trong cùng một ngày.

## 7. Gia hạn hợp đồng

Khi hợp đồng sắp hết hạn, hệ thống gửi email nhắc Tổ quản lý hạ tầng kiểm tra và
chuẩn bị hồ sơ gia hạn. Email tổng hợp các hợp đồng cần xử lý theo từng dự án để
người phụ trách dễ theo dõi.

Sau khi chuẩn bị xong hồ sơ gia hạn, Tổ quản lý hạ tầng gửi trình ký. Hệ thống gửi
email cho Ban Giám đốc để xem xét.

Nếu Ban Giám đốc ký hoàn tất, hệ thống gửi email cho người thực hiện hồ sơ để xác
nhận hợp đồng đã được gia hạn.

Nếu Ban Giám đốc từ chối, hệ thống gửi email kèm lý do để người thực hiện điều
chỉnh hồ sơ và trình lại.

## 8. Trường hợp không thể gia hạn hợp đồng

Nếu Tổ quản lý hạ tầng xác định hợp đồng thuê đất hoặc thuê trạm không thể gia
hạn, người phụ trách ghi nhận lý do trên hệ thống. Hệ thống gửi email cho Giám
đốc Xí nghiệp để xem xét phương án xử lý.

Khi cần xin quyết định của Ban Giám đốc, Giám đốc Xí nghiệp trình trường hợp này
lên hệ thống. Ban Giám đốc nhận được email nêu rõ hợp đồng, dự án, trạm và lý do
không thể gia hạn.

Sau khi có quyết định hủy trạm hoặc hủy dự án, hệ thống gửi email cho các bên
liên quan để thực hiện quyết định và kết thúc hồ sơ.

## 9. Nguyên tắc chung khi nhận email

Email được gửi đến đúng người đang phụ trách hoặc đúng nhóm có trách nhiệm xử lý
bước tiếp theo. Vì vậy, người dùng cần có địa chỉ email hợp lệ và đang hoạt động
trên hệ thống.

Mỗi email cung cấp thông tin nhận biết hồ sơ và đường dẫn mở công việc tương ứng.
Người nhận nên mở hồ sơ trên hệ thống, kiểm tra nội dung rồi thực hiện đúng thao
tác được yêu cầu.

Nếu một công việc chưa đủ điều kiện chuyển bước, hệ thống không gửi email của
bước tiếp theo. Ví dụ:

- Duyệt yêu cầu vật tư không làm phát sinh email “Sẵn sàng cấp phát”.
- Nhập kho chưa đủ số lượng không gửi email cho KSGS đến nhận hàng.
- Xuất kho chưa đủ số lượng không gửi email cho Trưởng phòng khóa PO.
- Hồ sơ trình ký bị từ chối không được xem là đã hoàn tất.

Các nguyên tắc này giúp email phản ánh đúng tình trạng thực tế và tránh việc
người nhận thực hiện công việc quá sớm.

## 10. Bảng tổng hợp các email nghiệp vụ

| Tên email | Điều kiện/hành động kích hoạt quá trình gửi | Tác nhân | Người nhận | Mẫu email |
| --- | --- | --- | --- | --- |
| Thông báo phân công dự án | Dự án được tạo và đã chọn KSGS phụ trách, hoặc dự án được chuyển cho KSGS khác | Giám đốc Xí nghiệp | KSGS được phân công | **Tiêu đề:** Phân công phụ trách dự án `[Mã dự án]`<br>**Nội dung:** Anh/chị được phân công phụ trách dự án `[Tên dự án]`. Vui lòng mở hệ thống để xem thông tin và triển khai công việc. |
| Yêu cầu Ban Giám đốc ký hồ sơ | Hồ sơ đã chuẩn bị xong và được gửi trình ký | KSGS | Ban Giám đốc phụ trách ký | **Tiêu đề:** Đề nghị ký hồ sơ dự án `[Tên dự án]`<br>**Nội dung:** Hồ sơ `[Loại hồ sơ]` đã được gửi trình ký. Kính đề nghị Ban Giám đốc kiểm tra và xử lý trước `[Hạn xử lý]`. |
| Mã OTP xác thực ký số | Người ký yêu cầu gửi mã OTP khi đang thực hiện ký hồ sơ | Thành viên Ban Giám đốc đang ký | Chính người đang thực hiện ký | **Tiêu đề:** Mã OTP xác thực ký số<br>**Nội dung:** Mã xác thực của anh/chị là `[Mã OTP]`. Mã chỉ có hiệu lực trong 5 phút và không cung cấp cho người khác. |
| Hồ sơ đã ký hoàn tất | Toàn bộ hồ sơ trong đợt trình ký đã được ký đầy đủ | Ban Giám đốc | KSGS và người lập đợt trình ký | **Tiêu đề:** Hồ sơ `[Mã hồ sơ]` đã ký hoàn tất<br>**Nội dung:** Hồ sơ của dự án `[Tên dự án]` đã được ký đầy đủ. Anh/chị có thể mở hệ thống để xem và tiếp tục công việc. |
| Hồ sơ bị từ chối ký | Người có thẩm quyền từ chối ký và nhập lý do | Ban Giám đốc | KSGS và người lập đợt trình ký | **Tiêu đề:** Hồ sơ `[Mã hồ sơ]` bị từ chối ký<br>**Nội dung:** Hồ sơ chưa được chấp thuận. Lý do: `[Lý do từ chối]`. Vui lòng kiểm tra, điều chỉnh và trình lại khi cần. |
| Báo cáo thương lượng thuê đất không thành công | KSGS xác nhận không thương lượng được hợp đồng thuê đất và ghi rõ lý do | KSGS | Giám đốc Xí nghiệp | **Tiêu đề:** Báo cáo thương lượng thuê đất không thành công – `[Tên trạm]`<br>**Nội dung:** KSGS báo cáo việc thương lượng thuê đất tại trạm `[Tên trạm]` không thành công. Lý do: `[Lý do]`. Kính đề nghị Giám đốc Xí nghiệp xem xét. |
| Đề nghị xem xét hủy do thương lượng không thành công | Trường hợp thương lượng không thành công được trình lên Ban Giám đốc | Giám đốc Xí nghiệp | Ban Giám đốc | **Tiêu đề:** Đề nghị xem xét hủy trạm/dự án `[Tên dự án]`<br>**Nội dung:** Trường hợp thương lượng thuê đất không thành công đã được trình xem xét. Kính đề nghị Ban Giám đốc quyết định hủy trạm hoặc hủy dự án. |
| Thông báo quyết định hủy trạm hoặc hủy dự án | Quyết định hủy trạm hoặc hủy dự án đã được xác nhận | Giám đốc Xí nghiệp hoặc Ban Giám đốc | KSGS và những người liên quan đến dự án | **Tiêu đề:** Thông báo quyết định `[Hủy trạm/Hủy dự án]`<br>**Nội dung:** Ban Giám đốc đã quyết định `[Hủy trạm/Hủy dự án]` đối với `[Tên trạm hoặc dự án]`. Lý do: `[Lý do quyết định]`. |
| Yêu cầu phê duyệt cấp vật tư | KSGS hoàn thành yêu cầu vật tư và bấm gửi duyệt | KSGS | Trưởng phòng Kế hoạch | **Tiêu đề:** Yêu cầu phê duyệt cấp vật tư `[Mã yêu cầu]`<br>**Nội dung:** KSGS đã gửi yêu cầu vật tư cho dự án `[Tên dự án]`. Kính đề nghị Trưởng phòng kiểm tra và duyệt, tạm hoãn hoặc từ chối yêu cầu. |
| Yêu cầu vật tư đã được duyệt | Trưởng phòng Kế hoạch duyệt yêu cầu vật tư | Trưởng phòng Kế hoạch | KSGS/người tạo yêu cầu | **Tiêu đề:** Yêu cầu vật tư `[Mã yêu cầu]` đã được duyệt<br>**Nội dung:** Yêu cầu vật tư của dự án `[Tên dự án]` đã được duyệt và chuyển sang bước đặt hàng. Vật tư chưa sẵn sàng cấp phát ở thời điểm này. |
| Yêu cầu vật tư bị tạm hoãn | Trưởng phòng Kế hoạch chọn tạm hoãn và nhập lý do | Trưởng phòng Kế hoạch | KSGS/người tạo yêu cầu | **Tiêu đề:** Yêu cầu vật tư `[Mã yêu cầu]` tạm hoãn<br>**Nội dung:** Yêu cầu đang được tạm hoãn. Lý do: `[Lý do tạm hoãn]`. Vui lòng theo dõi và bổ sung thông tin khi được yêu cầu. |
| Yêu cầu vật tư bị từ chối | Trưởng phòng Kế hoạch từ chối và nhập lý do | Trưởng phòng Kế hoạch | KSGS/người tạo yêu cầu | **Tiêu đề:** Yêu cầu vật tư `[Mã yêu cầu]` bị từ chối<br>**Nội dung:** Yêu cầu chưa được chấp thuận. Lý do: `[Lý do từ chối]`. Vui lòng điều chỉnh và gửi lại nếu cần. |
| Đơn hàng đã đặt, chờ nhập kho | Đơn mua hàng của dự án được xác nhận đặt hàng | Bộ phận Kế hoạch | Thủ kho | **Tiêu đề:** Đơn hàng `[Mã PO]` đã đặt – chờ nhập kho<br>**Nội dung:** Đơn hàng phục vụ dự án `[Tên dự án]` đã được xác nhận. Thủ kho vui lòng theo dõi việc giao hàng và tạo phiếu nhập khi hàng đến. |
| Vật tư đã sẵn sàng cấp phát | Thủ kho xác nhận phiếu nhập và toàn bộ số lượng được duyệt đã về đủ | Thủ kho | KSGS/người tạo yêu cầu | **Tiêu đề:** Vật tư `[Mã yêu cầu]` đã sẵn sàng cấp phát<br>**Nội dung:** Kho đã nhận đủ vật tư cho dự án `[Tên dự án]`. Anh/chị vui lòng đến kho nhận vật tư theo yêu cầu. |
| Cấp phát vật tư hoàn tất, yêu cầu khóa PO | Thủ kho xác nhận phiếu xuất và toàn bộ vật tư đã được giao đủ | Thủ kho | Trưởng phòng Kế hoạch | **Tiêu đề:** Cấp phát hoàn tất – đề nghị khóa PO `[Mã PO]`<br>**Nội dung:** Kho đã xuất đủ vật tư của yêu cầu `[Mã yêu cầu]`. Kính đề nghị Trưởng phòng kiểm tra chứng từ và thực hiện khóa PO. |
| Dự án đã hoàn thành, chờ bàn giao | Toàn bộ công việc của dự án đã hoàn thành và dự án đủ điều kiện bàn giao | KSGS/hệ thống | Giám đốc Xí nghiệp | **Tiêu đề:** Dự án `[Tên dự án]` đã hoàn thành – chờ bàn giao<br>**Nội dung:** Các trạm thuộc dự án đã hoàn thành công việc. Kính đề nghị Giám đốc Xí nghiệp kiểm tra và thực hiện bàn giao sang bảo trì. |
| Đề nghị tiếp nhận bàn giao dự án | Giám đốc Xí nghiệp thực hiện bàn giao dự án sang bảo trì | Giám đốc Xí nghiệp | Tổ quản lý hạ tầng | **Tiêu đề:** Đề nghị tiếp nhận bàn giao dự án `[Tên dự án]`<br>**Nội dung:** Dự án đã được bàn giao sang Tổ quản lý hạ tầng. Vui lòng kiểm tra hồ sơ và xác nhận tiếp nhận trên hệ thống. |
| Xác nhận hoàn tất bàn giao | Tổ quản lý hạ tầng xác nhận đã tiếp nhận dự án | Tổ quản lý hạ tầng | Giám đốc Xí nghiệp | **Tiêu đề:** Hoàn tất bàn giao dự án `[Tên dự án]`<br>**Nội dung:** Tổ quản lý hạ tầng đã tiếp nhận dự án. Trạng thái dự án đã chuyển sang Hoàn tất bàn giao và các trạm đã chuyển sang Vận hành. |
| Nhắc lịch bảo trì sắp đến hạn | Hệ thống kiểm tra hằng ngày và phát hiện thiết bị sắp đến ngày bảo trì | Hệ thống | Kỹ thuật viên phụ trách; nếu chưa phân công thì gửi Tổ quản lý hạ tầng | **Tiêu đề:** Nhắc lịch bảo trì trạm `[Tên trạm]`<br>**Nội dung:** Trạm/thiết bị `[Tên thiết bị]` sẽ đến hạn bảo trì vào ngày `[Ngày đến hạn]`. Vui lòng sắp xếp thực hiện đúng kế hoạch. |
| Danh sách hợp đồng sắp hết hạn | Hệ thống kiểm tra hằng ngày và phát hiện hợp đồng sắp đến hạn gia hạn | Hệ thống | Tổ quản lý hạ tầng | **Tiêu đề:** Danh sách hợp đồng sắp hết hạn cần xử lý<br>**Nội dung:** Hệ thống ghi nhận `[Số lượng]` hợp đồng sắp hết hạn. Vui lòng kiểm tra danh sách và chuẩn bị hồ sơ gia hạn. |
| Yêu cầu ký hồ sơ gia hạn | Hồ sơ gia hạn đã hoàn tất và được gửi trình ký | Tổ quản lý hạ tầng | Ban Giám đốc | **Tiêu đề:** Đề nghị ký hồ sơ gia hạn `[Mã hồ sơ]`<br>**Nội dung:** Hồ sơ gia hạn hợp đồng của `[Tên trạm/dự án]` đã hoàn tất. Kính đề nghị Ban Giám đốc kiểm tra và ký xác nhận. |
| Hợp đồng gia hạn đã ký hoàn tất | Ban Giám đốc xác nhận ký xong hồ sơ gia hạn | Ban Giám đốc | Người thực hiện hồ sơ gia hạn/Tổ quản lý hạ tầng | **Tiêu đề:** Hồ sơ gia hạn `[Mã hồ sơ]` đã ký hoàn tất<br>**Nội dung:** Ban Giám đốc đã ký hồ sơ gia hạn. Vui lòng kiểm tra thời hạn mới và tiếp tục theo dõi hợp đồng. |
| Hồ sơ gia hạn bị từ chối | Ban Giám đốc từ chối ký và nhập lý do | Ban Giám đốc | Người thực hiện hồ sơ gia hạn và KSGS liên quan | **Tiêu đề:** Hồ sơ gia hạn `[Mã hồ sơ]` bị từ chối<br>**Nội dung:** Hồ sơ gia hạn chưa được chấp thuận. Lý do: `[Lý do từ chối]`. Vui lòng điều chỉnh và trình lại khi cần. |
| Báo cáo hợp đồng không thể gia hạn | Người phụ trách xác nhận hợp đồng thuê đất hoặc thuê trạm không thể gia hạn | Tổ quản lý hạ tầng | Giám đốc Xí nghiệp | **Tiêu đề:** Báo cáo hợp đồng không thể gia hạn – `[Tên trạm]`<br>**Nội dung:** Hợp đồng `[Loại hợp đồng]` không thể gia hạn. Lý do: `[Lý do]`. Kính đề nghị Giám đốc Xí nghiệp xem xét phương án xử lý. |
| Đề nghị xem xét hủy do không thể gia hạn | Trường hợp không thể gia hạn được trình lên cấp quyết định | Giám đốc Xí nghiệp | Ban Giám đốc | **Tiêu đề:** Đề nghị quyết định hủy do không thể gia hạn<br>**Nội dung:** Hồ sơ không thể gia hạn của `[Tên trạm/dự án]` đã được trình. Kính đề nghị Ban Giám đốc quyết định hủy trạm hoặc hủy dự án. |
| Thông báo quyết định sau khi không thể gia hạn | Quyết định hủy trạm hoặc hủy dự án đã được xác nhận | Giám đốc Xí nghiệp hoặc Ban Giám đốc | Người báo cáo, người phụ trách hồ sơ và các bên liên quan | **Tiêu đề:** Thông báo quyết định `[Hủy trạm/Hủy dự án]` sau gia hạn<br>**Nội dung:** Ban Giám đốc đã quyết định `[Hủy trạm/Hủy dự án]` đối với `[Tên trạm hoặc dự án]`. Lý do: `[Lý do quyết định]`. Các bên liên quan vui lòng thực hiện theo quyết định. |
