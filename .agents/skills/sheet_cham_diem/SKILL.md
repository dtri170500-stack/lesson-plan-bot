---
name: "sheet_cham_diem"
description: "Chuyên gia cấu trúc báo cáo Google Sheet. Định nghĩa chuẩn layout (cột, hàng) và Conditional Formatting để trình bày báo cáo đánh giá giáo án một cách khoa học."
---
# HƯỚNG DẪN CẤU TRÚC GOOGLE SHEET BÁO CÁO CHẤM ĐIỂM LESSON PLAN

Khi tạo, cập nhật hoặc thiết kế bảng tính (Google Sheet) dùng để theo dõi điểm số chất lượng của giáo án do AI tạo ra, Agent phải tuân thủ nghiêm ngặt cấu trúc dữ liệu sau để đảm bảo tính khoa học, dễ nhìn và thuận tiện cho Quản lý Học thuật (Academic Manager) kiểm tra.

## 1. CẤU TRÚC HÀNG (ROWS)

- **Hàng 1 (Super Header):** Dành cho tiêu đề bảng và thông tin tổng quan. (Ví dụ gộp ô A1:S1 ghi: `HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG GIÁO ÁN TỰ ĐỘNG BẰNG AI`).
- **Hàng 2 (Header Row):** Tên của các trường dữ liệu (Cột). Bắt buộc phải được **In đậm**, **Cố định (Freeze Row 2)** và bật bộ lọc **(Filter)**.
- **Hàng 3 trở đi (Data Rows):** Các dòng dữ liệu báo cáo được tự động thêm vào (Append) mỗi khi chạy xong Pipeline.

## 2. CẤU TRÚC CỘT BẮT BUỘC (COLUMNS)

Bảng tính phải bao gồm các cột sau (xếp theo thứ tự từ trái qua phải):

### A. Nhóm Thông tin Định danh (Meta Data)

- **Cột A - Timestamp:** Thời gian AI hoàn tất việc tạo và chấm điểm (Ví dụ: `2026-07-06 19:30:00`).
- **Cột B - Week / Topic:** Tuần học hoặc Chủ đề của giáo án (Ví dụ: `Week 2 - My Birthday Party`).
- **Cột C - File Name:** Tên file giáo án (Ví dụ: `My Birthday Party.md`).
- **Cột D - Age Group:** Độ tuổi mục tiêu (Ví dụ: `3-4`).

### B. Nhóm Đánh giá Tổng quan (Overview)

- **Cột E - Status:** Trạng thái vượt qua (Chỉ nhận 2 giá trị: `PASS` hoặc `FAIL`).
- **Cột F - Total Score:** Tổng điểm đạt được (Trên thang điểm 100).

### C. Nhóm Điểm Thành Phần (Sub-scores)

Dựa theo bộ tiêu chí sư phạm cốt lõi:

- **Cột G - Data Extraction (15):** Điểm khả năng bám sát học liệu gốc.
- **Cột H - Montessori Standards (20):** Điểm quản lý lớp học, tự sửa lỗi (Control of Error).
- **Cột I - Age Appropriateness (15):** Điểm chuẩn phương pháp theo độ tuổi (TPR, thời lượng).
- **Cột J - Scaffolding (15):** Điểm tiến trình tịnh tiến (Bloom's Taxonomy).
- **Cột K - Safety (10):** Điểm cảnh báo an toàn lớp học.
- **Cột L - Engagement (15):** Điểm hoạt động đa giác quan, trò chơi.
- **Cột M - Formatting (10):** Điểm cấu trúc văn bản 4 Parts, tiếng Anh chuẩn.

### D. Nhóm Cảnh Báo & Xử Lý (Actionable Insights)

- **Cột N - Failed Items:** Liệt kê tên các tiêu chí bị điểm kém (Vi phạm nghiêm trọng).
- **Cột O - AI Suggestions:** Lời khuyên chi tiết từ AI để sửa đổi giáo án (Làm gì để khắc phục).

### E. Nhóm Liên Kết & Quản Trị (Links & Management)

- **Cột P - Docx Link:** Link Google Drive bản Word (.docx) để giáo viên tải về.
- **Cột Q - PDF Link:** Link Google Drive bản PDF (Tùy chọn).
- **Cột R - Reviewer:** Tên người kiểm duyệt (Để trống để Quản lý ký tên/chọn Dropdown).
- **Cột S - Manager Notes:** Ghi chú thủ công của Quản lý Học thuật sau khi đọc.

## 3. ĐỊNH DẠNG TỰ ĐỘNG (CONDITIONAL FORMATTING)

Để báo cáo trực quan, hãy luôn thiết lập (hoặc viết script Google Apps Script để thiết lập) các quy tắc định dạng có điều kiện sau:

1. **Status (Cột E):**
   - Nếu Text = `PASS` ➡️ Tô nền Xanh lá mạt nhạt (Light Green), chữ Xanh lục đậm.
   - Nếu Text = `FAIL` ➡️ Tô nền Đỏ nhạt (Light Red), chữ Đỏ sậm (Dark Red) + In đậm.
2. **Total Score (Cột F):**
   - Sử dụng Dải màu (Color Scale): `< 50` (Đỏ) ➡️ `50-79` (Vàng) ➡️ `>= 80` (Xanh lá).
3. **Các cột điểm thành phần (Cột G đến M):**
   - Bất kỳ ô nào có điểm nhỏ hơn 50% số điểm tối đa của tiêu chí đó ➡️ Tô nền Cam nhạt để làm nổi bật lỗ hổng của bài giảng.
4. **Wrap Text:** Cột N (Failed Items) và Cột O (AI Suggestions) phải luôn được bật chế độ **Text Wrapping (Xuống dòng tự động)** để không bị tràn chữ che khuất ô khác.

## 4. QUY TRÌNH TRIGGER

Agent phụ trách xuất báo cáo điểm phải tự động format file CSV hoặc G-Sheet API theo đúng cấu trúc này trước khi gửi cho người dùng. Mọi file xuất ra bị thiếu các cột ở mục A, B, C đều bị coi là vi phạm nguyên tắc "Explicit" trong khung CLEAR.
