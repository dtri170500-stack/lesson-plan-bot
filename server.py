import http.server
import json
import os

PORT = 9009

CRITERIA_DATA = [
    {
        "id": 1,
        "title": "1. Khả năng xử lý và quét dữ liệu đầu vào",
        "max_score": "15đ",
        "items": [
            {"score": "15đ", "type": "high", "desc": "Tuyệt đối: Trích xuất và hiểu chính xác 100% ý đồ bài học, từ vựng và mục tiêu của worksheet gốc. Giáo án bám sát hoàn toàn tài liệu thô."},
            {"score": "10đ", "type": "mid", "desc": "Tốt: Hiểu đúng chủ đề chính, nhưng bỏ sót 1-2 từ vựng phụ hoặc bối cảnh nhỏ trong file gốc."},
            {"score": "5đ", "type": "low", "desc": "Kém: Trích xuất thiếu dữ liệu nghiêm trọng, giáo án sinh ra bị thiếu liên kết với tài liệu gốc do lỗi đọc file."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Không nhận diện được dữ liệu đầu vào hoặc bịa đặt (hallucinate) hoàn toàn nội dung không hề có."}
        ]
    },
    {
        "id": 2,
        "title": "2. Tiêu chuẩn Montessori và Tổ chức lớp học",
        "max_score": "20đ",
        "items": [
            {"score": "20đ", "type": "high", "desc": "Xuất sắc: Tích hợp đầy đủ 'Prepared environment' và 'Control of Error'. Sử dụng 100% ngôn ngữ tích cực."},
            {"score": "15đ", "type": "mid", "desc": "Tốt: Môi trường thân thiện, tự do trong giới hạn nhưng thiếu tính năng tự sửa lỗi cho học sinh."},
            {"score": "10đ", "type": "low", "desc": "Trung bình: Dạy theo kiểu truyền thống (thầy nói - trò nghe), thiếu vắng các yếu tố trạm học, lời lẽ vẫn tích cực."},
            {"score": "5đ", "type": "low", "desc": "Kém: Không có phương pháp rõ ràng, xuất hiện 1-2 câu mệnh lệnh khô khan."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Đi ngược triết lý Montessori (ép buộc, dọa nạt, tạo áp lực nói hoàn hảo cho trẻ)."}
        ]
    },
    {
        "id": 3,
        "title": "3. Chuẩn phương pháp giảng dạy theo độ tuổi",
        "max_score": "15đ",
        "items": [
            {"score": "15đ", "type": "high", "desc": "Hoàn hảo: Bài giảng tương thích 100% độ tuổi (TPR cho 3-4T, phonics/tư duy cho 5-6T)."},
            {"score": "10đ", "type": "mid", "desc": "Khá: Phù hợp độ tuổi nhưng thời lượng hoạt động tĩnh kéo quá dài."},
            {"score": "5đ", "type": "low", "desc": "Kém: Phân bổ bài học quá sức hoặc quá dễ."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Hoàn toàn sai lệch độ tuổi và khả năng nhận thức của trẻ."}
        ]
    },
    {
        "id": 4,
        "title": "4. Tiến trình học tập (Scaffolding)",
        "max_score": "15đ",
        "items": [
            {"score": "15đ", "type": "high", "desc": "Xuất sắc: Tịnh tiến độ khó logic theo thang Bloom: Dễ -> Trung bình -> Khó."},
            {"score": "10đ", "type": "mid", "desc": "Khá: Có thứ tự dễ đến khó nhưng hoạt động kém phong phú."},
            {"score": "5đ", "type": "low", "desc": "Kém: Tiến trình lộn xộn, thiếu bước đệm (scaffolding), nhảy cóc độ khó."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Hoạt động lạc đề hoàn toàn so với Objectives của buổi học."}
        ]
    },
    {
        "id": 5,
        "title": "5. Độ an toàn lớp học (Safety Factor)",
        "max_score": "10đ",
        "items": [
            {"score": "10đ", "type": "high", "desc": "Tuyệt đối: Hoạt động an toàn 100%. Luôn ghi chú giám sát an toàn rõ ràng."},
            {"score": "5đ", "type": "low", "desc": "Khá: Không có hoạt động nguy hiểm trực tiếp, nhưng thiếu cảnh báo dọn dẹp trước Game vận động mạnh."},
            {"score": "0đ", "type": "fail", "desc": "Cảnh báo đỏ: Sử dụng vật nguy hiểm (nhọn, sinh nhiệt, nhỏ dễ hóc) MÀ KHÔNG CÓ 'Safety Note'."}
        ]
    },
    {
        "id": 6,
        "title": "6. Tính tò mò, hứng thú & Đa giác quan",
        "max_score": "15đ",
        "items": [
            {"score": "15đ", "type": "high", "desc": "Xuất sắc: Phối hợp hoàn hảo nghe nhạc, vận động, nhìn trực quan và thủ công."},
            {"score": "10đ", "type": "mid", "desc": "Khá: Bài học vui nhộn nhưng chỉ tập trung vào 1-2 giác quan."},
            {"score": "5đ", "type": "low", "desc": "Kém: Nhàm chán, thiếu vắng âm nhạc và trò chơi, ngồi ghế quá lâu."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Chỉ thuần túy chép bài, làm worksheet lặp lại."}
        ]
    },
    {
        "id": 7,
        "title": "7. Định dạng và Đặt tên file",
        "max_score": "10đ",
        "items": [
            {"score": "10đ", "type": "high", "desc": "Hoàn hảo: Đúng tên file chuẩn `[CHỦ ĐỀ] - Lesson [SỐ].docx`. Tiêu đề căn giữa, đủ 4 Parts rõ ràng bằng tiếng Anh."},
            {"score": "7đ", "type": "mid", "desc": "Khá: Đủ 4 Parts nhưng tên file sai quy ước hoa/thường, chưa căn giữa tiêu đề."},
            {"score": "3đ", "type": "low", "desc": "Kém: Thiếu 1 trong 4 Part bắt buộc."},
            {"score": "0đ", "type": "fail", "desc": "Không đạt: Lỗi định dạng, trộn lẫn tiếng Việt và tiếng Anh."}
        ]
    }
]

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/criteria':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(CRITERIA_DATA, ensure_ascii=False).encode('utf-8'))
        elif self.path == '/api/results':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            report_path = os.path.join(os.path.dirname(__file__), '.agents', 'reporting', 'grading_report.json')
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.wfile.write(data.encode('utf-8'))
            else:
                self.wfile.write(json.dumps([]).encode('utf-8'))
        elif self.path == '/' or self.path == '/index.html':
            self.path = '/grading_sheet_ui_test.html'
            super().do_GET()
        else:
            super().do_GET()

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), MyHandler)
    print(f"Server starting on http://localhost:{PORT}")
    server.serve_forever()
