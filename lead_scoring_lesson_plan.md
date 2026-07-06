# Hướng dẫn Đánh giá và Chấm điểm Giáo án (Lesson Plan Lead Scoring)

Tài liệu này cung cấp bộ tiêu chí (Prompt Guidelines) để AI tự động trích xuất dữ liệu và chấm điểm chất lượng giáo án (Lesson Plan) được sản xuất từ hệ thống. 

**Mục tiêu của AI đánh giá:** Đọc đối chiếu dữ liệu gốc từ thư mục `Nhập học liệu pdf và docs` (file Markdown trích xuất) và so sánh với kết quả giáo án đầu ra tại `Output giáo án docs`, từ đó đưa ra thang điểm đánh giá toàn diện.

---

## BỘ TIÊU CHÍ CHẤM ĐIỂM (Thang điểm 100)

### 1. Khả năng Xử lý và Quét dữ liệu đầu vào (15 điểm)
- **Tiêu chí:** AI hiểu đúng ý đồ của bài học/worksheet gốc hay không.
- **Trừ điểm:**
  - Nếu file đầu vào chất lượng thấp, định dạng sai, hoặc nội dung quá mơ hồ dẫn đến việc trích xuất Markdown bị lỗi hoặc bỏ sót thông tin quan trọng.
  - Giáo án đầu ra không phản ánh đúng chủ đề hoặc từ vựng/ngữ pháp của tài liệu gốc.

### 2. Tiêu chuẩn Montessori và Tổ chức lớp học (20 điểm)
- **Tiêu chí:** Mức độ tuân thủ các nguyên tắc Montessori (Tôn trọng sự tự do trong giới hạn, Môi trường được chuẩn bị sẵn sàng, Kiểm soát lỗi tự động).
- **Cộng/Trừ điểm:**
  - Cộng điểm nếu giáo án có ghi chú rõ ràng về cách thiết lập không gian lớp học hoặc trạm học (stations).
  - Cộng điểm nếu có hoạt động cho phép trẻ tự sửa lỗi (Self-Correction) mà không cần sự can thiệp tiêu cực của giáo viên.
  - Trừ điểm nếu sử dụng các từ ngữ mang tính ép buộc hoặc không có tính khích lệ học sinh.

### 3. Chuẩn Phương pháp giảng dạy theo Độ tuổi (15 điểm)
- **Tiêu chí:** Nội dung phải tương thích tuyệt đối với sự phát triển của trẻ Mầm non (3-4 tuổi và 5-6 tuổi).
- **Cộng/Trừ điểm:**
  - **3-4 tuổi:** Tập trung vào nhận diện từ vựng cơ bản, TPR (Phản xạ toàn thân), thời gian tập trung ngắn (nhiều hoạt động chuyển tiếp).
  - **5-6 tuổi:** Có thể bao gồm ghép vần (Phonics), làm quen cấu trúc câu đơn giản, viết/vẽ sáng tạo.
  - Trừ điểm nặng nếu phân bổ bài học quá sức (ví dụ: yêu cầu trẻ 3-4 tuổi tự viết câu hoàn chỉnh).

### 4. Tiến trình Học tập (Scaffolding & Progression) (15 điểm)
- **Tiêu chí:** Cấu trúc bài giảng phải có sự tịnh tiến logic về độ khó.
- **Cộng/Trừ điểm:**
  - Bài học phải tuân thủ lộ trình: Dễ (Nhận biết) -> Trung bình (Hiểu/Vận dụng) -> Khó (Sáng tạo) dựa trên thang đo Bloom và mức độ phức tạp ngôn ngữ.
  - Các hoạt động thực tế (guided practice) phải bám sát và phục vụ trực tiếp cho Mục tiêu bài học (Objectives). Trừ điểm nếu hoạt động bị lạc đề.

### 5. Độ An toàn Lớp học (Safety Factor) (10 điểm)
- **Tiêu chí:** Đảm bảo rủi ro vật lý ở mức thấp nhất trong các hoạt động.
- **Cộng/Trừ điểm:**
  - **Cảnh báo Đỏ (Trừ điểm nặng):** Giáo án yêu cầu sử dụng các vật dụng nguy hiểm như lửa, vật sắc nhọn không có kiểm soát, hoặc các vật nhỏ dễ gây hóc sặc mà không có phần cảnh báo "Safety Note".
  - **Bắt buộc:** Các hoạt động thủ công cắt dán BẮT BUỘC phải ghi chú: *"Sử dụng kéo an toàn dành cho trẻ em dưới sự giám sát sát sao từ trợ giảng (TA)"*. Nếu thiếu câu này -> Trừ điểm.

### 6. Tính Tò mò, Hứng thú và Đa giác quan (15 điểm)
- **Tiêu chí:** Đảm bảo lớp học không nhàm chán và kích thích được mọi giác quan của trẻ.
- **Cộng/Trừ điểm:**
  - Bài học có xen kẽ nhịp nhàng giữa hoạt động tĩnh (Worksheet, tô màu) và hoạt động động (Nhảy múa, TPR, Games).
  - Có các hoạt động liên quan đến âm nhạc (Songs) và nghệ thuật (Crafts, cắt dán sáng tạo).

### 7. Định dạng và Đặt tên file (10 điểm)
- **Tiêu chí:** Tính chuẩn hóa của hệ thống.
- **Cộng/Trừ điểm:**
  - File đầu ra phải có định dạng rõ ràng (đã chuyển đổi MD/DOCX).
  - Tên Topic / Tên file phải được đặt đúng cú pháp quy định: `[TÊN CHỦ ĐỀ] - Lesson [SỐ THỨ TỰ TRONG MÔN].docx` (Ví dụ: `My birthday Party - Lesson 1.docx`).
  - Tiêu đề chính phải được căn giữa, cấu trúc 4 Parts (Warm-up, New Words, Guided Practice, Review & Closing) phải đầy đủ bằng tiếng Anh.

---

## QUY TRÌNH THỰC THI (Execution Prompt cho AI Scorer)

1. **Đọc Context:** AI sẽ đọc các file dữ liệu đầu vào (tài liệu thô hoặc markdown) từ thư mục `Nhập học liệu pdf và docs`.
2. **Đọc Output:** AI quét file giáo án tương ứng từ thư mục `Output giáo án docs`.
3. **Phân tích đối chiếu:** Chạy 7 tiêu chí trên để đối chiếu.
4. **Xuất Báo Cáo:** AI sẽ sinh ra một bản Report ngắn gọn dạng Markdown bao gồm:
   - **Tổng điểm:** `[X]/100`
   - **Nhận xét điểm mạnh (Strengths):** Các yếu tố tốt nhất của giáo án.
   - **Các lỗi/Rủi ro cần khắc phục (Red Flags/Weaknesses):** Cụ thể nếu vi phạm tính an toàn hoặc lệch độ tuổi.
   - **Đề xuất sửa đổi (Recommendations):** Lời khuyên để tối ưu lại giáo án.
