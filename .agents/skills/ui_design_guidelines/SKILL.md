---
name: ui_design_guidelines
description: Hướng dẫn thiết kế giao diện (UI/UX) với nhận diện thương hiệu của doanh nghiệp, bao gồm màu sắc, font chữ và phong cách thiết kế neo-brutalism.
---

# Brand & UI Design Guidelines

Khi thực hiện các tác vụ thiết kế giao diện (UI/UX), tạo web app, mockups, hoặc viết CSS/Tailwind trong workspace này, Agent BẮT BUỘC phải tuân thủ nghiêm ngặt cẩm nang thương hiệu (Brand Guidelines) sau:

## 1. Color Palette (Bảng màu)
Sử dụng mã màu HEX chính xác như sau:
- **Cyan Cobalt Blue:** `#3050A2` (Màu chính - Primary)
- **Mountain Meadow:** `#29B198` (Màu phụ / Nhấn - Secondary / Accent)
- **Cerise:** `#E9305C` (Màu nổi bật / Cảnh báo - Highlight / Warning)
- **White:** `#FFFFFF` (Nền sáng - Background)
- **Isabelline:** `#F8F2ED` (Nền nhạt / Bề mặt - Light Background / Surface)
- **Black:** `#192027` (Văn bản / Viền - Text / Borders)

## 2. Typography (Nghệ thuật chữ)
- **Font chữ bắt buộc:** `Inter` (Google Fonts).
- Áp dụng font Inter cho toàn bộ các thành phần văn bản trên UI (Heading, Body, Button, v.v.).
- Nhúng font: `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">` hoặc `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');`

## 3. Styling & Aesthetic (Phong cách thiết kế)
- **Đường nét:** Các thành phần giao diện (như card, button, input form, container...) BẮT BUỘC phải có **đường viền đen rõ nét (solid black borders - sử dụng màu Black `#192027` hoặc `#000000`)** và **được bo tròn (rounded corners)**.
- **Phong cách:** Hướng tới phong cách "Neo-brutalism" hoặc hiện đại, sắc nét. Các element thường có viền dày, bo góc và có thể kết hợp với solid shadows (bóng đổ dạng hình khối đặc màu đen) để tăng tính phong cách.

## 4. Implementation Rules (Quy tắc lập trình)
- Trong CSS, hãy luôn định nghĩa các root variables (CSS Custom Properties) cho các màu sắc trên trước khi áp dụng. Ví dụ:
  ```css
  :root {
    --color-primary: #3050A2;
    --color-secondary: #29B198;
    --color-accent: #E9305C;
    --color-white: #FFFFFF;
    --color-surface: #F8F2ED;
    --color-black: #192027;
  }
  ```
- Khi thiết kế, đảm bảo độ tương phản tốt giữa chữ và nền.
